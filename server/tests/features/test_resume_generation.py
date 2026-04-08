"""Tests for resume generation pipeline."""

from typing import Any
from unittest.mock import MagicMock, patch

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
                "features.resume_generation.resume_variants.get_variant_by_id",
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


# ---------------------------------------------------------------------------
# Test: JD not found in full mode
# ---------------------------------------------------------------------------


def test_run_resume_generation_jd_not_found_full_mode(
    mock_fit_report: dict[str, Any],
) -> None:
    """Verify ValueError when JD not found in full mode."""
    with patch("features.resume_generation.job_descriptions.get_jd", return_value=None):
        with pytest.raises(ValueError, match="Job description not found"):
            resume_generation.run_resume_generation(
                jd_id="missing-jd",
                user_id="user-1",
                fit_report=mock_fit_report,
                mode="full",
            )


# ---------------------------------------------------------------------------
# Test: Parent variant not found in refine mode
# ---------------------------------------------------------------------------


def test_run_resume_generation_parent_variant_not_found(
    mock_fit_report: dict[str, Any],
) -> None:
    """Verify ValueError when parent variant not found in refine mode."""
    with patch("features.resume_generation.job_descriptions.get_jd") as mock_get_jd:
        mock_get_jd.return_value = {"id": "jd-1", "content": "JD"}

        with patch(
            "features.resume_generation.resume_variants.get_variant_by_id"
        ) as mock_get_variant:
            mock_get_variant.return_value = None

            with pytest.raises(ValueError, match="Variant not found"):
                resume_generation.run_resume_generation(
                    jd_id="jd-1",
                    user_id="user-1",
                    fit_report=mock_fit_report,
                    mode="refine",
                    parent_variant_id="missing-variant",
                )


# ---------------------------------------------------------------------------
# Test: Refine requires parent_variant_id
# ---------------------------------------------------------------------------


def test_run_resume_generation_refine_requires_parent_id(
    mock_fit_report: dict[str, Any],
) -> None:
    """Verify ValueError when refine mode called without parent_variant_id."""
    with pytest.raises(ValueError, match="parent_variant_id required"):
        resume_generation.run_resume_generation(
            jd_id="jd-1",
            user_id="user-1",
            fit_report=mock_fit_report,
            mode="refine",
        )


# ---------------------------------------------------------------------------
# Test: Generator includes contact_info in output
# ---------------------------------------------------------------------------


def test_generator_includes_contact_in_output(
    mock_fit_report: dict[str, Any],
) -> None:
    """Test that generator includes contact field in output JSON."""
    from pipeline.generator import run_generator

    narratives_text = "Test background"
    contact_info = {
        "email": "test@example.com",
        "linkedin": "https://linkedin.com/in/test",
    }

    # Create mock response object with proper structure
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = {
        "summary": "Senior Engineer",
        "experience": [
            {
                "company": "TechCorp",
                "title": "Senior Engineer",
                "dates": "2020-2026",
                "projects": [
                    {
                        "name": "React Platform",
                        "dates": "2020-2026",
                        "bullets": ["Built scalable system"],
                    }
                ],
            }
        ],
        "skills": ["React", "TypeScript"],
        "contact": {
            "email": "test@example.com",
            "linkedin": "https://linkedin.com/in/test",
        },
    }
    mock_response = MagicMock()
    mock_response.content = [mock_tool_block]

    with patch("pipeline.generator._get_anthropic_client") as mock_get_client:
        with patch("pipeline.generator.load_prompt") as mock_load_prompt:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt"

            result = run_generator(narratives_text, mock_fit_report, contact_info, "user-1")

            assert "contact" in result
            assert result["contact"]["email"] == "test@example.com"
            assert result["contact"]["linkedin"] == "https://linkedin.com/in/test"


# ---------------------------------------------------------------------------
# Test: Resume variant persists contact_info
# ---------------------------------------------------------------------------


def test_resume_variant_persists_contact_info() -> None:
    """Test that contact_info is saved to resume_variants table."""
    from db import resume_variants

    contact_data = {"email": "test@example.com"}

    with patch("db.resume_variants.get_client") as mock_get_client:
        # Mock the Supabase client response
        mock_response = {
            "data": [
                {
                    "id": "variant-1",
                    "user_id": "user-1",
                    "job_description_id": "jd-123",
                    "content": "Test resume",
                    "version": 1,
                    "screener_report": {},
                    "contact_info": contact_data,
                    "parent_variant_id": None,
                    "created_at": "2026-03-28T00:00:00",
                }
            ]
        }
        mock_table = (
            mock_get_client.return_value.table.return_value.insert.return_value.execute.return_value
        )
        mock_table.data = mock_response["data"]

        variant = resume_variants.create_resume_variant(
            job_description_id="jd-123",
            user_id="user-1",
            content="Test resume",
            version=1,
            screener_report={},
            contact_info=contact_data,
        )

        assert variant["contact_info"] == contact_data


# ---------------------------------------------------------------------------
# Test: Full pipeline preserves contact_info
# ---------------------------------------------------------------------------


