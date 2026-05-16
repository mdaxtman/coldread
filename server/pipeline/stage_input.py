"""Input and output contracts for resume generation pipeline stages.

This module defines Pydantic dataclasses that specify the precise input
and output contracts for each stage of the pipeline:
- Fit Assessment: evaluate candidate against JD
- Resume Generation: create tailored resume draft
- Refinement: improve resume while preserving voice
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class FitAssessmentInput:
    """Input contract for fit assessment stage.

    Attributes:
        jd_content: Raw job description text to evaluate against
        narratives_text: Formatted candidate background narratives
        user_id: Current user ID (scoped for multi-user readiness)
    """

    jd_content: str
    narratives_text: str
    user_id: str


@dataclass
class FitAssessmentOutput:
    """Output contract for fit assessment stage.

    Attributes:
        fit_level: Overall fit classification (strong/moderate/borderline/poor)
        matches: List of matched requirements with priority and notes
        gaps: List of unmet requirements with type (hard/soft) and notes
        terminology: List of term mappings from candidate to JD terminology
        reasoning: Narrative explanation of the assessment
    """

    fit_level: str  # "strong", "moderate", "borderline", "poor"
    matches: list[dict[str, Any]]  # [{requirement, priority, notes}]
    gaps: list[dict[str, Any]]  # [{requirement, type, notes}]
    terminology: list[dict[str, str]]  # [{my_term, jd_term, confidence}]
    reasoning: str


@dataclass
class ResumeGenerationInput:
    """Input contract for resume generation stage.

    Attributes:
        narratives_text: Formatted candidate background narratives
        fit_assessment_output: Pre-computed fit assessment to guide generation
        contact_info: Optional contact information (email, phone, location, etc.)
        user_id: Current user ID (scoped for multi-user readiness)
    """

    narratives_text: str
    fit_assessment_output: FitAssessmentOutput
    contact_info: dict[str, str] | None
    user_id: str


@dataclass
class ResumeGenerationOutput:
    """Output contract for resume generation stage.

    Attributes:
        summary: Career summary section
        experience: List of past roles with projects and bullets
        skills: List of relevant skills
        contact: Contact information dict (email, phone, location, linkedin, github, website)
    """

    summary: str | None
    experience: list[dict[str, Any]]  # [{company, title, dates, projects}]
    skills: list[str]
    contact: dict[str, str] | None


@dataclass
class RefinementInput:
    """Input contract for refinement stage.

    Attributes:
        resume_content: Generated resume data (structured or markdown)
        fit_assessment_output: Pre-computed fit assessment for gap reference
        jd_content: Job description for alignment checking
        user_id: Current user ID (scoped for multi-user readiness)
    """

    resume_content: Any  # Can be dict (structured) or str (markdown)
    fit_assessment_output: FitAssessmentOutput
    jd_content: str
    user_id: str


@dataclass
class RefinementOutput:
    """Output contract for refinement stage.

    Attributes:
        refined_content: Refined resume as markdown or HTML string
        changes_made: List of changes applied with descriptions
        remaining_gaps: Hard gaps that couldn't be addressed
    """

    refined_content: str
    changes_made: list[dict[str, str]] | None  # [{section, change_description}]
    remaining_gaps: list[dict[str, str]] | None  # [{requirement, why_unfixable}]
