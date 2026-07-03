"""Tests for refinement stage module.

Validates that refinement stage correctly accepts RefinementInput,
calls Anthropic Claude with proper schema, and returns RefinementOutput
with refined resume content and list of changes made.
"""

from unittest.mock import MagicMock, patch

import pytest

from pipeline.refinement_stage import run_refinement_stage
from pipeline.stage_input import FitAssessmentOutput, RefinementInput, RefinementOutput


class TestRefinementStage:
    """Validate refinement stage contract and behavior."""

    def test_returns_structured_output_with_refined_content(self) -> None:
        """Verify stage returns valid RefinementOutput with refined resume."""
        fit_output = FitAssessmentOutput(
            fit_level="moderate",
            matches=[],
            gaps=[{"requirement": "Kubernetes", "type": "hard", "notes": ""}],
            terminology=[],
            overall_score=0.65,
            semantic_score=0.7,
            keyword_coverage={},
        )

        input_data = RefinementInput(
            resume_content="## Summary\nSenior engineer...",
            fit_assessment_output=fit_output,
            jd_content="Kubernetes experience required",
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "refined_content": "## Summary\nSenior engineer with Kubernetes experience...",
            "changes": ["Added Kubernetes to summary"],
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
            patch("pipeline.refinement_stage.load_prompt") as mock_load_prompt,
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt for refinement"

            output = run_refinement_stage(input_data)

            assert isinstance(output, RefinementOutput)
            assert isinstance(output.refined_content, str)
            assert len(output.refined_content) > 0
            assert "Kubernetes" in output.refined_content
            assert isinstance(output.changes_made, list)
            assert len(output.changes_made) > 0

    def test_includes_gaps_in_prompt(self) -> None:
        """Verify stage includes fit assessment gaps in the refinement prompt."""
        fit_output = FitAssessmentOutput(
            fit_level="moderate",
            matches=[{"requirement": "React", "priority": "required", "notes": "core skill"}],
            gaps=[
                {"requirement": "Kubernetes", "type": "hard", "notes": "deployment platform"},
                {"requirement": "Docker", "type": "hard", "notes": "containerization"},
            ],
            terminology=[],
            overall_score=0.65,
            semantic_score=0.7,
            keyword_coverage={"react": True, "kubernetes": False, "docker": False},
        )

        input_data = RefinementInput(
            resume_content="## Summary\nSenior React engineer",
            fit_assessment_output=fit_output,
            jd_content="Kubernetes and Docker required for DevOps role",
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "refined_content": "## Summary\nSenior React engineer",
            "changes": [],
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
            patch("pipeline.refinement_stage.load_prompt") as mock_load_prompt,
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt"

            run_refinement_stage(input_data)

            # Verify gaps are included in the message
            call_kwargs = mock_client.messages.create.call_args[1]
            message_content = call_kwargs["messages"][0]["content"]
            assert "Kubernetes" in message_content or "kubernetes" in message_content.lower()
            assert "Docker" in message_content or "docker" in message_content.lower()

    def test_calls_api_with_correct_inputs(self) -> None:
        """Verify stage calls Anthropic with proper parameters."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            overall_score=0.85,
            semantic_score=0.85,
            keyword_coverage={},
        )

        input_data = RefinementInput(
            resume_content="## Summary\nSenior engineer with 8+ years",
            fit_assessment_output=fit_output,
            jd_content="JD content here",
            user_id="user-456",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "refined_content": "## Summary\nSenior engineer",
            "changes": [],
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
            patch("pipeline.refinement_stage.load_prompt") as mock_load_prompt,
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt"

            run_refinement_stage(input_data)

            # Verify API was called with correct parameters
            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["model"] == "claude-sonnet-5"
            assert call_kwargs["max_tokens"] == 8192
            assert call_kwargs["system"] == "System prompt"
            assert len(call_kwargs["messages"]) == 1
            assert "Senior engineer with 8+ years" in call_kwargs["messages"][0]["content"]
            assert "JD content here" in call_kwargs["messages"][0]["content"]

    def test_includes_resume_and_jd_in_prompt(self) -> None:
        """Verify stage includes resume content and JD in the refinement prompt."""
        fit_output = FitAssessmentOutput(
            fit_level="moderate",
            matches=[],
            gaps=[],
            terminology=[],
            overall_score=0.65,
            semantic_score=0.7,
            keyword_coverage={},
        )

        resume_content = (
            "## Summary\nSenior Full Stack Engineer\n## Experience\nReact and Node.js projects"
        )
        jd_content = "Looking for experienced full-stack engineers with React and Node.js"

        input_data = RefinementInput(
            resume_content=resume_content,
            fit_assessment_output=fit_output,
            jd_content=jd_content,
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "refined_content": resume_content,
            "changes": [],
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
            patch("pipeline.refinement_stage.load_prompt"),
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            run_refinement_stage(input_data)

            # Verify resume and JD are included in the message
            call_kwargs = mock_client.messages.create.call_args[1]
            message_content = call_kwargs["messages"][0]["content"]
            assert "Senior Full Stack Engineer" in message_content
            assert "React and Node.js" in message_content
            assert "Looking for experienced full-stack engineers" in message_content

    def test_returns_changes_made_list(self) -> None:
        """Verify stage returns list of changes made during refinement."""
        fit_output = FitAssessmentOutput(
            fit_level="moderate",
            matches=[],
            gaps=[],
            terminology=[],
            overall_score=0.65,
            semantic_score=0.7,
            keyword_coverage={},
        )

        input_data = RefinementInput(
            resume_content="## Summary\nSenior engineer",
            fit_assessment_output=fit_output,
            jd_content="JD content",
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "refined_content": "## Summary\nSenior engineer with specific skills",
            "changes": [
                "Enhanced summary with key skills",
                "Reworded experience section for clarity",
                "Updated terminology to match JD",
            ],
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
            patch("pipeline.refinement_stage.load_prompt"),
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            output = run_refinement_stage(input_data)

            assert len(output.changes_made) == 3
            assert "Enhanced summary with key skills" in output.changes_made
            assert "Reworded experience section for clarity" in output.changes_made
            assert "Updated terminology to match JD" in output.changes_made

    def test_handles_missing_tool_output(self) -> None:
        """Verify stage raises error when API response has no tool_use block."""
        fit_output = FitAssessmentOutput(
            fit_level="moderate",
            matches=[],
            gaps=[],
            terminology=[],
            overall_score=0.65,
            semantic_score=0.7,
            keyword_coverage={},
        )

        input_data = RefinementInput(
            resume_content="## Summary\nSenior engineer",
            fit_assessment_output=fit_output,
            jd_content="JD content",
            user_id="user-123",
        )

        with patch("pipeline.anthropic_utils._get_anthropic_client") as mock_client:
            # Mock response with no tool_use block
            mock_response = MagicMock()
            mock_response.content = []  # Empty, no tool output
            mock_client.return_value.messages.create.return_value = mock_response

            with patch("pipeline.refinement_stage.load_prompt"):
                with pytest.raises(RuntimeError, match="No tool_use block in response"):
                    run_refinement_stage(input_data)

    def test_handles_empty_gaps(self) -> None:
        """Verify stage handles fit assessment with no gaps gracefully."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[
                {"requirement": "React", "priority": "required", "notes": ""},
                {"requirement": "TypeScript", "priority": "required", "notes": ""},
            ],
            gaps=[],  # No gaps
            terminology=[],
            overall_score=0.85,
            semantic_score=0.85,
            keyword_coverage={"react": True, "typescript": True},
        )

        input_data = RefinementInput(
            resume_content="## Summary\nSenior React engineer",
            fit_assessment_output=fit_output,
            jd_content="React and TypeScript role",
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "refined_content": "## Summary\nSenior React engineer",
            "changes": [],
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
            patch("pipeline.refinement_stage.load_prompt"),
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            output = run_refinement_stage(input_data)

            # Should not raise, and output should be valid
            assert isinstance(output, RefinementOutput)
            assert output.refined_content
