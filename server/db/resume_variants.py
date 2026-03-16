"""Data access layer for resume variants."""

from typing import Any, cast

from db.client import get_client


def create_resume_variant(
    job_description_id: str,
    user_id: str,
    content: str,
    version: int,
    screener_report: dict[str, Any],
    parent_variant_id: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "user_id": user_id,
        "job_description_id": job_description_id,
        "content": content,
        "version": version,
        "screener_report": screener_report,
    }
    if parent_variant_id is not None:
        row["parent_variant_id"] = parent_variant_id
    response = get_client().table("resume_variants").insert(row).execute()
    return cast(dict[str, Any], response.data[0])


def get_latest_variant(job_description_id: str, user_id: str) -> dict[str, Any] | None:
    response = (
        get_client()
        .table("resume_variants")
        .select("*")
        .eq("job_description_id", job_description_id)
        .eq("user_id", user_id)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    return cast(dict[str, Any], response.data[0])


def list_variants(job_description_id: str, user_id: str) -> list[dict[str, Any]]:
    response = (
        get_client()
        .table("resume_variants")
        .select("*")
        .eq("job_description_id", job_description_id)
        .eq("user_id", user_id)
        .order("version", desc=True)
        .execute()
    )
    return [cast(dict[str, Any], r) for r in response.data]
