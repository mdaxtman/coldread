"""Resume generation stage — independent module for strategic resume creation.

Extracts resume generation as a reusable pipeline stage that accepts
ResumeGenerationInput and returns ResumeGenerationOutput with a markdown-formatted
resume guided by fit assessment context.

The request itself is built by `pipeline.generator.run_generator`, the same
call the app's routes make. This module once built its own copy, and the copy
missed every later change to the request: the posting, the bullet budget, the
gap labels, draft validation and role ordering. Both load the one `generator`
prompt, so the copy was sending a request that prompt was no longer written for.
"""

from dataclasses import asdict
from typing import Any

from pipeline.generator import order_roles, run_generator
from pipeline.stage_input import ResumeGenerationInput, ResumeGenerationOutput


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
        input_data: ResumeGenerationInput containing narratives, the posting,
            fit assessment, contact info, and user_id

    Returns:
        ResumeGenerationOutput with markdown-formatted resume and contact info

    Raises:
        RuntimeError: If API call fails or no usable draft is returned
        ValueError: If no active prompt found for generator stage
    """
    resume_data = order_roles(
        run_generator(
            input_data.narratives_text,
            asdict(input_data.fit_assessment_output),
            input_data.contact_info,
            input_data.jd_content,
            input_data.user_id,
        )
    )

    return ResumeGenerationOutput(
        content=_build_resume_markdown(resume_data),
        contact_info=input_data.contact_info,
    )
