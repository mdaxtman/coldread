"""Shared fixtures for integration tests — patches DB layer so no Supabase credentials needed."""

from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest

SAMPLE_JD = {
    "id": "00000000-0000-0000-0000-000000000020",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "title": None,
    "company": None,
    "content": "Test job description",
    "created_at": "2025-01-01T00:00:00+00:00",
}

SAMPLE_FIT_REPORT = {
    "id": "00000000-0000-0000-0000-000000000030",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "job_description_id": "00000000-0000-0000-0000-000000000020",
    "fit_level": "strong",
    "matches": [
        {
            "requirement": "Python backend development",
            "priority": "required",
            "notes": "FastAPI demonstrated",
        },
    ],
    "gaps": [],
    "terminology": [],
    "reasoning": "Strong match on core requirements.",
    "created_at": "2025-01-01T00:00:00+00:00",
}


@pytest.fixture(autouse=True)
def mock_db_layer() -> Generator[None, None, None]:
    """Patch DB lookups used by /jobs routes so tests don't need Supabase credentials.

    Returns valid data for the known sample IDs; None for all other IDs
    (which triggers the same 404 the real DB would return for unknown records).
    """

    def get_jd(jd_id: str, user_id: str) -> Any:
        return SAMPLE_JD if jd_id == SAMPLE_JD["id"] else None

    def get_fit_report(fit_report_id: str, user_id: str) -> Any:
        return SAMPLE_FIT_REPORT if fit_report_id == SAMPLE_FIT_REPORT["id"] else None

    with (
        patch("db.job_descriptions.get_jd", side_effect=get_jd),
        patch("db.fit_reports.get_fit_report_by_id", side_effect=get_fit_report),
    ):
        yield
