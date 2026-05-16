"""Tests for resume generation stage module.

Validates that resume generation stage correctly accepts ResumeGenerationInput,
calls Anthropic Claude with proper schema, and returns ResumeGenerationOutput
with markdown-formatted resume content.
"""

from unittest.mock import MagicMock, patch

import pytest

from pipeline.resume_generation_stage import run_resume_generation_stage
from pipeline.stage_input import FitAssessmentOutput, ResumeGenerationInput, ResumeGenerationOutput


class TestResumeGenerationStage:
    """Validate resume generation stage contract and behavior."""

    def test_returns_structured_output_with_markdown(self) -> None:
        """Verify stage returns valid ResumeGenerationOutput with markdown."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            overall_score=0.8,
            semantic_score=0.85,
            keyword_coverage={},
        )

        input_data = ResumeGenerationInput(
            narratives_text="Senior engineer with React experience",
            fit_assessment_output=fit_output,
            contact_info={"email": "test@example.com"},
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "summary": "Senior Frontend Engineer with 8+ years of experience",
            "experience": [
                {
                    "company": "TechCorp",
                    "title": "Senior Engineer",
                    "dates": "2020-2024",
                    "projects": [
                        {
                            "name": "React Redesign",
                            "dates": "2023-2024",
                            "bullets": ["Led React migration", "Improved performance by 40%"],
                        }
                    ],
                }
            ],
            "skills": ["React", "TypeScript", "Node.js"],
            "contact": {"email": "test@example.com"},
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.resume_generation_stage._get_anthropic_client") as mock_get_client,
            patch("pipeline.resume_generation_stage.load_prompt") as mock_load_prompt,
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt for generator"

            output = run_resume_generation_stage(input_data)

            assert isinstance(output, ResumeGenerationOutput)
            assert isinstance(output.content, str)
            assert len(output.content) > 0
            assert "Senior Frontend Engineer" in output.content
            assert "React" in output.content
            assert output.contact_info == {"email": "test@example.com"}

    def test_includes_contact_info_in_markdown(self) -> None:
        """Verify stage includes contact information in markdown."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            overall_score=0.8,
            semantic_score=0.85,
            keyword_coverage={},
        )

        input_data = ResumeGenerationInput(
            narratives_text="Senior engineer",
            fit_assessment_output=fit_output,
            contact_info={"email": "john@example.com", "phone": "555-1234", "linkedin": "john-doe"},
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "summary": "Senior Engineer",
            "experience": [],
            "skills": ["React"],
            "contact": {"email": "john@example.com", "phone": "555-1234", "linkedin": "john-doe"},
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.resume_generation_stage._get_anthropic_client") as mock_get_client,
            patch("pipeline.resume_generation_stage.load_prompt"),
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            output = run_resume_generation_stage(input_data)

            assert "john@example.com" in output.content
            assert "555-1234" in output.content or "john-doe" in output.content

    def test_calls_api_with_correct_inputs(self) -> None:
        """Verify stage calls Anthropic with proper parameters."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[{"requirement": "React", "priority": "required", "notes": ""}],
            gaps=[],
            terminology=[{"my_term": "frontend", "jd_term": "UI engineer", "confidence": 0.9}],
            overall_score=0.85,
            semantic_score=0.85,
            keyword_coverage={"react": True},
        )

        input_data = ResumeGenerationInput(
            narratives_text="Senior React engineer with 8+ years",
            fit_assessment_output=fit_output,
            contact_info=None,
            user_id="user-456",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "summary": "Senior engineer",
            "experience": [],
            "skills": ["React"],
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.resume_generation_stage._get_anthropic_client") as mock_get_client,
            patch("pipeline.resume_generation_stage.load_prompt") as mock_load_prompt,
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt"

            run_resume_generation_stage(input_data)

            # Verify API was called with correct parameters
            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["model"] == "claude-sonnet-4-20250514"
            assert call_kwargs["max_tokens"] == 4096
            assert call_kwargs["system"] == "System prompt"
            assert len(call_kwargs["messages"]) == 1
            assert "Senior React engineer with 8+ years" in call_kwargs["messages"][0]["content"]

    def test_handles_missing_tool_output(self) -> None:
        """Verify stage raises error when API response has no tool_use block."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            overall_score=0.8,
            semantic_score=0.85,
            keyword_coverage={},
        )

        input_data = ResumeGenerationInput(
            narratives_text="Senior engineer",
            fit_assessment_output=fit_output,
            contact_info=None,
            user_id="user-123",
        )

        with patch("pipeline.resume_generation_stage._get_anthropic_client") as mock_client:
            # Mock response with no tool_use block
            mock_response = MagicMock()
            mock_response.content = []  # Empty, no tool output
            mock_client.return_value.messages.create.return_value = mock_response

            with patch("pipeline.resume_generation_stage.load_prompt"):
                with pytest.raises(RuntimeError, match="No tool_use block in response"):
                    run_resume_generation_stage(input_data)

    def test_includes_fit_assessment_in_prompt(self) -> None:
        """Verify stage includes fit assessment context in the prompt."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[{"requirement": "React", "priority": "required", "notes": "core skill"}],
            gaps=[{"requirement": "Rust", "type": "hard", "notes": ""}],
            terminology=[{"my_term": "frontend", "jd_term": "UI engineer", "confidence": 0.9}],
            overall_score=0.85,
            semantic_score=0.85,
            keyword_coverage={"react": True, "rust": False},
        )

        input_data = ResumeGenerationInput(
            narratives_text="Senior React engineer",
            fit_assessment_output=fit_output,
            contact_info=None,
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "summary": "Senior engineer",
            "experience": [],
            "skills": ["React"],
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.resume_generation_stage._get_anthropic_client") as mock_get_client,
            patch("pipeline.resume_generation_stage.load_prompt"),
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            run_resume_generation_stage(input_data)

            # Verify fit assessment context is included in the message
            call_kwargs = mock_client.messages.create.call_args[1]
            message_content = call_kwargs["messages"][0]["content"]
            assert "strong" in message_content.lower()  # fit_level
            assert "React" in message_content or "react" in message_content.lower()

    def test_markdown_includes_all_sections(self) -> None:
        """Verify markdown output includes summary, experience, and skills sections."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            overall_score=0.8,
            semantic_score=0.85,
            keyword_coverage={},
        )

        input_data = ResumeGenerationInput(
            narratives_text="Senior engineer",
            fit_assessment_output=fit_output,
            contact_info={"email": "test@example.com"},
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "summary": "Senior Engineer with React expertise",
            "experience": [
                {
                    "company": "TechCorp",
                    "title": "Senior Engineer",
                    "dates": "2020-2024",
                    "projects": [
                        {
                            "name": "React Redesign",
                            "dates": "2023-2024",
                            "bullets": ["Led migration", "Improved performance"],
                        }
                    ],
                }
            ],
            "skills": ["React", "TypeScript"],
            "contact": {"email": "test@example.com"},
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.resume_generation_stage._get_anthropic_client") as mock_get_client,
            patch("pipeline.resume_generation_stage.load_prompt"),
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            output = run_resume_generation_stage(input_data)

            # Verify markdown includes key sections
            markdown = output.content
            assert "## Summary" in markdown or "Summary" in markdown
            assert "## Experience" in markdown or "Experience" in markdown
            assert "## Skills" in markdown or "Skills" in markdown
            assert "Senior Engineer with React expertise" in markdown
            assert "React" in markdown
            assert "TypeScript" in markdown
