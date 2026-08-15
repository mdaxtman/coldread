"""Data access layer for job descriptions."""

import re
from typing import Any, cast

from db.client import get_client

_MAX_TITLE_LEN = 90

_FRONTMATTER_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$")
_KNOWN_FRONTMATTER_KEYS = frozenset(
    {
        "title",
        "source",
        "author",
        "published",
        "created",
        "description",
        "tags",
        "date",
        "slug",
        "layout",
        "categories",
    }
)


def derive_title(content: str) -> str | None:
    """Best-effort human label from the first meaningful line of a pasted JD.

    JDs arrive as unstructured paste; without this every run shows as
    "Untitled JD" across the UI. A clipper's frontmatter `title:` is used when
    present — otherwise the heuristic is: first non-empty line of the body,
    markdown/bullet prefixes stripped, cut at the first sentence break,
    hard-capped at a label-sized length.
    """
    body, metadata = strip_frontmatter(content)

    title = metadata.get("title")
    if title is None:
        title = next(
            (stripped for line in body.splitlines() if (stripped := line.strip("#*_-• \t"))),
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
    # Persist the body, not the clipper's frontmatter: it is not job-description
    # prose, and leaving it in front of the JD destabilises the fit stage's
    # tool-call serialisation badly enough to fail the run outright (#48).
    body, _ = strip_frontmatter(content)
    response = (
        get_client()
        .table("job_descriptions")
        .insert(
            {
                "user_id": user_id,
                "content": body,
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


def strip_frontmatter(content: str) -> tuple[str, dict[str, str]]:
    """Split clipper YAML frontmatter off a pasted JD.

    Returns `(body, metadata)`. When no frontmatter is recognised the content is
    returned untouched with an empty dict — over-stripping silently deletes real
    job requirements, so every ambiguous case resolves to "leave it alone".

    Two shapes occur in practice. The fenced form opens with `---` and is
    unambiguous. The unfenced form is the same block with its opening delimiter
    lost on copy, which is what the browser clipper actually produces once the
    text has been through an editor; recognising it needs a stricter rule, so it
    additionally requires at least one known frontmatter key. That keeps a
    markdown horizontal rule further down the document from being mistaken for a
    terminator, and keeps prose that merely opens `Responsibilities:` intact.
    """
    if not content.strip():
        return content, {}

    lines = content.split("\n")
    fenced = lines[0].strip() == "---"
    metadata: dict[str, str] = {}
    saw_known_key = False
    index = 1 if fenced else 0

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped == "---":
            break
        if not stripped:
            if not fenced:
                return content, {}
            index += 1
            continue
        if line[:1] in (" ", "\t", "-"):  # list item or wrapped value
            index += 1
            continue

        match = _FRONTMATTER_KEY.match(line)
        if match is None:
            return content, {}

        key, value = match.group(1).lower(), match.group(2).strip()
        saw_known_key = saw_known_key or key in _KNOWN_FRONTMATTER_KEYS
        if value:
            metadata[key] = value.strip("\"'")
        index += 1
    else:
        return content, {}  # ran off the end without a terminator

    if not fenced and not (saw_known_key and metadata):
        return content, {}

    return "\n".join(lines[index + 1 :]).lstrip("\n"), metadata
