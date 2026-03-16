"""Data access layer for canonical narratives (read-only in ColdRead)."""

from typing import Any, cast

from db.client import get_client


def list_narratives(user_id: str) -> list[dict[str, Any]]:
    response = (
        get_client()
        .table("narratives")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [cast(dict[str, Any], r) for r in response.data]
