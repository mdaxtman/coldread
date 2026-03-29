"""Fit assessment — Strong / Moderate / Borderline / Poor with gap detection.

Calls the Anthropic API with the screener prompt and candidate narratives,
using tool use to guarantee structured JSON output.
"""

from typing import Any, cast

import anthropic

from config import get_anthropic_api_key
from db import fit_reports, job_descriptions, narratives
from pipeline.prompt_loader import load_prompt
from security.injection_detection import analyze_jd_for_injection

_client: anthropic.Anthropic | None = None


def _get_anthropic_client() -> anthropic.Anthropic:
    global _client  # noqa: PLW0603
    if _client is None:
        _client = anthropic.Anthropic(api_key=get_anthropic_api_key())
    return _client


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
                "required": ["my_term", "jd_term"],
                "properties": {
                    "my_term": {"type": "string"},
                    "jd_term": {"type": "string"},
                },
            },
        },
        "reasoning": {"type": "string"},
    },
}


def _format_narratives(narrative_rows: list[dict[str, Any]]) -> str:
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


def run_fit_assessment(jd_id: str, user_id: str) -> dict[str, Any]:
    jd = job_descriptions.get_jd(jd_id, user_id)
    if jd is None:
        raise ValueError(f"Job description not found: {jd_id}")

    # Analyze for suspicious patterns (non-blocking, for monitoring)
    analyze_jd_for_injection(jd["content"], user_id)

    narrative_rows = narratives.list_narratives(user_id)
    narratives_text = _format_narratives(narrative_rows)
    system_prompt = load_prompt("screener", user_id)

    user_message = (
        f"<job_description>\n{jd['content']}\n</job_description>\n\n"
        f"<candidate_background>\n{narratives_text}\n</candidate_background>\n\n"
        "Evaluate the candidate's background against this job description "
        "and submit your assessment using the submit_fit_report tool."
    )

    response = _get_anthropic_client().messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        tools=[
            {
                "name": "submit_fit_report",
                "description": "Submit the structured fit assessment result",
                "input_schema": _FIT_REPORT_SCHEMA,
            }
        ],
        tool_choice={"type": "tool", "name": "submit_fit_report"},
    )

    try:
        tool_block = next(b for b in response.content if b.type == "tool_use")
    except StopIteration:
        content_types = [b.type for b in response.content]
        raise RuntimeError(
            f"Anthropic response contained no tool_use block. Content types: {content_types}"
        )
    result = cast(dict[str, Any], tool_block.input)

    return fit_reports.create_fit_report(
        job_description_id=jd_id,
        user_id=user_id,
        fit_level=result["fit_level"],
        matches=result["matches"],
        gaps=result["gaps"],
        terminology=result["terminology"],
        reasoning=result["reasoning"],
    )
