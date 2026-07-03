"""Integration tests for SSE streaming endpoints."""

import json
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from observability.run_context import current_run_context
from tests.integration.conftest import SAMPLE_JD

client = TestClient(app)

JD_ID = SAMPLE_JD["id"]


def _parse_sse(text: str) -> list[tuple[str, dict[str, Any]]]:
    events = []
    for block in text.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.splitlines() if ": " in line)
        events.append((lines["event"], json.loads(lines["data"])))
    return events


def _fake_fit_workflow(jd_id: str, user_id: str) -> dict[str, Any]:
    ctx = current_run_context.get()
    assert ctx is not None, "workflow must run inside a RunContext"
    seq = ctx.begin_stage("fit")
    ctx.finish_call(seq, "fit", "claude-sonnet-4-20250514", 1000, 400, "tool_use", 50, {}, [])
    return {"id": "fit-report-1"}


def test_fit_stream_happy_path() -> None:
    with (
        patch("api.streaming.fit_assessment.run_fit_assessment_workflow", _fake_fit_workflow),
        patch("api.streaming.pipeline_runs.create_run", return_value={"id": "run-1"}),
        patch("api.streaming.pipeline_runs.finish_run") as finish,
        patch("api.streaming.pipeline_runs.add_model_call"),
    ):
        resp = client.post(f"/jds/{JD_ID}/fit/stream")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse(resp.text)
    names = [e[0] for e in events]
    assert names == ["run_started", "stage_started", "stage_finished", "run_completed"]
    completed = events[-1][1]
    assert completed["resultId"] == "fit-report-1"
    assert completed["tokensIn"] == 1000
    assert finish.call_args.kwargs["status"] == "completed"


def test_fit_stream_failure_emits_run_failed() -> None:
    def boom(jd_id: str, user_id: str) -> dict[str, Any]:
        raise RuntimeError("fit_assessment_failed: model exploded")

    with (
        patch("api.streaming.fit_assessment.run_fit_assessment_workflow", boom),
        patch("api.streaming.pipeline_runs.create_run", return_value={"id": "run-1"}),
        patch("api.streaming.pipeline_runs.finish_run") as finish,
    ):
        resp = client.post(f"/jds/{JD_ID}/fit/stream")
    events = _parse_sse(resp.text)
    assert events[-1][0] == "run_failed"
    assert "model exploded" in events[-1][1]["error"]
    assert finish.call_args.kwargs["status"] == "failed"


def test_fit_stream_unknown_jd_404s_before_stream_opens() -> None:
    resp = client.post("/jds/nonexistent-jd-id/fit/stream")
    assert resp.status_code == 404
