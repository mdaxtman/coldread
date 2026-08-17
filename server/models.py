"""Pydantic models for ColdRead API request/response serialization."""

import json
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


class UpdateJdRequest(CamelModel):
    title: str


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


class CulturalSignalModel(CamelModel):
    quality: str
    jd_signal: str
    evidence_hint: str


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

    name: str | None = None
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
    overall_score: float | None = None
    semantic_score: float | None = None
    cultural_signals: list[CulturalSignalModel] = []
    product_connection: str | None = None


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


# ---------------------------------------------------------------------------
# Response models — Observability (Runs / Prompts / Usage)
# ---------------------------------------------------------------------------


class PipelineRunResponse(CamelModel):
    id: str
    job_description_id: str
    kind: str
    status: str
    error: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: int | None = None
    tokens_in: int
    tokens_out: int
    est_cost_usd: float
    jd_title: str | None = None
    jd_company: str | None = None


def _size_marker(value: Any) -> str:
    """Stand in for private content, keeping its scale so the inspector stays useful."""
    if isinstance(value, str):
        size = len(value)
    else:
        try:
            size = len(json.dumps(value, default=str))
        except (TypeError, ValueError):
            return "[redacted]"
    return f"[redacted] — {size:,} chars"


class MessageView(CamelModel):
    """One message from a stored request.

    `content` is always a size marker. The message bodies are the candidate
    narratives and the job description, which must not cross the wire (#40); the
    role and the count are what the inspector actually needs.
    """

    role: str | None = None
    content: str


class ContentBlockView(CamelModel):
    """One block of a model response, limited to what the run inspector renders.

    `input` stays `dict[str, Any]` on purpose: a tool_use block's input is the
    model's structured output and its shape varies per tool, so it is genuinely
    dynamic rather than an unwritten contract.
    """

    type: str
    text: str | None = None
    name: str | None = None
    input: dict[str, Any] | None = None


class RequestView(CamelModel):
    """Allowlist of the stored request envelope.

    Anything not named here never reaches the client — including fields the
    Anthropic SDK may add later. That is the point: a denylist forwards unknown
    fields by default, an allowlist withholds them by default.
    """

    model: str | None = None
    system: str | None = None
    messages: list[MessageView] = []
    tool_names: list[str] = []

    @classmethod
    def from_payload(cls, payload: Any) -> "RequestView":
        if not isinstance(payload, dict):
            return cls()

        raw_messages = payload.get("messages")
        messages = (
            [
                MessageView(
                    role=m.get("role") if isinstance(m, dict) else None,
                    content=_size_marker(m.get("content") if isinstance(m, dict) else m),
                )
                for m in raw_messages
            ]
            if isinstance(raw_messages, list)
            else []
        )

        raw_tools = payload.get("tools")
        tool_names = (
            [t.get("name", "") for t in raw_tools if isinstance(t, dict)]
            if isinstance(raw_tools, list)
            else []
        )

        system = payload.get("system")
        return cls(
            model=payload.get("model") if isinstance(payload.get("model"), str) else None,
            system=_size_marker(system) if system is not None else None,
            messages=messages,
            tool_names=tool_names,
        )


class ModelCallResponse(CamelModel):
    id: str
    stage: str
    seq: int
    model: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    stop_reason: str | None = None
    est_cost_usd: float
    request: RequestView
    response: list[ContentBlockView]
    created_at: datetime

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "ModelCallResponse":
        """Build the wire contract from a stored `model_calls` row.

        The stored payload stays complete in the database — reading a raw request
        is how the malformed tool call in #48 was diagnosed. Only what crosses the
        API boundary is narrowed.
        """
        raw_blocks = row.get("response")
        blocks = (
            [b for b in raw_blocks if isinstance(b, dict)] if isinstance(raw_blocks, list) else []
        )
        return cls(
            **{k: v for k, v in row.items() if k not in ("request", "response")},
            request=RequestView.from_payload(row.get("request")),
            response=[
                ContentBlockView(
                    type=str(b.get("type", "")),
                    text=b.get("text"),
                    name=b.get("name"),
                    input=b.get("input") if isinstance(b.get("input"), dict) else None,
                )
                for b in blocks
            ],
        )


class RunDetailResponse(CamelModel):
    run: PipelineRunResponse
    calls: list[ModelCallResponse]


class PromptResponse(CamelModel):
    id: str
    stage: str
    name: str
    version: int
    active: bool
    template: str


class UsageSummaryResponse(CamelModel):
    tokens_in: int
    tokens_out: int
    est_cost_usd: float
    run_count: int
