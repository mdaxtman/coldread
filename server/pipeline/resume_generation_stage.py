"""Resume generation stage — independent module for strategic resume creation.

Extracts resume generation as a reusable pipeline stage that accepts
ResumeGenerationInput and returns ResumeGenerationOutput with a markdown-formatted
resume guided by fit assessment context.
"""

from typing import Any, cast

from pipeline.anthropic_utils import _extract_tool_response, _get_anthropic_client
from pipeline.prompt_loader import load_prompt
from pipeline.stage_input import ResumeGenerationInput, ResumeGenerationOutput

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
        "contact": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "location": {"type": "string"},
                "linkedin": {"type": "string"},
                "github": {"type": "string"},
                "website": {"type": "string"},
            },
        },
    },
}


def _format_fit_context(fit_assessment: dict[str, Any]) -> str:
    """Format fit assessment into context for resume generation.

    Converts the pre-computed fit assessment into readable guidance showing:
    - Fit level classification
    - What requirements are matched
    - What gaps exist
    - Terminology mappings to use

    Args:
        fit_assessment: Fit assessment output from screener stage

    Returns:
        Formatted text describing fit assessment context
    """
    lines = []

    # Fit level summary
    fit_level = fit_assessment.get("fit_level", "unknown")
    overall_score = fit_assessment.get("overall_score", 0.5)
    lines.append(f"Fit Assessment: {fit_level.upper()} ({overall_score:.0%})")

    # MATCHES section
    matches = fit_assessment.get("matches", [])
    if matches:
        lines.append("\nMATCHES (emphasize these):")
        for match in matches:
            priority = match.get("priority", "required").upper()
            req = match.get("requirement", "")
            lines.append(f"  - [{priority}] {req}")

    # GAPS section
    gaps = fit_assessment.get("gaps", [])
    soft_gaps = [g for g in gaps if g.get("type") == "soft"]
    hard_gaps = [g for g in gaps if g.get("type") == "hard"]

    if soft_gaps:
        lines.append("\nGAPS - SOFT (position adjacent strengths if relevant):")
        for gap in soft_gaps:
            req = gap.get("requirement", "")
            lines.append(f"  - {req}")

    if hard_gaps:
        lines.append("\nGAPS - HARD (leave as gap, do not bridge):")
        for gap in hard_gaps:
            req = gap.get("requirement", "")
            lines.append(f"  - {req}")

    # TERMINOLOGY section
    terminology = fit_assessment.get("terminology", [])
    if terminology:
        lines.append("\nTERMINOLOGY (use JD's exact terms where applicable):")
        for term in terminology:
            my_term = term.get("my_term", "")
            jd_term = term.get("jd_term", "")
            lines.append(f"  - {my_term} → {jd_term}")

    return "\n".join(lines)


def _format_contact_info(contact_info: dict[str, str] | None) -> str:
    """Format contact info into readable text for generator prompt.

    Args:
        contact_info: Optional dict with email, phone, location, linkedin, github, website

    Returns:
        Formatted contact info text
    """
    if not contact_info:
        return ""

    lines = []
    if contact_info.get("email"):
        lines.append(f"Email: {contact_info['email']}")
    if contact_info.get("phone"):
        lines.append(f"Phone: {contact_info['phone']}")
    if contact_info.get("location"):
        lines.append(f"Location: {contact_info['location']}")
    if contact_info.get("linkedin"):
        lines.append(f"LinkedIn: {contact_info['linkedin']}")
    if contact_info.get("github"):
        lines.append(f"GitHub: {contact_info['github']}")
    if contact_info.get("website"):
        lines.append(f"Website: {contact_info['website']}")

    return "\n".join(lines)


