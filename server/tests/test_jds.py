"""Tests for job description endpoints and pipeline result lookups."""

from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

SAMPLE_JD = {
    "id": "00000000-0000-0000-0000-000000000020",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "title": None,
    "company": None,
    "content": "We are looking for a senior backend engineer...",
    "created_at": "2025-01-01T00:00:00+00:00",
}

SAMPLE_FIT_REPORT = {
    "id": "00000000-0000-0000-0000-000000000030",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "job_description_id": "00000000-0000-0000-0000-000000000020",
    "fit_level": "strong",
    "matches": ["Python", "FastAPI", "PostgreSQL"],
    "gaps": [{"requirement": "Kubernetes", "type": "soft", "notes": "Some exposure"}],
    "terminology": [{"my_term": "CI/CD", "jd_term": "DevOps"}],
    "reasoning": "Strong match on core requirements.",
    "created_at": "2025-01-01T00:00:00+00:00",
}

SAMPLE_RESUME_VARIANT = {
    "id": "00000000-0000-0000-0000-000000000040",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "job_description_id": "00000000-0000-0000-0000-000000000020",
    "content": "# Resume\nSenior Backend Engineer...",
    "version": 1,
    "parent_variant_id": None,
    "screener_report": {
        "keyword_coverage": {"python": True, "kubernetes": False},
        "semantic_score": 0.82,
        "terminology_mismatches": [{"my_term": "CI/CD", "jd_term": "DevOps"}],
        "overall_score": 0.78,
    },
    "created_at": "2025-01-01T00:00:00+00:00",
}

JD_ID = SAMPLE_JD["id"]


# ---------------------------------------------------------------------------
# POST /jds
# ---------------------------------------------------------------------------


@patch("db.job_descriptions.create_jd")
def test_create_jd(mock_create: Any) -> None:
    mock_create.return_value = SAMPLE_JD
    response = client.post(
        "/jds",
        json={"content": "..."},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == SAMPLE_JD["id"]
    assert data["userId"] == SAMPLE_JD["user_id"]
    assert data["company"] is None
    # Verify camelCase serialization
    assert "user_id" not in data
    assert "created_at" not in data


# ---------------------------------------------------------------------------
# GET /jds
# ---------------------------------------------------------------------------


@patch("db.job_descriptions.list_jds")
def test_list_jds(mock_list: Any) -> None:
    mock_list.return_value = [SAMPLE_JD]
    response = client.get("/jds")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] is None


@patch("db.job_descriptions.list_jds")
def test_list_jds_empty(mock_list: Any) -> None:
    mock_list.return_value = []
    response = client.get("/jds")
    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /jds/{jd_id}/fit
# ---------------------------------------------------------------------------


@patch("db.fit_reports.get_latest_fit_report")
def test_get_fit_report(mock_get: Any) -> None:
    mock_get.return_value = SAMPLE_FIT_REPORT
    response = client.get(f"/jds/{JD_ID}/fit")
    assert response.status_code == 200
    data = response.json()
    assert data["fitLevel"] == "strong"
    assert len(data["matches"]) == 3
    assert data["gaps"][0]["requirement"] == "Kubernetes"
    assert data["terminology"][0]["myTerm"] == "CI/CD"


@patch("db.fit_reports.get_latest_fit_report")
def test_get_fit_report_not_found(mock_get: Any) -> None:
    mock_get.return_value = None
    response = client.get(f"/jds/{JD_ID}/fit")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /jds/{jd_id}/resume
# ---------------------------------------------------------------------------


@patch("db.resume_variants.get_latest_variant")
def test_get_latest_resume(mock_get: Any) -> None:
    mock_get.return_value = SAMPLE_RESUME_VARIANT
    response = client.get(f"/jds/{JD_ID}/resume")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1
    assert data["parentVariantId"] is None
    assert data["screenerReport"]["semanticScore"] == 0.82


@patch("db.resume_variants.get_latest_variant")
def test_get_latest_resume_not_found(mock_get: Any) -> None:
    mock_get.return_value = None
    response = client.get(f"/jds/{JD_ID}/resume")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /jds/{jd_id}/resume/variants
# ---------------------------------------------------------------------------


@patch("db.resume_variants.list_variants")
def test_list_resume_variants(mock_list: Any) -> None:
    mock_list.return_value = [SAMPLE_RESUME_VARIANT]
    response = client.get(f"/jds/{JD_ID}/resume/variants")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["screenerReport"]["overallScore"] == 0.78


@patch("db.resume_variants.list_variants")
def test_list_resume_variants_empty(mock_list: Any) -> None:
    mock_list.return_value = []
    response = client.get(f"/jds/{JD_ID}/resume/variants")
    assert response.status_code == 200
    assert response.json() == []
