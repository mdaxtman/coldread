"""Pydantic models for ColdRead API request/response serialization."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model that serializes snake_case fields as camelCase in JSON responses."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


# ---------------------------------------------------------------------------
# Response models — Narratives
# ---------------------------------------------------------------------------


class NarrativeResponse(CamelModel):
    id: str
    user_id: str
    title: str
    content: str
    category: str | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Request models — Job Descriptions
# ---------------------------------------------------------------------------


class CreateJdRequest(CamelModel):
    title: str
    company: str
    content: str


# ---------------------------------------------------------------------------
# Response models — Job Descriptions & Pipeline Results
# ---------------------------------------------------------------------------


class JobDescriptionResponse(CamelModel):
    id: str
    user_id: str
    title: str
    company: str
    content: str
    created_at: datetime


class GapModel(CamelModel):
    requirement: str
    type: Literal["hard", "soft"]
    notes: str


class TerminologyAlignmentModel(CamelModel):
    my_term: str
    jd_term: str


class ScreenerReportModel(CamelModel):
    keyword_coverage: dict[str, bool]
    semantic_score: float
    terminology_mismatches: list[TerminologyAlignmentModel]
    overall_score: float


class FitReportResponse(CamelModel):
    id: str
    user_id: str
    job_description_id: str
    fit_level: Literal["strong", "moderate", "borderline", "poor"]
    matches: list[str]
    gaps: list[GapModel]
    terminology: list[TerminologyAlignmentModel]
    reasoning: str
    created_at: datetime


class ResumeVariantResponse(CamelModel):
    id: str
    user_id: str
    job_description_id: str
    content: str
    version: int
    parent_variant_id: str | None = None
    screener_report: ScreenerReportModel
    created_at: datetime
