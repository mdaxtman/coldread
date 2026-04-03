"""Data access layer for fit reports."""

from typing import Any, Literal, TypedDict, cast

from db.client import get_client


class Match(TypedDict):
    requirement: str
    priority: Literal["required", "preferred", "implied"]
    notes: str


class Gap(TypedDict):
    requirement: str
    type: Literal["hard", "soft"]
    notes: str


class TerminologyItem(TypedDict):
    my_term: str
    jd_term: str
    confidence: float


class FitReport(TypedDict):
    id: str
    user_id: str
    job_description_id: str
    fit_level: Literal["strong", "moderate", "borderline", "poor"]
    matches: list[Match]
    gaps: list[Gap]
    terminology: list[TerminologyItem]
    reasoning: str
    created_at: str


def create_fit_report(
    job_description_id: str,
    user_id: str,
    fit_level: str,
    matches: list[Match],
    gaps: list[Gap],
    terminology: list[TerminologyItem],
    reasoning: str,
) -> FitReport:
    response = (
        get_client()
        .table("fit_reports")
        .insert(
            cast(
                Any,
                {
                    "user_id": user_id,
                    "job_description_id": job_description_id,
                    "fit_level": fit_level,
                    "matches": matches,
                    "gaps": gaps,
                    "terminology": terminology,
                    "reasoning": reasoning,
                },
            )
        )
        .execute()
    )
    return cast(FitReport, response.data[0])


def get_latest_fit_report(job_description_id: str, user_id: str) -> FitReport | None:
    response = (
        get_client()
        .table("fit_reports")
        .select("*")
        .eq("job_description_id", job_description_id)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    return cast(FitReport, response.data[0])


def get_fit_report_by_id(fit_report_id: str, user_id: str) -> FitReport | None:
    response = (
        get_client()
        .table("fit_reports")
        .select("*")
        .eq("id", fit_report_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    return cast(FitReport, response.data[0])


def list_fit_reports(job_description_id: str, user_id: str) -> list[FitReport]:
    response = (
        get_client()
        .table("fit_reports")
        .select("*")
        .eq("job_description_id", job_description_id)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [cast(FitReport, r) for r in response.data]
