"""Run-scoped telemetry context.

A RunContext is set (via contextvar) for the duration of one pipeline run.
call_model() reports each Anthropic call here; the context accumulates
records, forwards them to an optional persistence callback, and emits
camelCase events onto a thread-safe queue for SSE streaming.

The contextvar is Python's equivalent of Node's AsyncLocalStorage: ambient
state visible to everything downstream without threading parameters through.
"""

import logging
import queue
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from observability.pricing import estimate_cost_usd

logger = logging.getLogger(__name__)


@dataclass
class ModelCallRecord:
    stage: str
    seq: int
    model: str
    tokens_in: int
    tokens_out: int
    stop_reason: str | None
    latency_ms: int
    est_cost_usd: float
    request: dict[str, Any]
    response: list[Any]


@dataclass
class RunContext:
    run_id: str
    jd_id: str
    kind: str
    user_id: str
    events: "queue.Queue[dict[str, Any] | None]"
    on_call: Callable[[ModelCallRecord], None] | None = None
    records: list[ModelCallRecord] = field(default_factory=list)
    _seq: int = 0

    def emit(self, event: str, data: dict[str, Any]) -> None:
        self.events.put({"event": event, "data": data})

    def begin_stage(self, stage: str) -> int:
        self._seq += 1
        self.emit("stage_started", {"stage": stage, "seq": self._seq})
        return self._seq

    def finish_call(
        self,
        seq: int,
        stage: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        stop_reason: str | None,
        latency_ms: int,
        request: dict[str, Any],
        response: list[Any],
        fallback_model: str | None = None,
    ) -> ModelCallRecord:
        record = ModelCallRecord(
            stage=stage,
            seq=seq,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            stop_reason=stop_reason,
            latency_ms=latency_ms,
            est_cost_usd=estimate_cost_usd(
                model, tokens_in, tokens_out, fallback_model=fallback_model
            ),
            request=request,
            response=response,
        )
        self.records.append(record)
        if self.on_call is not None:
            try:
                self.on_call(record)
            except Exception:
                logger.exception("model-call telemetry persistence failed")
        self.emit(
            "stage_finished",
            {
                "stage": stage,
                "seq": seq,
                "model": model,
                "tokensIn": tokens_in,
                "tokensOut": tokens_out,
                "latencyMs": latency_ms,
                "stopReason": stop_reason,
                "estCostUsd": record.est_cost_usd,
            },
        )
        return record

    def totals(self) -> dict[str, Any]:
        return {
            "tokensIn": sum(r.tokens_in for r in self.records),
            "tokensOut": sum(r.tokens_out for r in self.records),
            "estCostUsd": round(sum(r.est_cost_usd for r in self.records), 6),
            "callCount": len(self.records),
        }


current_run_context: ContextVar[RunContext | None] = ContextVar("current_run_context", default=None)
