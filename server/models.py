"""Pydantic models for ColdRead API request/response serialization."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model that serializes snake_case fields as camelCase in JSON responses."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


# ---------------------------------------------------------------------------
# Request models — Job Descriptions
# ---------------------------------------------------------------------------


class CreateJdRequest(CamelModel):
    content: str


class GenerateResumeRequest(CamelModel):
    fit_report_id: str


# ---------------------------------------------------------------------------
# Response models — Job Descriptions & Pipeline Results
# ---------------------------------------------------------------------------


class JobDescriptionResponse(CamelModel):
    id: str
    user_id: str
    title: str | None = None
    company: str | None = None
    content: str
    created_at: datetime


class MatchModel(CamelModel):
    requirement: str
    priority: Literal["required", "preferred", "implied"]
    notes: str


class GapModel(CamelModel):
    requirement: str
    type: Literal["hard", "soft"]
    notes: str


class TerminologyAlignmentModel(CamelModel):
    my_term: str
    jd_term: str


class ScreenerAnalysisModel(CamelModel):
    """ATS screener analysis: what the resume is missing or could improve."""

    keyword_coverage: dict[str, bool]
    semantic_score: float
    terminology_mismatches: list[TerminologyAlignmentModel]
    overall_score: float
    coverage_gaps: list[dict[str, str]] | None = None


class RefinementChangesModel(CamelModel):
    """Changes made during refinement step to improve the resume."""

    sections_modified: list[str]
    changes: list[dict[str, str]]
    remaining_gaps: list[dict[str, str]]
    coverage_improvement: float


class ScreenerReportModel(CamelModel):
    """Complete screener report: analysis + refinement changes."""

    screener_analysis: ScreenerAnalysisModel
    refinement_changes: RefinementChangesModel


class ResumeContact(CamelModel):
    """Contact information in resume."""

    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    website: str | None = None


class FitReportResponse(CamelModel):
    id: str
    user_id: str
    job_description_id: str
    fit_level: Literal["strong", "moderate", "borderline", "poor"]
    matches: list[MatchModel]
    gaps: list[GapModel]
    terminology: list[TerminologyAlignmentModel]
    reasoning: str
    created_at: datetime


class ResumeVariantResponse(CamelModel):
    id: str
    user_id: str
    job_description_id: str
    content: str
    contact_info: ResumeContact | None = None
    version: int
    parent_variant_id: str | None = None
    screener_report: ScreenerReportModel
    created_at: datetime
