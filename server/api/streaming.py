"""SSE streaming endpoints — run a pipeline in a worker thread and narrate it.

Transport seam for the future job queue (#18-27): today the pipeline runs
in-request; later a worker sets the same RunContext and these routes become
subscribe-by-run-id. Events cross the sync-pipeline/async-generator boundary
via a stdlib thread-safe queue drained with run_in_executor.

Note on JD-ownership checks: `api.routes` defines `_verify_jd_ownership` but
this module is imported from the bottom of `api.routes` (to register
`streaming_router`), so importing that helper back from `api.routes` would
depend on `api.routes` having already executed past its definition — fragile
if routes.py is ever reordered. Instead we duplicate the (small) ownership
check here against `db.job_descriptions` directly, keeping the import graph
one-directional: `api.routes` -> `api.streaming`.
"""

import asyncio
import json
import queue
import time
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.dependencies import get_current_user_id
from db import fit_reports, job_descriptions, pipeline_runs
from features import fit_assessment, resume_generation
from models import GenerateResumeRequest
from observability.run_context import ModelCallRecord, RunContext, current_run_context

streaming_router = APIRouter(prefix="/jds", tags=["streaming"])


def _verify_jd_ownership(jd_id: str, user_id: str) -> None:
    """Raise 404 if the JD does not exist or does not belong to the user.

    Mirrors `api.routes._verify_jd_ownership` — duplicated locally to avoid
    a circular import (see module docstring). Ensures a bogus JD id 404s
    before the SSE stream opens, rather than surfacing as a `run_failed`
    event after a 200.
    """
    try:
        jd = job_descriptions.get_jd(jd_id, user_id)
        if jd is None:
            raise HTTPException(status_code=404, detail="Job description not found")
    except HTTPException:
        raise
    except Exception as e:
        if "invalid input syntax" in str(e) or "uuid" in str(e).lower():
            raise HTTPException(status_code=404, detail="Job description not found")
        raise


def sse_line(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def stream_pipeline_run(
    kind: str, jd_id: str, user_id: str, work: Callable[[], dict[str, Any]]
) -> StreamingResponse:
    events: queue.Queue[dict[str, Any] | None] = queue.Queue()
    run_row = pipeline_runs.create_run(user_id, jd_id, kind)
    run_id = run_row["id"]

    def _on_call(record: ModelCallRecord) -> None:
        pipeline_runs.add_model_call(run_id, user_id, record)

    ctx = RunContext(
        run_id=run_id,
        jd_id=jd_id,
        kind=kind,
        user_id=user_id,
        events=events,
        on_call=_on_call,
    )

    def work_in_thread() -> None:
        token = current_run_context.set(ctx)
        start = time.perf_counter()
        try:
            result = work()
            totals = ctx.totals()
            duration_ms = int((time.perf_counter() - start) * 1000)
            pipeline_runs.finish_run(
                run_id,
                user_id,
                status="completed",
                duration_ms=duration_ms,
                tokens_in=totals["tokensIn"],
                tokens_out=totals["tokensOut"],
                est_cost_usd=totals["estCostUsd"],
            )
            events.put(
                {
                    "event": "run_completed",
                    "data": {"resultId": result["id"], "durationMs": duration_ms, **totals},
                }
            )
        except Exception as e:  # noqa: BLE001 — boundary: convert to run_failed
            totals = ctx.totals()
            duration_ms = int((time.perf_counter() - start) * 1000)
            pipeline_runs.finish_run(
                run_id,
                user_id,
                status="failed",
                duration_ms=duration_ms,
                tokens_in=totals["tokensIn"],
                tokens_out=totals["tokensOut"],
                est_cost_usd=totals["estCostUsd"],
                error=str(e),
            )
            events.put({"event": "run_failed", "data": {"error": str(e), **totals}})
        finally:
            current_run_context.reset(token)
            events.put(None)  # sentinel: stream is done

    async def generate() -> Any:
        yield sse_line("run_started", {"runId": run_id, "kind": kind, "jdId": jd_id})
        loop = asyncio.get_running_loop()
        worker = loop.run_in_executor(None, work_in_thread)
        while True:
            item = await loop.run_in_executor(None, events.get)
            if item is None:
                break
            yield sse_line(item["event"], item["data"])
        await worker

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@streaming_router.post("/{jd_id}/fit/stream")
def stream_fit(jd_id: str, user_id: str = Depends(get_current_user_id)) -> StreamingResponse:
    _verify_jd_ownership(jd_id, user_id)
    return stream_pipeline_run(
        "fit",
        jd_id,
        user_id,
        lambda: dict(fit_assessment.run_fit_assessment_workflow(jd_id, user_id)),
    )


@streaming_router.post("/{jd_id}/resume/stream")
def stream_generate(
    jd_id: str,
    body: GenerateResumeRequest,
    user_id: str = Depends(get_current_user_id),
) -> StreamingResponse:
    _verify_jd_ownership(jd_id, user_id)
    fit_report = fit_reports.get_fit_report_by_id(body.fit_report_id, user_id)

    def work() -> dict[str, Any]:
        if fit_report is None:
            raise ValueError(f"Fit report not found: {body.fit_report_id}")
        return resume_generation.run_resume_generation(
            jd_id, user_id, dict(fit_report), mode="full"
        )

    return stream_pipeline_run("generate", jd_id, user_id, work)


@streaming_router.post("/{jd_id}/resume/refine/{variant_id}/stream")
def stream_refine(
    jd_id: str,
    variant_id: str,
    body: GenerateResumeRequest,
    user_id: str = Depends(get_current_user_id),
) -> StreamingResponse:
    _verify_jd_ownership(jd_id, user_id)
    fit_report = fit_reports.get_fit_report_by_id(body.fit_report_id, user_id)

    def work() -> dict[str, Any]:
        if fit_report is None:
            raise ValueError(f"Fit report not found: {body.fit_report_id}")
        return resume_generation.run_resume_generation(
            jd_id, user_id, dict(fit_report), mode="refine", parent_variant_id=variant_id
        )

    return stream_pipeline_run("refine", jd_id, user_id, work)
