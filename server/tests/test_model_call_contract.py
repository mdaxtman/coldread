"""`ModelCallResponse` used to forward the raw Anthropic payload to the client.

`request: dict[str, Any]` and `response: list[Any]` were the only two `Any`
escapes in `models.py`; everything else in that file is precisely typed. The
untypedness propagated to `client/src/types.ts` as `Record<string, unknown>` and
`unknown[]`, which is why the run inspector re-derived the shape at render time
with hand-written guards.

#58 removed the acute leak with a denylist — strip `messages`, strip `system`,
forward the rest. A denylist fails open: any kwarg the SDK adds later ships by
default. These tests pin the opposite property. Anything the contract does not
name must not reach the client, whether or not anyone anticipated it.

`ContentBlockView.input` is deliberately still `dict[str, Any]`: a tool_use
block's input is the model's structured output and its shape varies per tool.
That is a genuinely dynamic value, not a missing contract.
"""

from typing import Any

from models import ModelCallResponse

NARRATIVE = "I built the entire looks shelf from scratch at Nordstrom." * 40
SYSTEM_PROMPT = "You are analyzing how well a candidate's background matches a job."

RAW_ROW: dict[str, Any] = {
    "id": "call-1",
    "stage": "fit",
    "seq": 1,
    "model": "claude-sonnet-5",
    "latency_ms": 2140,
    "tokens_in": 3318,
    "tokens_out": 1102,
    "stop_reason": "tool_use",
    "est_cost_usd": 0.041,
    "created_at": "2026-07-03T10:00:05+00:00",
    "request": {
        "model": "claude-sonnet-5",
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": NARRATIVE}],
        "tools": [{"name": "submit_fit_report", "input_schema": {"type": "object"}}],
        "tool_choice": {"type": "tool", "name": "submit_fit_report"},
        "some_future_sdk_field": "leaked-by-a-denylist",
    },
    "response": [
        {"type": "text", "text": "thinking out loud"},
        {"type": "tool_use", "id": "toolu_1", "name": "submit_fit_report", "input": {"fit": "x"}},
    ],
}


def _serialized() -> str:
    return ModelCallResponse.from_row(RAW_ROW).model_dump_json()


class TestFailsClosed:
    def test_a_field_the_contract_does_not_name_never_reaches_the_client(self) -> None:
        """The property a denylist cannot provide."""
        assert "leaked-by-a-denylist" not in _serialized()

    def test_narratives_never_reach_the_client(self) -> None:
        assert "looks shelf" not in _serialized()

    def test_the_system_prompt_never_reaches_the_client(self) -> None:
        assert "analyzing how well a candidate" not in _serialized()

    def test_tool_schemas_are_reduced_to_names(self) -> None:
        assert "input_schema" not in _serialized()


class TestInspectorStaysUsable:
    def test_request_keeps_model_and_message_shape(self) -> None:
        request = ModelCallResponse.from_row(RAW_ROW).request

        assert request.model == "claude-sonnet-5"
        assert len(request.messages) == 1
        assert request.messages[0].role == "user"
        assert "redacted" in request.messages[0].content
        assert request.system is not None and "redacted" in request.system
        assert request.tool_names == ["submit_fit_report"]

    def test_response_blocks_keep_what_the_inspector_renders(self) -> None:
        blocks = ModelCallResponse.from_row(RAW_ROW).response

        assert [b.type for b in blocks] == ["text", "tool_use"]
        assert blocks[0].text == "thinking out loud"
        assert blocks[1].name == "submit_fit_report"
        assert blocks[1].input == {"fit": "x"}

    def test_the_stored_row_is_not_mutated(self) -> None:
        ModelCallResponse.from_row(RAW_ROW)

        assert RAW_ROW["request"]["system"] == SYSTEM_PROMPT
        assert RAW_ROW["request"]["messages"][0]["content"] == NARRATIVE


class TestMalformedPayloads:
    def test_missing_request_and_response_are_safe(self) -> None:
        call = ModelCallResponse.from_row({**RAW_ROW, "request": {}, "response": []})

        assert call.request.messages == []
        assert call.response == []

    def test_non_list_messages_and_blocks_are_dropped(self) -> None:
        call = ModelCallResponse.from_row(
            {**RAW_ROW, "request": {"messages": "not-a-list"}, "response": "not-a-list"}
        )

        assert call.request.messages == []
        assert call.response == []
