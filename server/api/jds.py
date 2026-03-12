"""ColdRead API routes for job descriptions and pipeline results."""

from fastapi import APIRouter, HTTPException

from db import fit_reports, job_descriptions, resume_variants
from models import (
    CreateJdRequest,
    FitReportResponse,
    JobDescriptionResponse,
    ResumeVariantResponse,
)

router = APIRouter(prefix="/jds", tags=["job-descriptions"])


# ---------------------------------------------------------------------------
# Job Descriptions
# ---------------------------------------------------------------------------


@router.post("", response_model=JobDescriptionResponse, status_code=201)
def create_jd(body: CreateJdRequest) -> JobDescriptionResponse:
    row = job_descriptions.create_jd(body.title, body.company, body.content)
    return JobDescriptionResponse(**row)


@router.get("", response_model=list[JobDescriptionResponse])
def list_jds() -> list[JobDescriptionResponse]:
    rows = job_descriptions.list_jds()
    return [JobDescriptionResponse(**r) for r in rows]


# ---------------------------------------------------------------------------
# Fit Reports
# ---------------------------------------------------------------------------


@router.get("/{jd_id}/fit", response_model=FitReportResponse)
def get_fit_report(jd_id: str) -> FitReportResponse:
    row = fit_reports.get_latest_fit_report(jd_id)
    if row is None:
        raise HTTPException(status_code=404, detail="No fit report found")
    return FitReportResponse(**row)


# ---------------------------------------------------------------------------
# Resume Variants
# ---------------------------------------------------------------------------


@router.get("/{jd_id}/resume", response_model=ResumeVariantResponse)
def get_latest_resume(jd_id: str) -> ResumeVariantResponse:
    row = resume_variants.get_latest_variant(jd_id)
    if row is None:
        raise HTTPException(status_code=404, detail="No resume variant found")
    return ResumeVariantResponse(**row)


@router.get("/{jd_id}/resume/variants", response_model=list[ResumeVariantResponse])
def list_resume_variants(jd_id: str) -> list[ResumeVariantResponse]:
    rows = resume_variants.list_variants(jd_id)
    return [ResumeVariantResponse(**r) for r in rows]
