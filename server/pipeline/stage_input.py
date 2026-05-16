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
        overall_score: Overall fit score (0.0-1.0)
        semantic_score: Semantic alignment score (0.0-1.0)
        keyword_coverage: Mapping of keywords to coverage status
    """

    fit_level: str  # "strong", "moderate", "borderline", "poor"
    matches: list[dict[str, Any]]  # [{requirement, priority, notes}]
    gaps: list[dict[str, Any]]  # [{requirement, type, notes}]
    terminology: list[dict[str, str]]  # [{my_term, jd_term, confidence}]
    overall_score: float
    semantic_score: float
    keyword_coverage: dict[str, bool]


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
        content: Markdown-formatted resume text
        contact_info: Optional contact information (email, phone, location, etc.)
    """

    content: str
    contact_info: dict[str, str] | None


@dataclass
class RefinementInput:
    """Input contract for refinement stage.

    Attributes:
        resume_content: Generated resume as markdown string
        fit_assessment_output: Pre-computed fit assessment for gap reference
        jd_content: Job description for alignment checking
        user_id: Current user ID (scoped for multi-user readiness)
    """

    resume_content: str
    fit_assessment_output: FitAssessmentOutput
    jd_content: str
    user_id: str


@dataclass
class RefinementOutput:
    """Output contract for refinement stage.

    Attributes:
        refined_content: Refined resume as markdown string
        changes_made: List of change descriptions applied to the resume
    """

    refined_content: str
    changes_made: list[str]
