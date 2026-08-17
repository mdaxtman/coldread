"""ColdRead API routes."""

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_current_user_id
from api.redaction import redact_request
from db import fit_reports, job_descriptions, pipeline_runs, resume_variants
from db import prompts as prompts_db
from features import fit_assessment, resume_generation
from models import (
    CreateJdRequest,
    FitReportResponse,
    GenerateResumeRequest,
    JobDescriptionResponse,
    ModelCallResponse,
    PipelineRunResponse,
    PromptResponse,
    ResumeVariantResponse,
    RunDetailResponse,
    UpdateJdRequest,
    UsageSummaryResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Job Descriptions
# ---------------------------------------------------------------------------

jds = APIRouter(prefix="/jds", tags=["job-descriptions"])


def _verify_jd_ownership(jd_id: str, user_id: str) -> None:
    """Raise 404 if the JD does not exist or does not belong to the user.

    Uses 404 (not 403) to avoid leaking whether a resource ID is valid.
    """
    try:
        jd = job_descriptions.get_jd(jd_id, user_id)
        if jd is None:
            raise HTTPException(status_code=404, detail="Job description not found")
    except Exception as e:
        # Handle database errors (e.g., invalid UUID format)
        if "invalid input syntax" in str(e) or "uuid" in str(e).lower():
            raise HTTPException(status_code=404, detail="Job description not found")
        raise


@jds.post("", response_model=JobDescriptionResponse, status_code=201)
def create_jd(
    body: CreateJdRequest,
    user_id: str = Depends(get_current_user_id),
) -> JobDescriptionResponse:
    # Validate JD content
    if not body.content or not body.content.strip():
        raise HTTPException(status_code=400, detail="Job description content cannot be empty")

    if len(body.content) > 50000:
        raise HTTPException(
            status_code=400, detail="Job description exceeds maximum length (50,000 characters)"
        )

    row = job_descriptions.create_jd(body.content, user_id)
    return JobDescriptionResponse(**row)


@jds.get("", response_model=list[JobDescriptionResponse])
def list_jds(
    user_id: str = Depends(get_current_user_id),
) -> list[JobDescriptionResponse]:
    rows = job_descriptions.list_jds(user_id)
    return [JobDescriptionResponse(**r) for r in rows]


@jds.get("/{jd_id}", response_model=JobDescriptionResponse)
def get_jd(
    jd_id: str,
    user_id: str = Depends(get_current_user_id),
) -> JobDescriptionResponse:
    row = job_descriptions.get_jd(jd_id, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Job description not found")
    return JobDescriptionResponse(**row)


@jds.patch("/{jd_id}", response_model=JobDescriptionResponse)
def update_jd(
    jd_id: str,
    body: UpdateJdRequest,
    user_id: str = Depends(get_current_user_id),
) -> JobDescriptionResponse:
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    if len(title) > 200:
        raise HTTPException(status_code=400, detail="Title exceeds maximum length (200 characters)")
    _verify_jd_ownership(jd_id, user_id)
    row = job_descriptions.update_jd_title(jd_id, user_id, title)
    if row is None:
        raise HTTPException(status_code=404, detail="Job description not found")
    return JobDescriptionResponse(**row)


# ---------------------------------------------------------------------------
# Fit Reports
# ---------------------------------------------------------------------------


@jds.post("/{jd_id}/fit", response_model=FitReportResponse, status_code=201)
def run_fit(
    jd_id: str,
    user_id: str = Depends(get_current_user_id),
) -> FitReportResponse:
    _verify_jd_ownership(jd_id, user_id)
    try:
        row = fit_assessment.run_fit_assessment_workflow(jd_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return FitReportResponse(**row)


@jds.get("/{jd_id}/fit", response_model=FitReportResponse)
def get_fit_report(
    jd_id: str,
    user_id: str = Depends(get_current_user_id),
) -> FitReportResponse:
    _verify_jd_ownership(jd_id, user_id)
    row = fit_reports.get_latest_fit_report(jd_id, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="No fit report found")
    return FitReportResponse(**cast(Any, dict(row)))


# ---------------------------------------------------------------------------
# Resume Generation
# ---------------------------------------------------------------------------


@jds.post("/{jd_id}/resume", response_model=ResumeVariantResponse, status_code=201)
def generate_resume(
    jd_id: str,
    body: GenerateResumeRequest,
    user_id: str = Depends(get_current_user_id),
) -> ResumeVariantResponse:
    _verify_jd_ownership(jd_id, user_id)
    fit_report = fit_reports.get_fit_report_by_id(body.fit_report_id, user_id)
    if fit_report is None:
        raise HTTPException(status_code=404, detail="Fit report not found")
    try:
        row = resume_generation.run_resume_generation(jd_id, user_id, dict(fit_report), mode="full")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ResumeVariantResponse(**row)


@jds.post(
    "/{jd_id}/resume/refine/{variant_id}",
    response_model=ResumeVariantResponse,
    status_code=201,
)
def refine_resume(
    jd_id: str,
    variant_id: str,
    body: GenerateResumeRequest,
    user_id: str = Depends(get_current_user_id),
) -> ResumeVariantResponse:
    _verify_jd_ownership(jd_id, user_id)
    fit_report = fit_reports.get_fit_report_by_id(body.fit_report_id, user_id)
    if fit_report is None:
        raise HTTPException(status_code=404, detail="Fit report not found")
    try:
        row = resume_generation.run_resume_generation(
            jd_id, user_id, dict(fit_report), mode="refine", parent_variant_id=variant_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ResumeVariantResponse(**row)


# ---------------------------------------------------------------------------
# Resume Variants
# ---------------------------------------------------------------------------


@jds.get("/{jd_id}/resume", response_model=ResumeVariantResponse)
def get_latest_resume(
    jd_id: str,
    user_id: str = Depends(get_current_user_id),
) -> ResumeVariantResponse:
    _verify_jd_ownership(jd_id, user_id)
    row = resume_variants.get_latest_variant(jd_id, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="No resume variant found")
    return ResumeVariantResponse(**row)


@jds.get("/{jd_id}/resume/variants", response_model=list[ResumeVariantResponse])
def list_resume_variants(
    jd_id: str,
    user_id: str = Depends(get_current_user_id),
) -> list[ResumeVariantResponse]:
    _verify_jd_ownership(jd_id, user_id)
    rows = resume_variants.list_variants(jd_id, user_id)
    return [ResumeVariantResponse(**r) for r in rows]


# ---------------------------------------------------------------------------
# Observability (Runs / Prompts / Usage)
# ---------------------------------------------------------------------------

observability_router = APIRouter(tags=["observability"])


def _run_response(row: dict[str, Any]) -> PipelineRunResponse:
    jd = row.get("job_descriptions") or {}
    fields = cast(dict[str, Any], {k: v for k, v in row.items() if k != "job_descriptions"})
    return PipelineRunResponse(
        **fields,
        jd_title=jd.get("title"),
        jd_company=jd.get("company"),
    )


@observability_router.get("/runs", response_model=list[PipelineRunResponse])
def list_runs(user_id: str = Depends(get_current_user_id)) -> list[PipelineRunResponse]:
    return [_run_response(r) for r in pipeline_runs.list_runs(user_id)]


@observability_router.get("/runs/{run_id}", response_model=RunDetailResponse)
def get_run(run_id: str, user_id: str = Depends(get_current_user_id)) -> RunDetailResponse:
    row = pipeline_runs.get_run(run_id, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Run not found")
    # The stored request envelope carries the narratives and the system prompt, and
    # this API has no authentication — redact before it crosses the wire (#40).
    calls = [
        ModelCallResponse(**{**c, "request": redact_request(c.get("request") or {})})
        for c in pipeline_runs.list_calls(run_id, user_id)
    ]
    return RunDetailResponse(run=_run_response(row), calls=calls)


@observability_router.get("/prompts", response_model=list[PromptResponse])
def list_prompts(user_id: str = Depends(get_current_user_id)) -> list[PromptResponse]:
    return [PromptResponse(**p) for p in prompts_db.list_active_prompts(user_id)]


@observability_router.get("/usage/summary", response_model=UsageSummaryResponse)
def usage_summary(user_id: str = Depends(get_current_user_id)) -> UsageSummaryResponse:
    return UsageSummaryResponse(**pipeline_runs.usage_summary(user_id))


router.include_router(jds)
router.include_router(observability_router)

from api.streaming import streaming_router  # noqa: E402 — avoids circular import at module load

router.include_router(streaming_router)
