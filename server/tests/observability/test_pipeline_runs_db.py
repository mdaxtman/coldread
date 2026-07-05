"""Tests for the pipeline_runs data access layer (mocked Supabase client)."""

from unittest.mock import MagicMock, patch

from db import pipeline_runs
from observability.run_context import ModelCallRecord


def _mock_client(rows: list[dict[str, object]]) -> MagicMock:
    client = MagicMock()
    chain = client.table.return_value
    for method in ("insert", "update", "select", "eq", "order", "limit", "gte"):
        getattr(chain, method).return_value = chain
    chain.execute.return_value = MagicMock(data=rows)
    return client


def test_create_run_inserts_running_row() -> None:
    client = _mock_client([{"id": "run-1", "status": "running"}])
    with patch.object(pipeline_runs, "get_client", return_value=client):
        row = pipeline_runs.create_run("user-1", "jd-1", "fit")
    assert row["id"] == "run-1"
    inserted = client.table.return_value.insert.call_args[0][0]
    assert inserted["user_id"] == "user-1"
    assert inserted["kind"] == "fit"
    assert inserted["status"] == "running"


def test_add_model_call_serializes_record() -> None:
    client = _mock_client([{"id": "call-1"}])
    record = ModelCallRecord(
        stage="fit",
        seq=1,
        model="claude-sonnet-5",
        tokens_in=10,
        tokens_out=5,
        stop_reason="tool_use",
        latency_ms=42,
        est_cost_usd=0.0001,
        request={"model": "m"},
        response=[],
    )
    with patch.object(pipeline_runs, "get_client", return_value=client):
        pipeline_runs.add_model_call("run-1", "user-1", record)
    inserted = client.table.return_value.insert.call_args[0][0]
    assert inserted["run_id"] == "run-1"
    assert inserted["stage"] == "fit"
    assert inserted["tokens_in"] == 10
    assert inserted["request"] == {"model": "m"}


def test_usage_summary_sums_all_rows() -> None:
    client = _mock_client(
        [
            {"tokens_in": 100, "tokens_out": 50, "est_cost_usd": 0.01},
            {"tokens_in": 200, "tokens_out": 70, "est_cost_usd": 0.02},
        ]
    )
    with patch.object(pipeline_runs, "get_client", return_value=client):
        summary = pipeline_runs.usage_summary("user-1")
    assert summary == {
        "tokens_in": 300,
        "tokens_out": 120,
        "est_cost_usd": 0.03,
        "run_count": 2,
    }
