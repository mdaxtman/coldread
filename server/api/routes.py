"""ColdRead API routes."""

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_current_user_id
from db import fit_reports, job_descriptions, resume_variants
from features import fit_assessment, resume_generation
from jobs.models import Job, JobQueue, JobType
from models import (
    CreateJdRequest,
    FitReportResponse,
    GenerateResumeRequest,
    JobDescriptionResponse,
    JobResponse,
    ResumeVariantResponse,
)

router = APIRouter()

# Global job queue instance
_job_queue = JobQueue()


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


def _get_fit_report_safe(fit_report_id: str, user_id: str) -> Any:
    """Get a fit report with proper error handling.

    Args:
        fit_report_id: Fit report ID
        user_id: Current user ID

    Returns:
        Fit report record

    Raises:
        HTTPException: If fit report not found or invalid ID format
    """
    try:
        fit_report = fit_reports.get_fit_report_by_id(fit_report_id, user_id)
        if fit_report is None:
            raise HTTPException(status_code=404, detail="Fit report not found")
        return fit_report
    except HTTPException:
        raise
    except Exception as e:
        # Handle database errors (e.g., invalid UUID format)
        if "invalid input syntax" in str(e) or "uuid" in str(e).lower():
            raise HTTPException(status_code=404, detail="Fit report not found")
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
# Async Job Endpoints
# ---------------------------------------------------------------------------

jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])


@jobs_router.post("/fit-assessment/{jd_id}", response_model=JobResponse, status_code=202)
def queue_fit_assessment(
    jd_id: str,
    user_id: str = Depends(get_current_user_id),
) -> JobResponse:
    """Queue a fit assessment job for a job description.

    Returns immediately with job_id and status (pending).
    The job will be processed asynchronously.

    Args:
        jd_id: Job description ID
        user_id: Current user ID

    Returns:
        Job response with job_id and status

    Raises:
        HTTPException: If JD not found or user doesn't own the JD
    """
    # Verify JD exists and belongs to user before queuing
    try:
        _verify_jd_ownership(jd_id, user_id)
    except HTTPException:
        raise

    job = Job.create(JobType.FIT_ASSESSMENT, user_id, jd_id=jd_id)
    _job_queue.add_job(job)

    return JobResponse(
        job_id=job.job_id,
        job_type=job.job_type.value,
        status=job.status.value,
        created_at=job.created_at,
        metadata=job.metadata,
    )


@jobs_router.post("/resume-generation", response_model=JobResponse, status_code=202)
def queue_resume_generation(
    body: GenerateResumeRequest,
    user_id: str = Depends(get_current_user_id),
) -> JobResponse:
    """Queue a resume generation job from a completed fit assessment.

    Returns immediately with job_id and status (pending).
    The job will be processed asynchronously.

    Args:
        body: Resume generation request with fit_report_id
        user_id: Current user ID

    Returns:
        Job response with job_id and status

    Raises:
        HTTPException: If fit report not found or user doesn't own it
    """
    # Verify the fit report exists and belongs to the user
    fit_report = _get_fit_report_safe(body.fit_report_id, user_id)

    job = Job.create(
        JobType.RESUME_GENERATION,
        user_id,
        fit_report_id=body.fit_report_id,
        jd_id=fit_report["job_description_id"],
    )
    _job_queue.add_job(job)

    return JobResponse(
        job_id=job.job_id,
        job_type=job.job_type.value,
        status=job.status.value,
        created_at=job.created_at,
        metadata=job.metadata,
    )


@jobs_router.post("/refinement/{variant_id}", response_model=JobResponse, status_code=202)
def queue_refinement(
    variant_id: str,
    body: GenerateResumeRequest,
    user_id: str = Depends(get_current_user_id),
) -> JobResponse:
    """Queue a resume refinement job for an existing resume variant.

    Returns immediately with job_id and status (pending).
    The job will be processed asynchronously.

    Args:
        variant_id: Resume variant ID to refine
        body: Refinement request with fit_report_id
        user_id: Current user ID

    Returns:
        Job response with job_id and status

    Raises:
        HTTPException: If variant or fit report not found
    """
    # Verify the fit report exists and belongs to the user
    fit_report = _get_fit_report_safe(body.fit_report_id, user_id)

    job = Job.create(
        JobType.REFINEMENT,
        user_id,
        fit_report_id=body.fit_report_id,
        variant_id=variant_id,
        jd_id=fit_report["job_description_id"],
    )
    _job_queue.add_job(job)

    return JobResponse(
        job_id=job.job_id,
        job_type=job.job_type.value,
        status=job.status.value,
        created_at=job.created_at,
        metadata=job.metadata,
    )


@jobs_router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    user_id: str = Depends(get_current_user_id),
) -> JobResponse:
    """Get the status of a queued job.

    Args:
        job_id: Job ID to retrieve
        user_id: Current user ID

    Returns:
        Job response with status and metadata

    Raises:
        HTTPException: If job not found or user doesn't own it
    """
    job = _job_queue.get_job(job_id)
    if job is None or job.user_id != user_id:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        job_id=job.job_id,
        job_type=job.job_type.value,
        status=job.status.value,
        created_at=job.created_at,
        metadata=job.metadata,
    )


router.include_router(jds)
router.include_router(jobs_router)

from api.streaming import streaming_router  # noqa: E402 — avoids circular import at module load

router.include_router(streaming_router)
