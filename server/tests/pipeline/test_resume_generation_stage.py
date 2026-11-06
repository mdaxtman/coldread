"""Tests for resume generation stage module.

Validates that resume generation stage correctly accepts ResumeGenerationInput,
calls Anthropic Claude with proper schema, and returns ResumeGenerationOutput
with markdown-formatted resume content.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pipeline.generator import BULLET_BUDGET
from pipeline.resume_generation_stage import run_resume_generation_stage
from pipeline.stage_input import FitAssessmentOutput, ResumeGenerationInput, ResumeGenerationOutput

# The generator samples again when a draft has no roles, so every canned draft
# below carries at least one.
_ROLE = {"company": "Acme", "title": "Engineer", "dates": "2020 – 2024", "projects": []}


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
            jd_content="Senior React engineer wanted",
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
            patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
            patch("pipeline.generator.load_prompt") as mock_load_prompt,
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
            jd_content="Senior React engineer wanted",
            fit_assessment_output=fit_output,
            contact_info={"email": "john@example.com", "phone": "555-1234", "linkedin": "john-doe"},
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "summary": "Senior Engineer",
            "experience": [_ROLE],
            "skills": ["React"],
            "contact": {"email": "john@example.com", "phone": "555-1234", "linkedin": "john-doe"},
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
            patch("pipeline.generator.load_prompt"),
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
            jd_content="Senior React engineer wanted",
            fit_assessment_output=fit_output,
            contact_info=None,
            user_id="user-456",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "summary": "Senior engineer",
            "experience": [_ROLE],
            "skills": ["React"],
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
            patch("pipeline.generator.load_prompt") as mock_load_prompt,
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client
            mock_load_prompt.return_value = "System prompt"

            run_resume_generation_stage(input_data)

            # Verify API was called with correct parameters
            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["model"] == "claude-sonnet-5"
            assert call_kwargs["max_tokens"] == 8192
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
            jd_content="Senior React engineer wanted",
            fit_assessment_output=fit_output,
            contact_info=None,
            user_id="user-123",
        )

        with patch("pipeline.anthropic_utils._get_anthropic_client") as mock_client:
            # Mock response with no tool_use block
            mock_response = MagicMock()
            mock_response.content = []  # Empty, no tool output
            mock_client.return_value.messages.create.return_value = mock_response

            with patch("pipeline.generator.load_prompt"):
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
            jd_content="Senior React engineer wanted",
            fit_assessment_output=fit_output,
            contact_info=None,
            user_id="user-123",
        )

        mock_response = MagicMock()
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.input = {
            "summary": "Senior engineer",
            "experience": [_ROLE],
            "skills": ["React"],
        }
        mock_response.content = [mock_tool_block]

        with (
            patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
            patch("pipeline.generator.load_prompt"),
        ):
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_get_client.return_value = mock_client

            run_resume_generation_stage(input_data)

            # Verify fit assessment context is included in the message
            call_kwargs = mock_client.messages.create.call_args[1]
            message_content = call_kwargs["messages"][0]["content"]
            assert "[REQUIRED] React (core skill)" in message_content
            assert "[HARD] Rust" in message_content

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
            jd_content="Senior React engineer wanted",
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
            patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
            patch("pipeline.generator.load_prompt"),
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


_USABLE_DRAFT = {
    "summary": "Senior engineer",
    "experience": [
        {
            "company": "Earlier Co",
            "title": "Engineer",
            "dates": "2015 – 2019",
            "projects": [{"name": "Platform", "bullets": ["Built the platform"]}],
        },
        {
            "company": "Current Co",
            "title": "Senior Engineer",
            "dates": "2019 – Present",
            "projects": [{"name": "Console", "bullets": ["Led the console"]}],
        },
    ],
    "skills": ["React"],
}


def _stage_input(jd_content: str = "the posting") -> ResumeGenerationInput:
    return ResumeGenerationInput(
        narratives_text="Senior React engineer",
        jd_content=jd_content,
        fit_assessment_output=FitAssessmentOutput(
            fit_level="strong",
            matches=[{"requirement": "React", "priority": "required", "notes": "core skill"}],
            gaps=[{"requirement": "GraphQL", "type": "soft", "notes": "one small project"}],
            terminology=[],
            overall_score=0.85,
            semantic_score=0.85,
            keyword_coverage={"react": True, "graphql": False},
        ),
        contact_info=None,
        user_id="user-123",
    )


def _run_stage_capturing_requests(
    input_data: ResumeGenerationInput, drafts: list[dict[str, Any]]
) -> tuple[ResumeGenerationOutput, list[str]]:
    """Run the stage against canned drafts; return its output and each request's message.

    The prompt is stubbed at the DB read, below every module that loads it, so
    these tests hold whichever module builds the request.
    """
    responses = []
    for draft in drafts:
        block = MagicMock()
        block.type = "tool_use"
        block.input = draft
        response = MagicMock()
        response.content = [block]
        responses.append(response)

    with (
        patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
        patch(
            "pipeline.prompt_loader.prompts.get_active_prompt",
            return_value={"template": "System prompt", "version": 1},
        ),
    ):
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = responses
        mock_get_client.return_value = mock_client

        output = run_resume_generation_stage(input_data)

    messages = [
        call.kwargs["messages"][0]["content"] for call in mock_client.messages.create.call_args_list
    ]
    return output, messages


class TestStageSendsTheLiveGeneratorRequest:
    """The stage loads the same `generator` prompt as the app's generator, so it
    has to send the request that prompt was written for."""

    def test_request_carries_the_posting_and_ends_with_the_bullet_budget(self) -> None:
        """The posting sits between the narratives and the fit report, and the
        bullet budget is the last thing the generator reads."""
        _, messages = _run_stage_capturing_requests(_stage_input(), [_USABLE_DRAFT])

        message = messages[0]
        posting = message.index("<job_description>\nthe posting\n</job_description>")
        assert message.index("<candidate_background>") < posting < message.index("<fit_assessment>")
        assert message.endswith(
            f"at most {BULLET_BUDGET} bullets in total across every role and project. "
            "Count them before you submit."
        )

    def test_gap_labels_match_the_generator_prompt(self) -> None:
        """Gaps are named at their true depth, as the prompt says. The stage's
        own labels told the generator to omit them."""
        _, messages = _run_stage_capturing_requests(_stage_input(), [_USABLE_DRAFT])

        assert "name lighter-but-real work at its true depth" in messages[0]
        assert "Omit if in doubt" not in messages[0]

    def test_unusable_draft_is_sampled_again(self) -> None:
        """A draft with no roles is not rendered as a resume."""
        no_roles = {**_USABLE_DRAFT, "experience": []}

        output, messages = _run_stage_capturing_requests(_stage_input(), [no_roles, _USABLE_DRAFT])

        assert len(messages) == 2
        assert "Current Co" in output.content

    def test_roles_are_rendered_most_recent_first(self) -> None:
        """The draft lists the current role second; the resume lists it first."""
        output, _ = _run_stage_capturing_requests(_stage_input(), [_USABLE_DRAFT])

        assert output.content.index("Current Co") < output.content.index("Earlier Co")
