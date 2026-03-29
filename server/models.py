"""Pydantic models for ColdRead API request/response serialization."""

from datetime import datetime
from typing import Any, Literal

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
    version: int
    parent_variant_id: str | None = None
    screener_report: dict[str, Any]
    created_at: datetime
