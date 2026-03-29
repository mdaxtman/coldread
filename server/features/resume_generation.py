"""Resume generation — three-step pipeline (generator → screener → refinement).

Orchestrates three sequential Claude API calls, each with tool use for structured output.
"""

from typing import Any, cast

import anthropic

from config import get_anthropic_api_key
from db import job_descriptions, narratives, resume_variants
from pipeline.prompt_loader import load_prompt

_client: anthropic.Anthropic | None = None


def _get_anthropic_client() -> anthropic.Anthropic:
    global _client  # noqa: PLW0603
    if _client is None:
        _client = anthropic.Anthropic(api_key=get_anthropic_api_key())
    return _client


# Tool schemas for Claude tool_use
_GENERATOR_SCHEMA = {
    "type": "object",
    "required": ["experience", "skills"],
    "properties": {
        "summary": {"type": "string"},
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["company", "title", "dates", "bullets"],
                "properties": {
                    "company": {"type": "string"},
                    "title": {"type": "string"},
                    "dates": {"type": "string"},
                    "bullets": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "skills": {"type": "array", "items": {"type": "string"}},
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
    },
}

_SCREENER_SCHEMA = {
    "type": "object",
    "required": ["keyword_coverage", "semantic_score", "terminology_mismatches", "overall_score"],
    "properties": {
        "keyword_coverage": {"type": "object"},
        "semantic_score": {"type": "number", "minimum": 0, "maximum": 1},
        "coverage_gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["requirement", "gap_type", "impact"],
                "properties": {
                    "requirement": {"type": "string"},
                    "gap_type": {"enum": ["hard", "soft"], "type": "string"},
                    "impact": {"type": "string"},
                },
            },
        },
        "terminology_mismatches": {
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
        "overall_score": {"type": "number", "minimum": 0, "maximum": 1},
    },
}

_REFINEMENT_SCHEMA = {
    "type": "object",
    "required": ["refined_content"],
    "properties": {
        "refined_content": {"type": "string"},
        "changes_made": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["section", "change_description"],
                "properties": {
                    "section": {"type": "string"},
                    "change_description": {"type": "string"},
                },
            },
        },
        "remaining_gaps": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["requirement", "why_unfixable"],
                "properties": {
                    "requirement": {"type": "string"},
                    "why_unfixable": {"type": "string"},
                },
            },
        },
        "coverage_improvement": {"type": "number", "minimum": 0, "maximum": 1},
    },
}


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


def _format_resume_for_screener(resume_data: dict[str, Any]) -> str:
    """Format generated resume back into text for screener analysis."""
    lines = []
    if resume_data.get("summary"):
        lines.append(f"## Summary\n{resume_data['summary']}")
    if resume_data.get("experience"):
        lines.append("## Experience")
        for job in resume_data["experience"]:
            lines.append(f"**{job['title']}** at {job['company']} ({job['dates']})")
            for bullet in job.get("bullets", []):
                lines.append(f"- {bullet}")
    if resume_data.get("skills"):
        lines.append(f"## Skills\n{', '.join(resume_data['skills'])}")
    if resume_data.get("education"):
        lines.append("## Education")
        for edu in resume_data["education"]:
            lines.append(f"- {edu['name']}: {edu['degree']} ({edu['year']})")
    return "\n\n".join(lines)


def _run_generator(jd_content: str, narratives_text: str, user_id: str) -> dict[str, Any]:
    """Step 1: Generator perspective — create resume from JD + narratives."""
    system_prompt = load_prompt("generator", user_id)
    user_message = (
        f"<job_description>\n{jd_content}\n</job_description>\n\n"
        f"<candidate_background>\n{narratives_text}\n</candidate_background>\n\n"
        "Generate a tailored resume for this candidate and job description. "
        "Use the submit_resume_draft tool to submit your output."
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
                    "name": "submit_resume_draft",
                    "description": "Submit the generated resume draft",
                    "input_schema": _GENERATOR_SCHEMA,
                }
            ],
        ),
        tool_choice={"type": "tool", "name": "submit_resume_draft"},
    )

    try:
        tool_block = next(b for b in response.content if b.type == "tool_use")
    except StopIteration:
        raise RuntimeError("Generator: No tool_use block in response")

    return cast(dict[str, Any], tool_block.input)


def _run_screener(jd_content: str, resume_text: str, user_id: str) -> dict[str, Any]:
    """Step 2: Screener perspective — analyze resume against JD."""
    system_prompt = load_prompt("resume_screener", user_id)
    user_message = (
        f"<job_description>\n{jd_content}\n</job_description>\n\n"
        f"<resume>\n{resume_text}\n</resume>\n\n"
        "Analyze this resume against the job description from an ATS perspective. "
        "Use the submit_screener_analysis tool to submit your assessment."
    )

    response = _get_anthropic_client().messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        tools=cast(
            Any,
            [
                {
                    "name": "submit_screener_analysis",
                    "description": "Submit the ATS screener analysis",
                    "input_schema": _SCREENER_SCHEMA,
                }
            ],
        ),
        tool_choice={"type": "tool", "name": "submit_screener_analysis"},
    )

    try:
        tool_block = next(b for b in response.content if b.type == "tool_use")
    except StopIteration:
        raise RuntimeError("Screener: No tool_use block in response")

    return cast(dict[str, Any], tool_block.input)


