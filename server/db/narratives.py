"""Data access layer for canonical narratives (read-only in ColdRead)."""

from typing import Any, cast

from config import DEFAULT_USER_ID
from db.client import get_client


def list_narratives() -> list[dict[str, Any]]:
    response = (
        get_client()
        .table("narratives")
        .select("*")
        .eq("user_id", DEFAULT_USER_ID)
        .order("created_at", desc=True)
        .execute()
    )
    return [cast(dict[str, Any], r) for r in response.data]
