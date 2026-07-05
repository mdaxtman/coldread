"""Data access layer for prompts stored in DB."""

from typing import Any, cast

from db.client import get_client


def get_active_prompt(stage: str, user_id: str) -> dict[str, Any] | None:
    """Return the latest active prompt for a given pipeline stage, or None."""
    response = (
        get_client()
        .table("prompts")
        .select("*")
        .eq("user_id", user_id)
        .eq("stage", stage)
        .eq("active", True)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return cast(dict[str, Any], response.data[0])
    return None


def list_active_prompts(user_id: str) -> list[dict[str, Any]]:
    """Return all active prompts for a user, ordered by stage."""
    response = (
        get_client()
        .table("prompts")
        .select("id, stage, name, version, active, template")
        .eq("user_id", user_id)
        .eq("active", True)
        .order("stage")
        .execute()
    )
    return cast(list[dict[str, Any]], response.data)
