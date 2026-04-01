"""Tests for resume generation pipeline."""

from typing import Any
from unittest.mock import patch

import pytest

from features import resume_generation


@pytest.fixture
def mock_jd() -> dict[str, Any]:
    """Mock job description."""
    return {
        "id": "jd-123",
        "user_id": "user-1",
        "content": "Senior Engineer required. 5+ years React. Experience with TypeScript.",
        "created_at": "2026-03-01T00:00:00",
    }


@pytest.fixture
def mock_narratives() -> list[dict[str, Any]]:
    """Mock narratives list."""
    return [
        {
            "id": "narr-1",
            "user_id": "user-1",
            "category": "career_overview",
            "title": "Career Overview",
            "content": "10 years frontend engineering experience...",
            "created_at": "2026-03-01T00:00:00",
        },
        {
            "id": "narr-2",
            "user_id": "user-1",
            "category": "role",
            "title": "Senior Engineer at TechCorp",
            "content": "Led React team, built TypeScript applications...",
            "created_at": "2026-03-01T00:00:00",
        },
    ]


@pytest.fixture
def mock_fit_report() -> dict[str, Any]:
    """Mock fit assessment report."""
    return {
        "id": "fit-123",
        "user_id": "user-1",
        "job_description_id": "jd-123",
        "fit_level": "strong",
        "matches": [
            {
                "requirement": "5+ years React",
                "priority": "required",
                "notes": "11 years experience",
            },
            {"requirement": "TypeScript", "priority": "required", "notes": "Strong expertise"},
        ],
        "gaps": [],
        "terminology": [],
        "reasoning": "Strong fit for the role",
        "created_at": "2026-03-28T00:00:00",
    }


@pytest.fixture
def mock_resume_variant() -> dict[str, Any]:
    """Mock resume variant from database."""
    return {
        "id": "variant-1",
        "user_id": "user-1",
        "job_description_id": "jd-123",
        "content": "Generated resume text...",
        "version": 1,
        "parent_variant_id": None,
        "screener_report": {
            "screener_analysis": {
                "keyword_coverage": {"React": True, "TypeScript": True},
                "semantic_score": 0.85,
                "terminology_mismatches": [],
                "overall_score": 0.85,
            },
            "refinement_changes": {
                "sections_modified": [],
                "changes": [],
                "remaining_gaps": [],
                "coverage_improvement": 0,
            },
        },
        "created_at": "2026-03-28T00:00:00",
    }


# ---------------------------------------------------------------------------
# Test: Full regenerate mode success
# ---------------------------------------------------------------------------


def test_full_regenerate_success(
    mock_jd: dict[str, Any],
    mock_narratives: list[dict[str, Any]],
    mock_fit_report: dict[str, Any],
    mock_resume_variant: dict[str, Any],
) -> None:
    """Test full regenerate mode with all three steps succeeding."""
    with patch("features.resume_generation.job_descriptions.get_jd", return_value=mock_jd):
        with patch(
            "features.resume_generation.narratives.list_narratives", return_value=mock_narratives
        ):
            with patch(
                "features.resume_generation.resume_variants.get_latest_variant", return_value=None
            ):
                with patch("features.resume_generation.run_generator") as mock_gen:
                    with patch("features.resume_generation.run_screener") as mock_scr:
                        with patch("features.resume_generation.run_refinement") as mock_ref:
                            with patch(
                                "features.resume_generation.resume_variants.create_resume_variant",
                                return_value=mock_resume_variant,
                            ) as mock_create:
                                # Setup mock returns
                                mock_gen.return_value = {
                                    "summary": "Senior Engineer",
                                    "experience": [],
                                    "skills": ["React", "TypeScript"],
                                }
                                mock_scr.return_value = {
                                    "keyword_coverage": {"React": True, "TypeScript": True},
                                    "semantic_score": 0.85,
                                    "terminology_mismatches": [],
                                    "overall_score": 0.85,
                                }
                                mock_ref.return_value = {
                                    "refined_content": "Refined resume...",
                                    "changes_made": [],
                                    "remaining_gaps": [],
                                    "coverage_improvement": 0,
                                }

                                # Run
                                result = resume_generation.run_resume_generation(
                                    "jd-123", "user-1", mock_fit_report, mode="full"
                                )

                                # Assert
                                assert result["id"] == "variant-1"
                                assert result["version"] == 1
                                assert mock_create.called


# ---------------------------------------------------------------------------
# Test: Generator failure
# ---------------------------------------------------------------------------