def _run_refinement(
    resume_data: dict[str, Any],
    screener_report: dict[str, Any],
    narratives_text: str,
    jd_content: str,
    user_id: str,
) -> dict[str, Any]:
    """Step 3: Refinement perspective — improve resume while preserving voice."""
    system_prompt = load_prompt("refinement", user_id)
    resume_text = _format_resume_for_screener(resume_data)

    user_message = (
        f"<job_description>\n{jd_content}\n</job_description>\n\n"
        f"<generated_resume>\n{resume_text}\n</generated_resume>\n\n"
        f"<screener_feedback>\n{screener_report}\n</screener_feedback>\n\n"
        f"<candidate_narratives>\n{narratives_text}\n</candidate_narratives>\n\n"
        "Refine the resume using the screener feedback while preserving authentic voice "
        "from the narratives. "
        "Use the submit_refined_resume tool to submit the refined resume and changes."
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
                    "name": "submit_refined_resume",
                    "description": "Submit the refined resume",
                    "input_schema": _REFINEMENT_SCHEMA,
                }
            ],
        ),
        tool_choice={"type": "tool", "name": "submit_refined_resume"},
    )

    try:
        tool_block = next(b for b in response.content if b.type == "tool_use")
    except StopIteration:
        raise RuntimeError("Refinement: No tool_use block in response")

    return cast(dict[str, Any], tool_block.input)


def _run_full_regenerate(jd_id: str, user_id: str) -> dict[str, Any]:
    """Full regenerate mode: all three steps from scratch."""
    # Load inputs
    jd = job_descriptions.get_jd(jd_id, user_id)
    if jd is None:
        raise ValueError(f"Job description not found: {jd_id}")

    narrative_rows = narratives.list_narratives(user_id)
    narratives_text = _format_narratives(narrative_rows)

    # Step 1: Generate
    try:
        resume_data = _run_generator(jd["content"], narratives_text, user_id)
    except Exception as e:
        raise RuntimeError(f"generator_failed: {str(e)}")

    # Format resume for screener
    resume_text = _format_resume_for_screener(resume_data)

    # Step 2: Screen
    try:
        screener_data = _run_screener(jd["content"], resume_text, user_id)
    except Exception as e:
        raise RuntimeError(f"screener_failed: {str(e)}")

    # Step 3: Refine
    try:
        refinement_data = _run_refinement(
            resume_data, screener_data, narratives_text, jd["content"], user_id
        )
    except Exception as e:
        raise RuntimeError(f"refinement_failed: {str(e)}")

    # Build screener_report
    screener_report = {
        "screener_analysis": screener_data,
        "refinement_changes": {
            "sections_modified": [c["section"] for c in refinement_data.get("changes_made", [])],
            "changes": refinement_data.get("changes_made", []),
            "remaining_gaps": refinement_data.get("remaining_gaps", []),
            "coverage_improvement": refinement_data.get("coverage_improvement", 0),
        },
    }

    # Get version number
    latest = resume_variants.get_latest_variant(jd_id, user_id)
    version = (latest["version"] + 1) if latest else 1

    # Save to DB
    result = resume_variants.create_resume_variant(
        job_description_id=jd_id,
        user_id=user_id,
        content=refinement_data["refined_content"],
        version=version,
        screener_report=screener_report,
    )
    return result


def _run_refine_existing(jd_id: str, user_id: str, parent_variant_id: str) -> dict[str, Any]:
    """Refine-existing mode: reuse generator + screener, run refinement only."""
    # Load inputs
    jd = job_descriptions.get_jd(jd_id, user_id)
    if jd is None:
        raise ValueError(f"Job description not found: {jd_id}")

    parent = resume_variants.get_latest_variant(jd_id, user_id)
    if parent is None or parent["id"] != parent_variant_id:
        raise ValueError(f"Variant not found: {parent_variant_id}")

    narrative_rows = narratives.list_narratives(user_id)
    narratives_text = _format_narratives(narrative_rows)

    # Extract previous screener data from parent variant
    screener_report = parent.get("screener_report", {})
    screener_data = screener_report.get("screener_analysis", {})

    # Step 3: Refine (using previous screener data)
    try:
        refinement_data = _run_refinement(
            {"summary": "", "experience": [], "skills": []},  # Placeholder, we use text version
            screener_data,
            narratives_text,
            jd["content"],
            user_id,
        )
    except Exception as e:
        raise RuntimeError(f"refinement_failed: {str(e)}")

    # Build updated screener_report
    updated_screener_report = {
        "screener_analysis": screener_data,
        "refinement_changes": {
            "sections_modified": [c["section"] for c in refinement_data.get("changes_made", [])],
            "changes": refinement_data.get("changes_made", []),
            "remaining_gaps": refinement_data.get("remaining_gaps", []),
            "coverage_improvement": refinement_data.get("coverage_improvement", 0),
        },
    }

    # Get version number
    version = parent["version"] + 1

    # Save new variant (refine-existing is a new version)
    result = resume_variants.create_resume_variant(
        job_description_id=jd_id,
        user_id=user_id,
        content=refinement_data["refined_content"],
        version=version,
        screener_report=updated_screener_report,
        parent_variant_id=parent_variant_id,
    )
    return result


def run_resume_generation(
    jd_id: str, user_id: str, mode: str = "full", parent_variant_id: str | None = None
) -> dict[str, Any]:
    """Run resume generation pipeline (generator → screener → refinement).

    Args:
        jd_id: Job description ID
        user_id: User ID
        mode: "full" for full regenerate, "refine" for refine-existing
        parent_variant_id: Variant to refine from (required if mode="refine")

    Returns:
        Resume variant row from database

    Raises:
        ValueError: If JD or variant not found
        RuntimeError: If any step fails
    """
    if mode == "full":
        return _run_full_regenerate(jd_id, user_id)
    elif mode == "refine":
        if parent_variant_id is None:
            raise ValueError("parent_variant_id required for refine mode")
        return _run_refine_existing(jd_id, user_id, parent_variant_id)
    else:
        raise ValueError(f"Unknown mode: {mode}")
