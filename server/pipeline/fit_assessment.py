"""Fit assessment stage — evaluate candidate fit against job description."""

from typing import Any, cast

from pipeline.anthropic_utils import _extract_tool_response, _get_anthropic_client
from pipeline.prompt_loader import load_prompt

_TOOL_NAME = "submit_fit_report"

_FIT_REPORT_SCHEMA: dict[str, object] = {
    "type": "object",
    "required": ["fit_level", "matches", "gaps", "terminology", "reasoning"],
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
        "reasoning": {"type": "string"},
    },
}


def run_fit_assessment(jd_content: str, narratives_text: str, user_id: str) -> dict[str, Any]:
    """Evaluate candidate fit against job description.

    Args:
        jd_content: Raw job description text
        narratives_text: Formatted candidate narratives
        user_id: Current user ID

    Returns:
        Fit assessment: {fit_level, matches, gaps, terminology, reasoning}

    Raises:
        RuntimeError: If API call fails or no tool response found
    """
    system_prompt = load_prompt("screener", user_id)
    user_message = (
        f"<job_description>\n{jd_content}\n</job_description>\n\n"
        f"<candidate_background>\n{narratives_text}\n</candidate_background>\n\n"
        "Evaluate the candidate's background against this job description "
        "and submit your assessment using the submit_fit_report tool."
    )

    response = _get_anthropic_client().messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        tools=cast(
            Any,
            [
                {
                    "name": _TOOL_NAME,
                    "description": "Submit the structured fit assessment result",
                    "input_schema": _FIT_REPORT_SCHEMA,
                }
            ],
        ),
        tool_choice={"type": "tool", "name": _TOOL_NAME},
    )

    result = _extract_tool_response(response)

    # Filter terminology mappings: only keep those with confidence >= 0.8
    if "terminology" in result:
        result["terminology"] = [
            term for term in result["terminology"] if term.get("confidence", 0) >= 0.8
        ]

    return result