def test_resume_generation_with_contact_info(
    mock_jd: dict[str, Any],
    mock_narratives: list[dict[str, Any]],
    mock_fit_report: dict[str, Any],
    mock_resume_variant: dict[str, Any],
) -> None:
    """Test full pipeline: fit assessment → generate resume with contact → screener → refinement."""
    contact_data = {"email": "test@example.com", "linkedin": "https://linkedin.com/in/test"}

    # Add contact_info to first narrative (career overview)
    mock_narratives_with_contact = [
        {**mock_narratives[0], "contact_info": contact_data},
        mock_narratives[1],
    ]

    # Add contact_info to the variant response
    mock_variant_with_contact = {**mock_resume_variant, "contact_info": contact_data}

    with patch("features.resume_generation.job_descriptions.get_jd", return_value=mock_jd):
        with patch(
            "features.resume_generation.narratives.list_narratives",
            return_value=mock_narratives_with_contact,
        ):
            with patch(
                "features.resume_generation.resume_variants.get_latest_variant", return_value=None
            ):
                with patch("features.resume_generation.run_generator") as mock_gen:
                    with patch("features.resume_generation.run_screener") as mock_scr:
                        with patch("features.resume_generation.run_refinement") as mock_ref:
                            with patch(
                                "features.resume_generation.resume_variants.create_resume_variant",
                                return_value=mock_variant_with_contact,
                            ) as mock_create:
                                # Setup mock returns
                                mock_gen.return_value = {
                                    "summary": "Senior Engineer",
                                    "experience": [],
                                    "skills": ["React", "TypeScript"],
                                    "contact": contact_data,
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

                                # Run the pipeline
                                result = resume_generation.run_resume_generation(
                                    "jd-123", "user-1", mock_fit_report, mode="full"
                                )

                                # Verify contact_info was persisted
                                assert "contact_info" in result
                                assert result["contact_info"]["email"] == "test@example.com"
                                # Verify create_resume_variant was called with contact_info
                                call_kwargs = mock_create.call_args.kwargs
                                assert "contact_info" in call_kwargs
                                assert call_kwargs["contact_info"] == contact_data


# ---------------------------------------------------------------------------
# Test: Generator with None contact_info edge case
# ---------------------------------------------------------------------------


def test_generator_with_contact_info_none() -> None:
    """Test that generator handles None contact_info gracefully."""
    from pipeline.generator import run_generator

    narratives_text = "Test background"
    fit_report = {}
    contact_info = None  # No contact info provided

    # Create mock response object with proper structure
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = {
        "summary": "Senior Engineer",
        "experience": [
            {
                "company": "TechCorp",
                "title": "Senior Engineer",
                "dates": "2020-2026",
                "projects": [
                    {
                        "name": "React Platform",
                        "dates": "2020-2026",
                        "bullets": ["Built scalable system"],
                    }
                ],
            }
        ],
        "skills": ["React", "TypeScript"],
        "contact": {},
    }
    mock_response = MagicMock()
    mock_response.content = [mock_tool_block]

    with patch("pipeline.generator._get_anthropic_client") as mock_get_client:
        with patch("pipeline.generator.load_prompt") as mock_load_prompt:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt"

            result = run_generator(narratives_text, fit_report, contact_info, "user-1")

            # Should still include contact field, but it will be empty or not present
            assert "contact" in result or result.get("contact") == {}


# ---------------------------------------------------------------------------
# Test: Generator with empty contact dict edge case
# ---------------------------------------------------------------------------


def test_generator_with_empty_contact_dict() -> None:
    """Test that generator handles empty contact dict."""
    from pipeline.generator import run_generator

    narratives_text = "Test background"
    fit_report = {}
    contact_info = {}  # Empty dict

    # Create mock response object with proper structure
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = {
        "summary": "Senior Engineer",
        "experience": [
            {
                "company": "TechCorp",
                "title": "Senior Engineer",
                "dates": "2020-2026",
                "projects": [
                    {
                        "name": "React Platform",
                        "dates": "2020-2026",
                        "bullets": ["Built scalable system"],
                    }
                ],
            }
        ],
        "skills": ["React", "TypeScript"],
        "contact": {},
    }
    mock_response = MagicMock()
    mock_response.content = [mock_tool_block]

    with patch("pipeline.generator._get_anthropic_client") as mock_get_client:
        with patch("pipeline.generator.load_prompt") as mock_load_prompt:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt"

            result = run_generator(narratives_text, fit_report, contact_info, "user-1")

            assert "contact" in result
            # Empty dict should pass through
            assert result["contact"] == {} or all(v is None for v in result["contact"].values())


# ---------------------------------------------------------------------------
# Test: Generator with partial contact info edge case
# ---------------------------------------------------------------------------


def test_generator_with_partial_contact_info() -> None:
    """Test that generator handles partial contact info (only some fields)."""
    from pipeline.generator import run_generator

    narratives_text = "Test background"
    fit_report = {}
    contact_info = {"email": "test@example.com"}  # Only email, no phone/location/etc

    # Create mock response object with proper structure
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = {
        "summary": "Senior Engineer",
        "experience": [
            {
                "company": "TechCorp",
                "title": "Senior Engineer",
                "dates": "2020-2026",
                "projects": [
                    {
                        "name": "React Platform",
                        "dates": "2020-2026",
                        "bullets": ["Built scalable system"],
                    }
                ],
            }
        ],
        "skills": ["React", "TypeScript"],
        "contact": {"email": "test@example.com"},
    }
    mock_response = MagicMock()
    mock_response.content = [mock_tool_block]

    with patch("pipeline.generator._get_anthropic_client") as mock_get_client:
        with patch("pipeline.generator.load_prompt") as mock_load_prompt:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt"

            result = run_generator(narratives_text, fit_report, contact_info, "user-1")

            assert "contact" in result
            assert result["contact"]["email"] == "test@example.com"
            # Other fields might be null or missing
