"""Data access layer for fit reports."""

from typing import Any, cast

from db.client import get_client


def create_fit_report(
    job_description_id: str,
    user_id: str,
    fit_level: str,
    matches: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    terminology: list[dict[str, Any]],
    reasoning: str,
) -> dict[str, Any]:
    response = (
        get_client()
        .table("fit_reports")
        .insert(
            {
                "user_id": user_id,
                "job_description_id": job_description_id,
                "fit_level": fit_level,
                "matches": matches,
                "gaps": gaps,
                "terminology": terminology,
                "reasoning": reasoning,
            }
        )
        .execute()
    )
    return cast(dict[str, Any], response.data[0])


def get_latest_fit_report(job_description_id: str, user_id: str) -> dict[str, Any] | None:
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
    return cast(dict[str, Any], response.data[0])


def list_fit_reports(job_description_id: str, user_id: str) -> list[dict[str, Any]]:
    response = (
        get_client()
        .table("fit_reports")
        .select("*")
        .eq("job_description_id", job_description_id)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [cast(dict[str, Any], r) for r in response.data]
