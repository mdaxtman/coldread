"""Data access layer for pipeline runs and model calls."""

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any, cast

from db.client import get_client
from observability.run_context import ModelCallRecord


def create_run(user_id: str, job_description_id: str, kind: str) -> dict[str, Any]:
    response = (
        get_client()
        .table("pipeline_runs")
        .insert(
            {
                "user_id": user_id,
                "job_description_id": job_description_id,
                "kind": kind,
                "status": "running",
            }
        )
        .execute()
    )
    return cast(dict[str, Any], response.data[0])


def finish_run(
    run_id: str,
    user_id: str,
    status: str,
    duration_ms: int,
    tokens_in: int,
    tokens_out: int,
    est_cost_usd: float,
    error: str | None = None,
) -> dict[str, Any]:
    response = (
        get_client()
        .table("pipeline_runs")
        .update(
            {
                "status": status,
                "error": error,
                "finished_at": datetime.now(UTC).isoformat(),
                "duration_ms": duration_ms,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "est_cost_usd": est_cost_usd,
            }
        )
        .eq("id", run_id)
        .eq("user_id", user_id)
        .execute()
    )
    return cast(dict[str, Any], response.data[0])


def add_model_call(run_id: str, user_id: str, record: ModelCallRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload.update({"run_id": run_id, "user_id": user_id})
    response = get_client().table("model_calls").insert(payload).execute()
    return cast(dict[str, Any], response.data[0])


def list_runs(user_id: str, limit: int = 50) -> list[dict[str, Any]]:
    response = (
        get_client()
        .table("pipeline_runs")
        .select("*, job_descriptions(title, company)")
        .eq("user_id", user_id)
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return cast(list[dict[str, Any]], response.data)


def get_run(run_id: str, user_id: str) -> dict[str, Any] | None:
    response = (
        get_client()
        .table("pipeline_runs")
        .select("*, job_descriptions(title, company)")
        .eq("id", run_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return cast(dict[str, Any], response.data[0]) if response.data else None


def list_calls(run_id: str, user_id: str) -> list[dict[str, Any]]:
    response = (
        get_client()
        .table("model_calls")
        .select("*")
        .eq("run_id", run_id)
        .eq("user_id", user_id)
        .order("seq")
        .execute()
    )
    return cast(list[dict[str, Any]], response.data)


def month_summary(user_id: str) -> dict[str, Any]:
    month_start = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    response = (
        get_client()
        .table("pipeline_runs")
        .select("tokens_in, tokens_out, est_cost_usd")
        .eq("user_id", user_id)
        .gte("started_at", month_start.isoformat())
        .execute()
    )
    rows: list[dict[str, Any]] = cast(list[dict[str, Any]], response.data or [])
    return {
        "tokens_in": sum(cast(int, r["tokens_in"]) or 0 for r in rows),
        "tokens_out": sum(cast(int, r["tokens_out"]) or 0 for r in rows),
        "est_cost_usd": round(sum(float(cast(float, r["est_cost_usd"]) or 0) for r in rows), 6),
        "run_count": len(rows),
    }