def _build_resume_markdown(resume_data: dict[str, Any]) -> str:
    """Convert structured resume data to markdown format.

    Builds a markdown resume from the structured data returned by Claude,
    including summary, experience, and skills sections with proper formatting.

    Args:
        resume_data: Structured resume containing summary, experience, skills, contact

    Returns:
        Markdown-formatted resume string
    """
    lines = []

    # Contact info header (if available)
    contact = resume_data.get("contact", {})
    if isinstance(contact, dict) and contact:
        contact_parts = []
        if contact.get("email"):
            contact_parts.append(contact["email"])
        if contact.get("phone"):
            contact_parts.append(contact["phone"])
        if contact.get("location"):
            contact_parts.append(contact["location"])
        if contact.get("linkedin"):
            contact_parts.append(contact["linkedin"])
        if contact.get("github"):
            contact_parts.append(contact["github"])
        if contact.get("website"):
            contact_parts.append(contact["website"])

        if contact_parts:
            lines.append(" | ".join(contact_parts))
            lines.append("")

    # Summary section
    summary = resume_data.get("summary", "")
    if summary:
        lines.append("## Summary")
        lines.append(summary)
        lines.append("")

    # Experience section
    experience = resume_data.get("experience", [])
    if experience:
        lines.append("## Experience")
        for exp in experience:
            company = exp.get("company", "")
            title = exp.get("title", "")
            dates = exp.get("dates", "")

            # Company / Title header
            if company and title:
                lines.append(f"### {title} at {company}")
            elif company or title:
                lines.append(f"### {company or title}")

            if dates:
                lines.append(f"_{dates}_")

            # Projects
            projects = exp.get("projects", [])
            for project in projects:
                project_name = project.get("name", "")
                project_dates = project.get("dates", "")
                bullets = project.get("bullets", [])

                if project_name:
                    lines.append(f"**{project_name}**")
                    if project_dates:
                        lines.append(f"_{project_dates}_")

                for bullet in bullets:
                    lines.append(f"- {bullet}")

            lines.append("")

    # Skills section
    skills = resume_data.get("skills", [])
    if skills:
        lines.append("## Skills")
        lines.append(", ".join(skills))
        lines.append("")

    return "\n".join(lines).strip()


def run_resume_generation_stage(input_data: ResumeGenerationInput) -> ResumeGenerationOutput:
    """Run the resume generation stage (writer perspective).

    Creates a strategic resume tailored to the job by using the fit assessment
    to guide emphasis, handle gaps appropriately, and adopt JD terminology.

    Args:
        input_data: ResumeGenerationInput containing narratives, fit assessment,
            contact info, and user_id

    Returns:
        ResumeGenerationOutput with markdown-formatted resume and contact info

    Raises:
        RuntimeError: If API call fails or no tool response found
        ValueError: If no active prompt found for generator stage
    """
    # Load system prompt from database
    system_prompt = load_prompt("generator", input_data.user_id)

    # Format fit assessment context and contact info
    fit_context = _format_fit_context(
        {
            "fit_level": input_data.fit_assessment_output.fit_level,
            "overall_score": input_data.fit_assessment_output.overall_score,
            "semantic_score": input_data.fit_assessment_output.semantic_score,
            "matches": input_data.fit_assessment_output.matches,
            "gaps": input_data.fit_assessment_output.gaps,
            "terminology": input_data.fit_assessment_output.terminology,
        }
    )
    contact_text = _format_contact_info(input_data.contact_info)

    # Build user message with context
    user_message = (
        f"<candidate_background>\n{input_data.narratives_text}\n</candidate_background>\n\n"
        f"<fit_assessment>\n{fit_context}\n</fit_assessment>\n\n"
    )

    if contact_text:
        user_message += f"<contact_info>\n{contact_text}\n</contact_info>\n\n"

    user_message += (
        "Create a focused, strategic resume that highlights strengths matching the role. "
        "Use the fit assessment above to guide emphasis, handle gaps appropriately, and use the "
        "exact terminology from the JD. "
        "Include your contact information in the contact field if provided. "
        "Use the submit_resume_draft tool to submit your output."
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
                    "description": "Submit the generated resume draft",
                    "input_schema": _GENERATOR_SCHEMA,
                }
            ],
        ),
        tool_choice={"type": "tool", "name": _TOOL_NAME},
    )

    # Extract tool response (structured resume data)
    resume_data = _extract_tool_response(response)

    # Convert structured resume to markdown
    markdown_content = _build_resume_markdown(resume_data)

    # Return structured output
    return ResumeGenerationOutput(
        content=markdown_content,
        contact_info=input_data.contact_info,
    )
