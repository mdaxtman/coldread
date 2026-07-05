"""Fit schema/persistence carries scores + cultural signals (#31/#32)."""

from unittest.mock import MagicMock, patch

from db import fit_reports
from pipeline.fit_assessment import _FIT_REPORT_SCHEMA


def test_schema_requires_scores() -> None:
    assert "overall_score" in _FIT_REPORT_SCHEMA["required"]
    assert "semantic_score" in _FIT_REPORT_SCHEMA["required"]
    props = _FIT_REPORT_SCHEMA["properties"]
    assert "cultural_signals" in props
    assert "product_connection" in props


def test_create_fit_report_persists_signals() -> None:
    client = MagicMock()
    chain = client.table.return_value
    chain.insert.return_value = chain
    chain.execute.return_value = MagicMock(data=[{"id": "fr-1"}])
    with patch.object(fit_reports, "get_client", return_value=client):
        fit_reports.create_fit_report(
            job_description_id="jd-1",
            user_id="u-1",
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            reasoning="ok",
            overall_score=0.84,
            semantic_score=0.81,
            cultural_signals=[{"quality": "ownership", "jd_signal": "x", "evidence_hint": "y"}],
            product_connection="parallel",
        )
    inserted = chain.insert.call_args[0][0]
    assert inserted["overall_score"] == 0.84
    assert inserted["cultural_signals"][0]["quality"] == "ownership"
    assert inserted["product_connection"] == "parallel"
