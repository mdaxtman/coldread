"""Data access layer for resume variants."""

import json
from typing import Any, cast

from db.client import get_client


def _parse_screener_report(screener_report: Any) -> dict[str, Any]:
    """Ensure screener_report JSON nested fields are properly parsed.

    Supabase stores nested JSON structures as strings in some cases.
    This function ensures terminology_mismatches is always a list.
    """
    if not isinstance(screener_report, dict):
        return cast(dict[str, Any], screener_report)

    report = screener_report.copy()

    # Parse screener_analysis.terminology_mismatches if it's a string
    if "screener_analysis" in report and isinstance(report["screener_analysis"], dict):
        analysis = report["screener_analysis"].copy()
        if "terminology_mismatches" in analysis:
            mismatches = analysis["terminology_mismatches"]
            # Supabase returns this as a JSON string; parse it if needed
            if isinstance(mismatches, str):
                try:
                    analysis["terminology_mismatches"] = json.loads(mismatches)
                except json.JSONDecodeError:
                    # Corrupted data; default to empty list
                    analysis["terminology_mismatches"] = []
        report["screener_analysis"] = analysis

    return report


def create_resume_variant(
    job_description_id: str,
    user_id: str,
    content: str,
    version: int,
    screener_report: dict[str, Any],
    parent_variant_id: str | None = None,
    contact_info: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "user_id": user_id,
        "job_description_id": job_description_id,
        "content": content,
        "version": version,
        "screener_report": screener_report,
    }
    if parent_variant_id is not None:
        row["parent_variant_id"] = parent_variant_id
    if contact_info:
        row["contact_info"] = contact_info
    response = get_client().table("resume_variants").insert(row).execute()
    result = cast(dict[str, Any], response.data[0])
    if "screener_report" in result:
        result["screener_report"] = _parse_screener_report(result["screener_report"])
    return result


def get_latest_variant(job_description_id: str, user_id: str) -> dict[str, Any] | None:
    response = (
        get_client()
        .table("resume_variants")
        .select("*")
        .eq("job_description_id", job_description_id)
        .eq("user_id", user_id)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    row = cast(dict[str, Any], response.data[0])
    if "screener_report" in row:
        row["screener_report"] = _parse_screener_report(row["screener_report"])
    return row


def get_variant_by_id(variant_id: str, user_id: str) -> dict[str, Any] | None:
    response = (
        get_client()
        .table("resume_variants")
        .select("*")
        .eq("id", variant_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        return None
    row = cast(dict[str, Any], response.data[0])
    if "screener_report" in row:
        row["screener_report"] = _parse_screener_report(row["screener_report"])
    return row


def list_variants(job_description_id: str, user_id: str) -> list[dict[str, Any]]:
    response = (
        get_client()
        .table("resume_variants")
        .select("*")
        .eq("job_description_id", job_description_id)
        .eq("user_id", user_id)
        .order("version", desc=True)
        .execute()
    )
    result = []
    for r in response.data:
        row = cast(dict[str, Any], r)
        if "screener_report" in row:
            row["screener_report"] = _parse_screener_report(row["screener_report"])
        result.append(row)
    return result
