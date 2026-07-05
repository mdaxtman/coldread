"""Refinement stage — independent module for improving resume while preserving voice.

Extracts refinement as a reusable pipeline stage that accepts RefinementInput
and returns RefinementOutput with a refined resume and list of changes made.
"""

from typing import Any, cast

from config import PIPELINE_MODEL
from pipeline.anthropic_utils import call_model
from pipeline.prompt_loader import load_prompt
from pipeline.stage_input import RefinementInput, RefinementOutput

_TOOL_NAME = "submit_refined_resume"

_REFINEMENT_SCHEMA = {
    "type": "object",
    "required": ["refined_content", "changes"],
    "properties": {
        "refined_content": {
            "type": "string",
            "description": "The refined resume content in markdown format",
        },
        "changes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of changes made to the resume",
        },
    },
}


def _format_gaps_summary(gaps: list[dict[str, Any]]) -> str:
    """Format fit assessment gaps into readable text for refinement prompt.

    Converts the gaps list from fit assessment into clear guidance showing
    what requirements are missing or weak so the refinement stage can
    strategically address them where possible.

    Args:
        gaps: List of gap dicts with 'requirement', 'type', and 'notes'

    Returns:
        Formatted text describing the gaps, or empty string if no gaps
    """
    if not gaps:
        return ""

    lines = ["COVERAGE GAPS (requirements not met by candidate):"]
    for gap in gaps:
        requirement = gap.get("requirement", "")
        gap_type = gap.get("type", "unknown")
        notes = gap.get("notes", "")

        if requirement:
            gap_line = f"- {requirement} ({gap_type})"
            if notes:
                gap_line += f": {notes}"
            lines.append(gap_line)

    return "\n".join(lines)


def run_refinement_stage(input_data: RefinementInput) -> RefinementOutput:
    """Run the refinement stage (editor perspective).

    Refines the generated resume to better address fit gaps and improve
    alignment with the job description while preserving the candidate's voice.

    Args:
        input_data: RefinementInput containing resume_content, fit_assessment_output,
            jd_content, and user_id

    Returns:
        RefinementOutput with refined_content and changes_made

    Raises:
        RuntimeError: If API call fails or no tool response found
        ValueError: If no active prompt found for refinement stage
    """
    # Load system prompt from database
    system_prompt = load_prompt("refinement", input_data.user_id)

    # Format gaps summary for inclusion in prompt
    gaps_summary = _format_gaps_summary(input_data.fit_assessment_output.gaps)

    # Build user message with resume, JD, and gaps context
    user_message = (
        f"<job_description>\n{input_data.jd_content}\n</job_description>\n\n"
        f"<generated_resume>\n{input_data.resume_content}\n</generated_resume>\n\n"
    )

    if gaps_summary:
        user_message += f"<coverage_gaps>\n{gaps_summary}\n</coverage_gaps>\n\n"

    user_message += (
        "Refine the resume's language and terminology to improve alignment with the job "
        "description. Do not add experience, capabilities, or claims not already present "
        "in the resume draft. Preserve the candidate's authentic voice and experience. "
        "Use the submit_refined_resume tool to submit your refined resume and the "
        "list of changes you made."
    )

    # Call Anthropic Claude with tool use
    # cast needed: Anthropic SDK requires Any type for tools parameter despite static type hints
    result = call_model(
        "refine",
        model=PIPELINE_MODEL,
        # 8192: refined full-resume output; 4096 truncated under the
        # claude-sonnet-5 tokenizer (observed stop_reason=max_tokens)
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        tools=cast(
            Any,
            [
                {
                    "name": _TOOL_NAME,
                    "description": "Submit the refined resume and list of changes",
                    "input_schema": _REFINEMENT_SCHEMA,
                }
            ],
        ),
        tool_choice={"type": "tool", "name": _TOOL_NAME},
    )

    # claude-sonnet-5 occasionally drifts the key name despite the schema
    # (tool schemas are not strictly enforced without strict mode, which
    # our min/max constraints preclude for now). Normalize before use.
    if "refined_content" not in result and "refined_resume" in result:
        result["refined_content"] = result.pop("refined_resume")
    if "refined_content" not in result:
        raise RuntimeError(
            f"refinement returned no refined_content (keys: {sorted(result.keys())})"
        )

    # Ensure changes_made is a list
    changes_made = result.get("changes", [])
    if not isinstance(changes_made, list):
        changes_made = []

    # Return structured output
    return RefinementOutput(
        refined_content=result.get("refined_content", ""),
        changes_made=changes_made,
    )
