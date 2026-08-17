"""Strip private content out of model-call payloads at the API boundary.

`call_model` records the full request envelope for observability, which is
genuinely useful locally — it is how the malformed tool call in #48 was
diagnosed. But that envelope contains the candidate narratives and the system
prompt, and the API has no authentication, so it must not cross the wire (#40).

Redaction happens here rather than at write time so the stored payload stays
complete for debugging. Shape is preserved — message count and roles survive,
`system` stays a string — because the run inspector type-checks these fields
before rendering, and a redacted-but-shaped payload keeps the observability view
working instead of silently emptying it.
"""

import json
from typing import Any

_LABEL = "[redacted]"


def _marker(value: Any) -> str:
    """Replace a value with a note of its size, so the inspector still shows scale."""
    if isinstance(value, str):
        size = len(value)
    else:
        try:
            size = len(json.dumps(value, default=str))
        except (TypeError, ValueError):
            return _LABEL
    return f"{_LABEL} — {size:,} chars"


def redact_request(request: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of a stored model-call request with private content removed.

    `messages` carries the narratives and the job description; `system` carries the
    prompt template. Everything else — model, token limits, thinking config, tool
    schema, tool choice — is structural and stays, because it is what makes the
    inspector worth having.
    """
    redacted = dict(request)

    if redacted.get("system") is not None:
        redacted["system"] = _marker(redacted["system"])

    if "messages" in redacted:
        messages = redacted["messages"]
        if isinstance(messages, list):
            redacted["messages"] = [
                {"role": m.get("role"), "content": _marker(m.get("content"))}
                if isinstance(m, dict)
                else {"role": None, "content": _marker(m)}
                for m in messages
            ]
        else:
            redacted["messages"] = []

    return redacted
