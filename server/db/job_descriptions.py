"""Data access layer for job descriptions."""

from typing import Any, cast

from db.client import get_client


def create_jd(content: str, user_id: str) -> dict[str, Any]:
    response = (
        get_client()
        .table("job_descriptions")
        .insert(
            {
                "user_id": user_id,
                "content": content,
            }
        )
        .execute()
    )
    return cast(dict[str, Any], response.data[0])


def list_jds(user_id: str) -> list[dict[str, Any]]:
    response = (
        get_client()
        .table("job_descriptions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [cast(dict[str, Any], r) for r in response.data]


def get_jd(jd_id: str, user_id: str) -> dict[str, Any] | None:
    response = (
        get_client()
        .table("job_descriptions")
        .select("*")
        .eq("id", jd_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not response.data:
        return None
    return cast(dict[str, Any], response.data[0])
