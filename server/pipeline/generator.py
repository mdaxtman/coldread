"""Generator stage — produce tailored resume draft guided by fit assessment."""

from typing import Any, cast

from pipeline.anthropic_utils import _extract_tool_response, _get_anthropic_client
from pipeline.prompt_loader import load_prompt

# Tool schema for Claude tool_use
_TOOL_NAME = "submit_resume_draft"

_GENERATOR_SCHEMA = {
    "type": "object",
    "required": ["experience", "skills"],
    "properties": {
        "summary": {"type": "string"},
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["company", "title", "dates", "projects"],
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "dates": {"type": "string"},
                    "projects": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "bullets"],
                            "properties": {
                                "name": {"type": "string"},
                                "dates": {"type": "string"},
                                "bullets": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                    },
                },
            },
        },
        "skills": {"type": "array", "items": {"type": "string"}},
    },
}


def _format_note(notes: str | None) -> str:
    """Format optional notes as suffix string."""
    return f" ({notes})" if notes else ""


def _format_narratives(narrative_rows: list[dict[str, Any]]) -> str:
    """Format narratives into Markdown sections."""
    if not narrative_rows:
        return "No candidate background narratives available."

    overview = [n for n in narrative_rows if n.get("category") == "career_overview"]
    roles = [n for n in narrative_rows if n.get("category") != "career_overview"]

    sections: list[str] = []
    if overview:
        sections.append(
            "## Career Overview\n"
            + "\n\n".join(f"### {n['title']}\n{n['content']}" for n in overview)
        )
    if roles:
        sections.append(
            "## Role Narratives\n" + "\n\n".join(f"### {n['title']}\n{n['content']}" for n in roles)
        )

    return "\n\n".join(sections)


def _format_fit_report(fit_report: dict[str, Any]) -> str:
    """Format fit report into structured guidance for the generator.

    Converts the pre-computed fit assessment into readable sections showing:
    - What requirements are clearly matched
    - What gaps exist and how to handle them
    - Which terminology should be used
    """
    lines = []

    # MATCHES section
    matches = fit_report.get("matches", [])
    if matches:
        lines.append("MATCHES — requirements you clearly meet (emphasize these):")
        for match in matches:
            priority = match.get("priority", "required").upper()
            req = match.get("requirement", "")
            notes = match.get("notes", "")
            notes_str = _format_note(notes)
            lines.append(f"  - [{priority}] {req}{notes_str}")

    # GAPS section (separated by type)
    gaps = fit_report.get("gaps", [])
    soft_gaps = [g for g in gaps if g.get("type") == "soft"]
    hard_gaps = [g for g in gaps if g.get("type") == "hard"]

    if soft_gaps:
        lines.append("\nGAPS — soft (position adjacent strengths if relevant):")
        for gap in soft_gaps:
            req = gap.get("requirement", "")
            notes = gap.get("notes", "")
            notes_str = _format_note(notes)
            lines.append(f"  - [SOFT] {req}{notes_str}")

    if hard_gaps:
        lines.append("\nGAPS — hard (leave as gap, do not bridge):")
        for gap in hard_gaps:
            req = gap.get("requirement", "")
            notes = gap.get("notes", "")
            notes_str = _format_note(notes)
            lines.append(f"  - [HARD] {req}{notes_str}")

    # TERMINOLOGY section
    terminology = fit_report.get("terminology", [])
    if terminology:
        lines.append("\nTERMINOLOGY — use JD's exact terms where experience matches:")
        for term in terminology:
            my_term = term.get("my_term", "")
            jd_term = term.get("jd_term", "")
            lines.append(f"  - {my_term} → {jd_term}")

    return "\n".join(lines)


def run_generator(narratives_text: str, fit_report: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Step 1: Generator perspective — create strategic resume guided by fit assessment.

    Receives pre-computed fit report (matches/gaps/terminology) to inform strategic choices:
    - Emphasize matched requirements
    - Handle soft gaps by positioning adjacent strengths
    - Omit hard gaps entirely
    - Use exact terminology from the JD where applicable

    Args:
        narratives_text: Formatted candidate narratives
        fit_report: Pre-computed fit assessment
        user_id: Current user ID

    Returns:
        Structured resume data: {summary, experience, skills, ...}

    Raises:
        RuntimeError: If API call fails or no tool response found
    """
    system_prompt = load_prompt("generator", user_id)
    fit_guidance = _format_fit_report(fit_report)
    user_message = (
        f"<candidate_background>\n{narratives_text}\n</candidate_background>\n\n"
        f"<fit_assessment>\n{fit_guidance}\n</fit_assessment>\n\n"
        "Create a focused, strategic resume that highlights strengths matching the role. "
        "Use the fit assessment above to guide emphasis, handle gaps appropriately, and use the "
        "exact terminology from the JD. "
        "Use the submit_resume_draft tool to submit your output."
    )

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
                    "description": "Submit the generated resume draft",
                    "input_schema": _GENERATOR_SCHEMA,
                }
            ],
        ),
        tool_choice={"type": "tool", "name": _TOOL_NAME},
    )

    return _extract_tool_response(response)
