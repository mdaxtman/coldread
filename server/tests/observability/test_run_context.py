"""Tests for RunContext event emission and record accumulation."""

import queue
from collections.abc import Callable
from typing import Any

from observability.run_context import ModelCallRecord, RunContext, current_run_context


def _make_ctx(
    on_call: Callable[[ModelCallRecord], None] | None = None,
) -> tuple[RunContext, "queue.Queue[dict[str, Any] | None]"]:
    events: queue.Queue[dict[str, Any] | None] = queue.Queue()
    ctx = RunContext(
        run_id="run-1",
        jd_id="jd-1",
        kind="fit",
        user_id="user-1",
        events=events,
        on_call=on_call,
    )
    return ctx, events


def test_begin_stage_emits_stage_started_with_incrementing_seq() -> None:
    ctx, events = _make_ctx()
    assert ctx.begin_stage("fit") == 1
    assert ctx.begin_stage("generate") == 2
    first = events.get_nowait()
    assert first == {"event": "stage_started", "data": {"stage": "fit", "seq": 1}}


def test_finish_call_records_costs_and_emits_stage_finished() -> None:
    seen: list[ModelCallRecord] = []
    ctx, events = _make_ctx(on_call=seen.append)
    seq = ctx.begin_stage("fit")
    events.get_nowait()  # discard stage_started
    record = ctx.finish_call(
        seq=seq,
        stage="fit",
        model="claude-sonnet-5",
        tokens_in=1000,
        tokens_out=500,
        stop_reason="tool_use",
        latency_ms=2140,
        request={"model": "claude-sonnet-5"},
        response=[{"type": "tool_use"}],
    )
    assert record.est_cost_usd == (1000 * 3.0 + 500 * 15.0) / 1_000_000
    assert seen == [record]
    assert ctx.records == [record]
    finished = events.get_nowait()
    assert finished is not None
    assert finished["event"] == "stage_finished"
    assert finished["data"]["stage"] == "fit"
    assert finished["data"]["tokensIn"] == 1000
    assert finished["data"]["tokensOut"] == 500
    assert finished["data"]["latencyMs"] == 2140
    assert finished["data"]["stopReason"] == "tool_use"
    assert finished["data"]["model"] == "claude-sonnet-5"


def test_totals_sums_records() -> None:
    ctx, _ = _make_ctx()
    s1 = ctx.begin_stage("fit")
    ctx.finish_call(s1, "fit", "claude-sonnet-5", 1000, 500, "tool_use", 100, {}, [])
    s2 = ctx.begin_stage("generate")
    ctx.finish_call(s2, "generate", "claude-sonnet-5", 2000, 700, "tool_use", 200, {}, [])
    totals = ctx.totals()
    assert totals["tokensIn"] == 3000
    assert totals["tokensOut"] == 1200
    assert totals["callCount"] == 2


def test_contextvar_defaults_to_none() -> None:
    assert current_run_context.get() is None
