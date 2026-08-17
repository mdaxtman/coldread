"""`GET /runs/{run_id}` serves the stored model-call envelope verbatim.

`anthropic_utils.call_model` records `request={k: v for k, v in kwargs.items()}`,
so a single call's `request` carries the whole prompt: `messages` holds the
candidate narratives (~80k chars of personal career history) and `system` holds
the prompt template that `CLAUDE.md` forbids committing. The API has no
authentication — `get_current_user_id` returns a constant — so on any public
deploy both are one unauthenticated GET away (#40).

Redacting at the API boundary rather than at write time is deliberate: the stored
envelope stays intact for local debugging, which is how the malformed tool call
in #48 was diagnosed. Only what crosses the wire is stripped.

Shape is preserved so the run inspector keeps working — the client type-checks
`system` as a string and `messages`/`tools` as arrays before rendering, so a
redacted payload still renders with counts and roles intact, just without bodies.
"""

from typing import Any

from api.redaction import redact_request

NARRATIVE = "I built the entire looks shelf from scratch at Nordstrom." * 40
SYSTEM_PROMPT = "You are analyzing how well a candidate's background matches a job."

REQUEST: dict[str, Any] = {
    "model": "claude-sonnet-5",
    "max_tokens": 4096,
    "thinking": {"type": "disabled"},
    "system": SYSTEM_PROMPT,
    "messages": [{"role": "user", "content": NARRATIVE}],
    "tools": [{"name": "submit_fit_report", "input_schema": {"type": "object"}}],
    "tool_choice": {"type": "tool", "name": "submit_fit_report"},
}


class TestRedactRequest:
    def test_narrative_content_never_survives(self) -> None:
        redacted = redact_request(REQUEST)

        assert "looks shelf" not in str(redacted)

    def test_system_prompt_never_survives(self) -> None:
        redacted = redact_request(REQUEST)

        assert "analyzing how well a candidate" not in str(redacted)

    def test_message_roles_and_count_are_preserved(self) -> None:
        redacted = redact_request(REQUEST)

        assert isinstance(redacted["messages"], list)
        assert len(redacted["messages"]) == 1
        assert redacted["messages"][0]["role"] == "user"

    def test_system_stays_a_string_so_the_inspector_still_renders_it(self) -> None:
        redacted = redact_request(REQUEST)

        assert isinstance(redacted["system"], str)
        assert "redacted" in redacted["system"]

    def test_non_sensitive_debugging_fields_are_untouched(self) -> None:
        redacted = redact_request(REQUEST)

        assert redacted["model"] == "claude-sonnet-5"
        assert redacted["max_tokens"] == 4096
        assert redacted["thinking"] == {"type": "disabled"}
        assert redacted["tool_choice"] == {"type": "tool", "name": "submit_fit_report"}
        assert redacted["tools"] == REQUEST["tools"]

    def test_the_stored_payload_is_not_mutated(self) -> None:
        redact_request(REQUEST)

        assert REQUEST["system"] == SYSTEM_PROMPT
        assert REQUEST["messages"][0]["content"] == NARRATIVE

    def test_missing_and_malformed_fields_are_safe(self) -> None:
        assert redact_request({}) == {}
        assert redact_request({"messages": "not-a-list"})["messages"] == []
        assert redact_request({"system": None})["system"] is None
