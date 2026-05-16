"""Fit assessment stage — independent module for JD-to-narratives analysis.

Extracts fit assessment as a reusable pipeline stage that accepts
FitAssessmentInput and returns FitAssessmentOutput with structured
fit analysis from the ATS screener perspective.
"""

from typing import Any

from pipeline.anthropic_utils import _extract_tool_response, _get_anthropic_client
from pipeline.prompt_loader import load_prompt
from pipeline.stage_input import FitAssessmentInput, FitAssessmentOutput

_TOOL_NAME = "submit_fit_report"
_TERMINOLOGY_CONFIDENCE_THRESHOLD = 0.8  # Filter terminology to high-confidence matches

_FIT_REPORT_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["fit_level", "matches", "gaps", "terminology"],
    "properties": {
        "fit_level": {
            "type": "string",
            "enum": ["strong", "moderate", "borderline", "poor"],
        },
        "matches": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["requirement", "priority", "notes"],
                "properties": {
                    "requirement": {"type": "string"},
                    "priority": {
                        "type": "string",
                        "enum": ["required", "preferred", "implied"],
                    },
                    "notes": {"type": "string"},
                },
            },
        },
        "gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["requirement", "type", "notes"],
                "properties": {
                    "requirement": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["hard", "soft"],
                    },
                    "notes": {"type": "string"},
                },
            },
        },
        "terminology": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["my_term", "jd_term", "confidence"],
                "properties": {
                    "my_term": {"type": "string"},
                    "jd_term": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
        "semantic_score": {"type": "number", "minimum": 0, "maximum": 1},
        "overall_score": {"type": "number", "minimum": 0, "maximum": 1},
    },
}


def _score_to_level(score: float) -> str:
    """Convert numeric score to fit level classification.

    Args:
        score: Numeric score from 0.0 to 1.0

    Returns:
        Fit level: "strong", "moderate", "borderline", or "poor"
    """
    if score >= 0.8:
        return "strong"
    elif score >= 0.6:
        return "moderate"
    elif score >= 0.4:
        return "borderline"
    else:
        return "poor"


def _extract_keywords(matches: list[dict[str, Any]], gaps: list[dict[str, Any]]) -> dict[str, bool]:
    """Extract keywords from matches and gaps to build coverage map.

    Args:
        matches: List of matched requirements
        gaps: List of unmet requirements

    Returns:
        Dictionary mapping keywords (lowercase) to coverage status (True/False)
    """
    coverage = {}

    # Add matched keywords as covered
    for match in matches:
        requirement = match.get("requirement", "").lower()
        if requirement:
            coverage[requirement] = True

    # Add gap keywords as not covered
    for gap in gaps:
        requirement = gap.get("requirement", "").lower()
        if requirement:
            coverage[requirement] = False

    return coverage


def run_fit_assessment_stage(input_data: FitAssessmentInput) -> FitAssessmentOutput:
    """Run the fit assessment stage (ATS screener perspective).

    Analyzes candidate narratives against job description to determine fit level,
    identify matched requirements, unmet gaps, and terminology alignments.

    Args:
        input_data: FitAssessmentInput containing JD, narratives, and user_id

    Returns:
        FitAssessmentOutput with structured fit analysis

    Raises:
        RuntimeError: If API call fails or no tool response found
        ValueError: If no active prompt found for screener stage
    """
    # Load system prompt from database
    system_prompt = load_prompt("screener", input_data.user_id)

    # Format user message with JD and narratives
    user_message = (
        f"<job_description>\n{input_data.jd_content}\n</job_description>\n\n"
        f"<candidate_background>\n{input_data.narratives_text}\n</candidate_background>\n\n"
        "Evaluate the candidate's background against this job description "
        "and submit your assessment using the submit_fit_report tool."
    )

    # Call Anthropic Claude with tool use
    response = _get_anthropic_client().messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        tools=[
            {
                "name": _TOOL_NAME,
                "description": "Submit the structured fit assessment result",
                "input_schema": _FIT_REPORT_SCHEMA,
            }
        ],
        tool_choice={"type": "tool", "name": _TOOL_NAME},
    )

    # Extract tool response
    result = _extract_tool_response(response)

    # Filter terminology: only keep high-confidence mappings
    terminology = result.get("terminology", [])
    if terminology:
        result["terminology"] = [
            term
            for term in terminology
            if term.get("confidence", 0) >= _TERMINOLOGY_CONFIDENCE_THRESHOLD
        ]

    # Extract scores (API should return these)
    overall_score = result.get("overall_score", 0.5)
    semantic_score = result.get("semantic_score", 0.5)

    # Build keyword coverage map from matches and gaps
    matches = result.get("matches", [])
    gaps = result.get("gaps", [])
    keyword_coverage = _extract_keywords(matches, gaps)

    # Determine fit level based on overall score
    fit_level = _score_to_level(overall_score)

    # Construct and return FitAssessmentOutput
    return FitAssessmentOutput(
        fit_level=fit_level,
        matches=matches,
        gaps=gaps,
        terminology=result.get("terminology", []),
        overall_score=overall_score,
        semantic_score=semantic_score,
        keyword_coverage=keyword_coverage,
    )
