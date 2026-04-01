"""ColdRead API routes."""

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_current_user_id
from db import fit_reports, job_descriptions, resume_variants
from features import fit_assessment, resume_generation
from models import (
    CreateJdRequest,
    FitReportResponse,
    GenerateResumeRequest,
    JobDescriptionResponse,
    ResumeVariantResponse,
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
    jd = job_descriptions.get_jd(jd_id, user_id)
    if jd is None:
        raise HTTPException(status_code=404, detail="Job description not found")


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
    return FitReportResponse(**row)


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
        row = resume_generation.run_resume_generation(jd_id, user_id, fit_report, mode="full")
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
            jd_id, user_id, fit_report, mode="refine", parent_variant_id=variant_id
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


router.include_router(jds)
