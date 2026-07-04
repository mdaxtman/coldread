"""Data access layer for job descriptions."""

from typing import Any, cast

from db.client import get_client

_MAX_TITLE_LEN = 90


def derive_title(content: str) -> str | None:
    """Best-effort human label from the first meaningful line of a pasted JD.

    JDs arrive as unstructured paste; without this every run shows as
    "Untitled JD" across the UI. The heuristic: first non-empty line,
    markdown/bullet prefixes stripped, cut at the first sentence break,
    hard-capped at a label-sized length.
    """
    title = next(
        (stripped for line in content.splitlines() if (stripped := line.strip("#*_-• \t"))),
        None,
    )
    if title is None:
        return None
    for sep in (". ", " | "):
        if sep in title:
            title = title.split(sep, 1)[0]
    if len(title) > _MAX_TITLE_LEN:
        title = title[:_MAX_TITLE_LEN].rsplit(" ", 1)[0] + "…"
    return title


def create_jd(content: str, user_id: str) -> dict[str, Any]:
    response = (
        get_client()
        .table("job_descriptions")
        .insert(
            {
                "user_id": user_id,
                "content": content,
                "title": derive_title(content),
            }
        )
        .execute()
    )
    return cast(dict[str, Any], response.data[0])


def update_jd_title(jd_id: str, user_id: str, title: str) -> dict[str, Any] | None:
    response = (
        get_client()
        .table("job_descriptions")
        .update({"title": title})
        .eq("id", jd_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not response.data:
        return None
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
