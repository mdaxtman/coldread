"""Data access layer for job descriptions."""

from typing import Any, cast

from config import DEFAULT_USER_ID
from db.client import get_client


def create_jd(content: str) -> dict[str, Any]:
    response = (
        get_client()
        .table("job_descriptions")
        .insert(
            {
                "user_id": DEFAULT_USER_ID,
                "content": content,
            }
        )
        .execute()
    )
    return cast(dict[str, Any], response.data[0])


def list_jds() -> list[dict[str, Any]]:
    response = (
        get_client()
        .table("job_descriptions")
        .select("*")
        .eq("user_id", DEFAULT_USER_ID)
        .order("created_at", desc=True)
        .execute()
    )
    return [cast(dict[str, Any], r) for r in response.data]


def get_jd(jd_id: str) -> dict[str, Any] | None:
    response = (
        get_client()
        .table("job_descriptions")
        .select("*")
        .eq("id", jd_id)
        .eq("user_id", DEFAULT_USER_ID)
        .execute()
    )
    if not response.data:
        return None
    return cast(dict[str, Any], response.data[0])
