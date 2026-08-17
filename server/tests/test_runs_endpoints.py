"""Tests for runs/prompts/usage read endpoints."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

_RUN_ROW = {
    "id": "run-1",
    "user_id": "u",
    "job_description_id": "jd-1",
    "kind": "fit",
    "status": "completed",
    "error": None,
    "started_at": "2026-07-03T10:00:00+00:00",
    "finished_at": "2026-07-03T10:00:07+00:00",
    "duration_ms": 6780,
    "tokens_in": 3318,
    "tokens_out": 1102,
    "est_cost_usd": 0.041,
    "job_descriptions": {"title": "Staff FE", "company": "Foundry"},
}

_CALL_ROW = {
    "id": "call-1",
    "user_id": "u",
    "run_id": "run-1",
    "stage": "fit",
    "seq": 1,
    "model": "claude-sonnet-5",
    "latency_ms": 2140,
    "tokens_in": 3318,
    "tokens_out": 1102,
    "stop_reason": "tool_use",
    "est_cost_usd": 0.041,
    "request": {"model": "claude-sonnet-5"},
    "response": [],
    "created_at": "2026-07-03T10:00:05+00:00",
}


def test_list_runs_flattens_jd() -> None:
    with patch("api.routes.pipeline_runs.list_runs", return_value=[_RUN_ROW]):
        resp = client.get("/runs")
    assert resp.status_code == 200
    body = resp.json()[0]
    assert body["jdTitle"] == "Staff FE"
    assert body["kind"] == "fit"
    assert body["estCostUsd"] == 0.041


def test_get_run_detail() -> None:
    with (
        patch("api.routes.pipeline_runs.get_run", return_value=_RUN_ROW),
        patch("api.routes.pipeline_runs.list_calls", return_value=[_CALL_ROW]),
    ):
        resp = client.get("/runs/run-1")
    assert resp.status_code == 200
    assert resp.json()["calls"][0]["stage"] == "fit"


def test_get_run_404() -> None:
    with patch("api.routes.pipeline_runs.get_run", return_value=None):
        assert client.get("/runs/nope").status_code == 404


def test_usage_summary() -> None:
    with patch(
        "api.routes.pipeline_runs.usage_summary",
        return_value={"tokens_in": 10, "tokens_out": 5, "est_cost_usd": 0.001, "run_count": 2},
    ):
        resp = client.get("/usage/summary")
    assert resp.json() == {
        "tokensIn": 10,
        "tokensOut": 5,
        "estCostUsd": 0.001,
        "runCount": 2,
    }


_SENSITIVE_CALL_ROW = {
    **_CALL_ROW,
    "request": {
        "model": "claude-sonnet-5",
        "system": "You are analyzing how well a candidate's background matches a job.",
        "messages": [{"role": "user", "content": "I built the entire looks shelf at Nordstrom."}],
        "tools": [{"name": "submit_fit_report"}],
    },
}


def test_get_run_detail_redacts_narratives_and_system_prompt() -> None:
    """The API is unauthenticated, so the stored prompt envelope must not ship (#40)."""
    with (
        patch("api.routes.pipeline_runs.get_run", return_value=_RUN_ROW),
        patch("api.routes.pipeline_runs.list_calls", return_value=[_SENSITIVE_CALL_ROW]),
    ):
        resp = client.get("/runs/run-1")

    assert resp.status_code == 200
    body = resp.text
    assert "looks shelf" not in body
    assert "analyzing how well a candidate" not in body


def test_get_run_detail_keeps_the_inspector_usable() -> None:
    """Redaction preserves shape — the client renders counts, roles and tool schema."""
    with (
        patch("api.routes.pipeline_runs.get_run", return_value=_RUN_ROW),
        patch("api.routes.pipeline_runs.list_calls", return_value=[_SENSITIVE_CALL_ROW]),
    ):
        request = client.get("/runs/run-1").json()["calls"][0]["request"]

    assert isinstance(request["system"], str)
    assert len(request["messages"]) == 1
    assert request["messages"][0]["role"] == "user"
    assert request["model"] == "claude-sonnet-5"
    assert request["tools"] == [{"name": "submit_fit_report"}]