def test_full_regenerate_generator_fails(
    mock_jd: dict[str, Any],
    mock_narratives: list[dict[str, Any]],
    mock_fit_report: dict[str, Any],
) -> None:
    """Test that generator failure stops pipeline and raises error."""
    with patch("features.resume_generation.job_descriptions.get_jd", return_value=mock_jd):
        with patch(
            "features.resume_generation.narratives.list_narratives", return_value=mock_narratives
        ):
            with patch(
                "features.resume_generation.run_generator",
                side_effect=RuntimeError("Claude error"),
            ):
                with pytest.raises(RuntimeError, match="generator_failed"):
                    resume_generation.run_resume_generation(
                        "jd-123", "user-1", mock_fit_report, mode="full"
                    )


# ---------------------------------------------------------------------------
# Test: Screener failure
# ---------------------------------------------------------------------------


def test_full_regenerate_screener_fails(
    mock_jd: dict[str, Any],
    mock_narratives: list[dict[str, Any]],
    mock_fit_report: dict[str, Any],
) -> None:
    """Test that screener failure stops pipeline."""
    with patch("features.resume_generation.job_descriptions.get_jd", return_value=mock_jd):
        with patch(
            "features.resume_generation.narratives.list_narratives", return_value=mock_narratives
        ):
            with patch(
                "features.resume_generation.resume_variants.get_latest_variant", return_value=None
            ):
                with patch("features.resume_generation.run_generator", return_value={"skills": []}):
                    with patch(
                        "features.resume_generation.run_screener",
                        side_effect=RuntimeError("Screener error"),
                    ):
                        with pytest.raises(RuntimeError, match="screener_failed"):
                            resume_generation.run_resume_generation(
                                "jd-123", "user-1", mock_fit_report, mode="full"
                            )


# ---------------------------------------------------------------------------
# Test: Refinement failure
# ---------------------------------------------------------------------------


def test_full_regenerate_refinement_fails(
    mock_jd: dict[str, Any],
    mock_narratives: list[dict[str, Any]],
    mock_fit_report: dict[str, Any],
) -> None:
    """Test that refinement failure stops pipeline."""
    with patch("features.resume_generation.job_descriptions.get_jd", return_value=mock_jd):
        with patch(
            "features.resume_generation.narratives.list_narratives", return_value=mock_narratives
        ):
            with patch(
                "features.resume_generation.resume_variants.get_latest_variant", return_value=None
            ):
                with patch(
                    "features.resume_generation.run_generator",
                    return_value={"skills": [], "summary": "Senior Engineer"},
                ):
                    with patch(
                        "features.resume_generation.run_screener",
                        return_value={"overall_score": 0.8},
                    ):
                        with patch(
                            "features.resume_generation.run_refinement",
                            side_effect=RuntimeError("Refinement error"),
                        ):
                            with pytest.raises(RuntimeError, match="refinement_failed"):
                                resume_generation.run_resume_generation(
                                    "jd-123", "user-1", mock_fit_report, mode="full"
                                )


# ---------------------------------------------------------------------------
# Test: Refine existing mode
# ---------------------------------------------------------------------------


def test_refine_existing_success(
    mock_jd: dict[str, Any],
    mock_narratives: list[dict[str, Any]],
    mock_fit_report: dict[str, Any],
    mock_resume_variant: dict[str, Any],
) -> None:
    """Test refine-existing mode (step 3 only)."""
    with patch("features.resume_generation.job_descriptions.get_jd", return_value=mock_jd):
        with patch(
            "features.resume_generation.narratives.list_narratives", return_value=mock_narratives
        ):
            with patch(
                "features.resume_generation.resume_variants.get_latest_variant",
                return_value=mock_resume_variant,
            ):
                with patch("features.resume_generation.run_refinement") as mock_ref:
                    with patch(
                        "features.resume_generation.resume_variants.create_resume_variant"
                    ) as mock_create:
                        mock_ref.return_value = {
                            "refined_content": "Better resume...",
                            "changes_made": [
                                {"section": "skills", "change_description": "Added keywords"}
                            ],
                            "remaining_gaps": [],
                            "coverage_improvement": 0.05,
                        }
                        # Return variant with version 2 and parent_variant_id set
                        mock_create.return_value = {
                            **mock_resume_variant,
                            "version": 2,
                            "parent_variant_id": "variant-1",
                        }

                        result = resume_generation.run_resume_generation(
                            "jd-123",
                            "user-1",
                            mock_fit_report,
                            mode="refine",
                            parent_variant_id="variant-1",
                        )

                        assert result["version"] == 2
                        assert result["parent_variant_id"] == "variant-1"
