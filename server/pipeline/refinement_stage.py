"""Refinement stage — independent module for improving resume while preserving voice.

Extracts refinement as a reusable pipeline stage that accepts RefinementInput
and returns RefinementOutput with a refined resume and list of changes made.
"""

from typing import Any, cast

from pipeline.anthropic_utils import _extract_tool_response, _get_anthropic_client
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
        "Refine the resume to improve alignment with the job description and "
        "strategically address coverage gaps where possible. "
        "Preserve the candidate's authentic voice and experience. "
        "Use the submit_refined_resume tool to submit your refined resume and the "
        "list of changes you made."
    )

    # Call Anthropic Claude with tool use
    # cast needed: Anthropic SDK requires Any type for tools parameter despite static type hints
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
                    "description": "Submit the refined resume and list of changes",
                    "input_schema": _REFINEMENT_SCHEMA,
                }
            ],
        ),
        tool_choice={"type": "tool", "name": _TOOL_NAME},
    )

    # Extract tool response (refined resume and changes)
    result = _extract_tool_response(response)

    # Ensure changes_made is a list
    changes_made = result.get("changes", [])
    if not isinstance(changes_made, list):
        changes_made = []

    # Return structured output
    return RefinementOutput(
        refined_content=result.get("refined_content", ""),
        changes_made=changes_made,
    )
