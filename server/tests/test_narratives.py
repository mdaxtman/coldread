"""Tests for narrative endpoints (read-only)."""

from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

SAMPLE_NARRATIVE = {
    "id": "00000000-0000-0000-0000-000000000010",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "title": "Senior Engineer at Acme",
    "content": "I led the team...",
    "created_at": "2025-01-01T00:00:00+00:00",
    "updated_at": "2025-01-01T00:00:00+00:00",
}


@patch("db.narratives.list_narratives")
def test_list_narratives(mock_list: Any) -> None:
    mock_list.return_value = [SAMPLE_NARRATIVE]
    response = client.get("/narratives")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["userId"] == SAMPLE_NARRATIVE["user_id"]
    assert data[0]["createdAt"] is not None
    # Verify camelCase — no snake_case keys
    assert "user_id" not in data[0]
    assert "created_at" not in data[0]


@patch("db.narratives.list_narratives")
def test_list_narratives_empty(mock_list: Any) -> None:
    mock_list.return_value = []
    response = client.get("/narratives")
    assert response.status_code == 200
    assert response.json() == []
