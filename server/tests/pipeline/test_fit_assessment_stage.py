"""Tests for fit assessment stage module.

Validates that fit assessment stage correctly accepts FitAssessmentInput,
calls Anthropic Claude with proper schema, and returns FitAssessmentOutput.
"""

from unittest.mock import MagicMock, patch

import pytest

from pipeline.fit_assessment_stage import run_fit_assessment_stage
from pipeline.stage_input import FitAssessmentInput, FitAssessmentOutput


class TestFitAssessmentStage:
    """Validate fit assessment stage contract and behavior."""

    def test_returns_structured_output(self) -> None:
        """Verify stage returns valid FitAssessmentOutput."""
        input_data = FitAssessmentInput(
            jd_content="React engineer, TypeScript, 5+ years",
            narratives_text="Senior frontend engineer with React expertise",
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "fit_level": "strong",
            "matches": [
                {"requirement": "React", "priority": "required", "notes": "core skill"},
                {"requirement": "TypeScript", "priority": "required", "notes": "core skill"},
            ],
            "gaps": [],
            "terminology": [{"my_term": "frontend", "jd_term": "UI engineer", "confidence": 0.85}],
            "reasoning": "Strong match for the role",
            "overall_score": 0.85,
            "semantic_score": 0.85,
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.fit_assessment_stage._get_anthropic_client") as mock_get_client,
            patch("pipeline.fit_assessment_stage.load_prompt") as mock_load_prompt,
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt for screener"

            output = run_fit_assessment_stage(input_data)

            assert isinstance(output, FitAssessmentOutput)
            assert output.fit_level == "strong"
            assert output.overall_score == 0.85
            assert output.semantic_score == 0.85
            assert len(output.matches) == 2
            assert len(output.gaps) == 0
            assert len(output.terminology) == 1
            assert output.keyword_coverage["react"] is True
            assert output.keyword_coverage["typescript"] is True

    def test_converts_scores_to_fit_levels(self) -> None:
        """Verify stage correctly maps overall_score to fit_level."""
        input_data = FitAssessmentInput(
            jd_content="JD",
            narratives_text="Narratives",
            user_id="user-123",
        )

        test_cases = [
            (0.85, "strong"),
            (0.72, "moderate"),
            (0.55, "borderline"),
            (0.25, "poor"),
        ]

        for score, expected_level in test_cases:
            mock_response = MagicMock()
            mock_tool_block = MagicMock()
            mock_tool_block.type = "tool_use"
            mock_tool_block.input = {
                "fit_level": "strong",  # API returns this, but we recalculate
                "matches": [],
                "gaps": [],
                "terminology": [],
                "reasoning": "Test",
                "overall_score": score,
                "semantic_score": score,
            }
            mock_response.content = [mock_tool_block]

            with (
                patch("pipeline.fit_assessment_stage._get_anthropic_client") as mock_get_client,
                patch("pipeline.fit_assessment_stage.load_prompt"),
            ):
                mock_client = MagicMock()
                mock_client.messages.create.return_value = mock_response
                mock_get_client.return_value = mock_client

                output = run_fit_assessment_stage(input_data)

                assert output.fit_level == expected_level

    def test_calls_api_with_correct_inputs(self) -> None:
        """Verify stage calls Anthropic with proper parameters."""
        input_data = FitAssessmentInput(
            jd_content="JD content here",
            narratives_text="Narratives here",
            user_id="user-456",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "fit_level": "strong",
            "matches": [],
            "gaps": [],
            "terminology": [],
            "reasoning": "Test",
            "overall_score": 0.85,
            "semantic_score": 0.85,
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.fit_assessment_stage._get_anthropic_client") as mock_get_client,
            patch("pipeline.fit_assessment_stage.load_prompt") as mock_load_prompt,
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt"

            run_fit_assessment_stage(input_data)

            # Verify API was called with correct parameters
            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["model"] == "claude-sonnet-4-20250514"
            assert call_kwargs["max_tokens"] == 4096
            assert call_kwargs["system"] == "System prompt"
            assert len(call_kwargs["messages"]) == 1
            assert "JD content here" in call_kwargs["messages"][0]["content"]
            assert "Narratives here" in call_kwargs["messages"][0]["content"]

    def test_filters_low_confidence_terminology(self) -> None:
        """Verify stage filters out low-confidence terminology mappings."""
        input_data = FitAssessmentInput(
            jd_content="JD",
            narratives_text="Narratives",
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "fit_level": "strong",
            "matches": [],
            "gaps": [],
            "terminology": [
                {"my_term": "frontend", "jd_term": "UI engineer", "confidence": 0.95},
                {"my_term": "api", "jd_term": "backend", "confidence": 0.5},  # Low confidence
                {"my_term": "mobile", "jd_term": "iOS dev", "confidence": 0.8},
            ],
            "reasoning": "Test",
            "overall_score": 0.85,
            "semantic_score": 0.85,
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.fit_assessment_stage._get_anthropic_client") as mock_get_client,
            patch("pipeline.fit_assessment_stage.load_prompt"),
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            output = run_fit_assessment_stage(input_data)

            # Only high-confidence terms should be kept (>= 0.8)
            assert len(output.terminology) == 2
            assert output.terminology[0]["confidence"] == 0.95
            assert output.terminology[1]["confidence"] == 0.8

    def test_extracts_keywords_for_coverage_mapping(self) -> None:
        """Verify stage extracts keywords from JD and builds coverage map."""
        input_data = FitAssessmentInput(
            jd_content="We need Python, Java, and AWS expertise for this backend role",
            narratives_text="Senior backend engineer with Python and Java experience",
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "fit_level": "moderate",
            "matches": [
                {"requirement": "Python", "priority": "required", "notes": ""},
                {"requirement": "Java", "priority": "required", "notes": ""},
            ],
            "gaps": [{"requirement": "AWS", "type": "hard", "notes": ""}],
            "terminology": [],
            "reasoning": "Has most skills",
            "overall_score": 0.72,
            "semantic_score": 0.72,
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.fit_assessment_stage._get_anthropic_client") as mock_get_client,
            patch("pipeline.fit_assessment_stage.load_prompt"),
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            output = run_fit_assessment_stage(input_data)

            # Check keyword coverage is built from matches and gaps
            assert "python" in output.keyword_coverage
            assert output.keyword_coverage["python"] is True
            assert "java" in output.keyword_coverage
            assert output.keyword_coverage["java"] is True
            assert "aws" in output.keyword_coverage
            assert output.keyword_coverage["aws"] is False  # In gaps, so False

    def test_handles_missing_tool_output(self) -> None:
        """Verify stage raises error when API response has no tool_use block."""
        input_data = FitAssessmentInput(
            jd_content="React engineer",
            narratives_text="Senior frontend engineer",
            user_id="user-123",
        )

        with patch("pipeline.fit_assessment_stage._get_anthropic_client") as mock_client:
            # Mock response with no tool_use block
            mock_response = MagicMock()
            mock_response.content = []  # Empty, no tool output
            mock_client.return_value.messages.create.return_value = mock_response

            with patch("pipeline.fit_assessment_stage.load_prompt"):
                with pytest.raises(RuntimeError, match="No tool_use block in response"):
                    run_fit_assessment_stage(input_data)
