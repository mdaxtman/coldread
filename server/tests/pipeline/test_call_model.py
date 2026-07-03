"""Tests for the instrumented call_model chokepoint."""

import queue
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from observability.run_context import RunContext, current_run_context
from pipeline import anthropic_utils
from pipeline.anthropic_utils import call_model


def _fake_response() -> SimpleNamespace:
    tool_block = SimpleNamespace(type="tool_use", input={"fit_level": "strong"})
    tool_block.model_dump = lambda: {"type": "tool_use", "input": {"fit_level": "strong"}}
    return SimpleNamespace(
        content=[tool_block],
        model="claude-sonnet-5",
        stop_reason="tool_use",
        usage=SimpleNamespace(input_tokens=1200, output_tokens=340),
    )


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    client = MagicMock()
    client.messages.create.return_value = _fake_response()
    monkeypatch.setattr(anthropic_utils, "_get_anthropic_client", lambda: client)
    return client


def test_returns_tool_input_without_context(fake_client: MagicMock) -> None:
    result = call_model("fit", model="claude-sonnet-5", max_tokens=10, messages=[])
    assert result == {"fit_level": "strong"}
    fake_client.messages.create.assert_called_once()


def test_records_telemetry_with_active_context(fake_client: MagicMock) -> None:
    events: queue.Queue[dict[str, Any] | None] = queue.Queue()
    ctx = RunContext(run_id="r", jd_id="j", kind="fit", user_id="u", events=events)
    token = current_run_context.set(ctx)
    try:
        call_model(
            "fit",
            model="claude-sonnet-5",
            max_tokens=4096,
            system="be honest",
            messages=[{"role": "user", "content": "hi"}],
        )
    finally:
        current_run_context.reset(token)

    assert len(ctx.records) == 1
    rec = ctx.records[0]
    assert rec.stage == "fit"
    assert rec.tokens_in == 1200
    assert rec.tokens_out == 340
    assert rec.stop_reason == "tool_use"
    assert rec.latency_ms >= 0
    assert rec.request["system"] == "be honest"
    assert rec.request["model"] == "claude-sonnet-5"
    assert rec.response == [{"type": "tool_use", "input": {"fit_level": "strong"}}]
    started = events.get_nowait()
    assert started is not None
    assert started["event"] == "stage_started"
    finished = events.get_nowait()
    assert finished is not None
    assert finished["event"] == "stage_finished"


def test_raises_when_no_tool_block(fake_client: MagicMock) -> None:
    fake_client.messages.create.return_value = SimpleNamespace(
        content=[],
        model="m",
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=1, output_tokens=1),
    )
    with pytest.raises(RuntimeError):
        call_model("fit", model="m", max_tokens=10, messages=[])


def test_thinking_defaults_to_disabled(fake_client: MagicMock) -> None:
    call_model("fit", model="claude-sonnet-5", max_tokens=10, messages=[])
    call_kwargs = fake_client.messages.create.call_args.kwargs
    assert call_kwargs["thinking"] == {"type": "disabled"}


def test_cost_falls_back_to_requested_model_when_response_model_unpriced(
    fake_client: MagicMock,
) -> None:
    # The API can echo a dated snapshot id back that isn't in PRICING yet;
    # the requested model id should still be used to estimate cost rather
    # than silently recording $0.
    fake_client.messages.create.return_value = SimpleNamespace(
        content=[
            SimpleNamespace(
                type="tool_use",
                input={"fit_level": "strong"},
                model_dump=lambda: {"type": "tool_use"},
            )
        ],
        model="claude-sonnet-5-20260315",
        stop_reason="tool_use",
        usage=SimpleNamespace(input_tokens=1_000_000, output_tokens=1_000_000),
    )
    events: queue.Queue[dict[str, Any] | None] = queue.Queue()
    ctx = RunContext(run_id="r", jd_id="j", kind="fit", user_id="u", events=events)
    token = current_run_context.set(ctx)
    try:
        call_model("fit", model="claude-sonnet-5", max_tokens=10, messages=[])
    finally:
        current_run_context.reset(token)

    rec = ctx.records[0]
    assert rec.model == "claude-sonnet-5-20260315"
    assert rec.est_cost_usd == 18.0


def test_explicit_thinking_is_not_overwritten(fake_client: MagicMock) -> None:
    call_model(
        "fit",
        model="claude-sonnet-5",
        max_tokens=10,
        messages=[],
        thinking={"type": "adaptive"},
    )
    call_kwargs = fake_client.messages.create.call_args.kwargs
    assert call_kwargs["thinking"] == {"type": "adaptive"}
