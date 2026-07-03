from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pipeline.refinement import _format_resume_for_screener, run_refinement


def test_format_resume_for_screener_with_all_sections() -> None:
    """Verify resume is formatted back to text correctly."""
    resume_data = {
        "summary": "Experienced engineer",
        "experience": [
            {
                "title": "Senior Engineer",
                "company": "Acme",
                "dates": "2020-2023",
                "projects": [
                    {
                        "name": "Project A",
                        "dates": "2021-2022",
                        "bullets": ["Did thing 1", "Did thing 2"],
                    }
                ],
            }
        ],
        "skills": ["Python", "Go"],
        "education": [{"name": "University", "degree": "BS Computer Science", "year": "2015"}],
    }

    result = _format_resume_for_screener(resume_data)
    assert "## Summary" in result
    assert "Experienced engineer" in result
    assert "## Experience" in result
    assert "**Senior Engineer** at Acme (2020-2023)" in result
    assert "**Project A** (2021-2022)" in result
    assert "- Did thing 1" in result
    assert "## Skills" in result
    assert "Python, Go" in result
    assert "## Education" in result
    assert "University: BS Computer Science (2015)" in result


def test_format_resume_for_screener_with_missing_sections() -> None:
    """Verify formatting handles resume with only summary and skills."""
    resume_data = {"summary": "Experienced engineer", "skills": ["Python", "Go"]}

    result = _format_resume_for_screener(resume_data)
    assert "## Summary" in result
    assert "Experienced engineer" in result
    assert "## Skills" in result
    assert "Python, Go" in result
    # Should not include Experience or Education sections
    assert "## Experience" not in result
    assert "## Education" not in result


def test_format_resume_for_screener_with_empty_arrays() -> None:
    """Verify formatting handles resume with empty experience/skills/education."""
    resume_data = {"summary": "Engineer", "experience": [], "skills": [], "education": []}

    result = _format_resume_for_screener(resume_data)
    assert "## Summary" in result
    # Empty arrays should not create section headers
    assert "## Experience" not in result
    assert "## Skills" not in result
    assert "## Education" not in result


def test_run_refinement_calls_api_and_returns_refined_content() -> None:
    """Verify run_refinement calls Anthropic and returns refinement output."""
    mock_response = MagicMock()
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = {
        "refined_content": "Refined resume text",
        "changes_made": [{"section": "Experience", "change_description": "Updated bullets"}],
        "remaining_gaps": [],
        "coverage_improvement": 0.1,
    }
    mock_response.content = [mock_tool_block]

    with (
        patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
        patch("pipeline.refinement.load_prompt") as mock_load_prompt,
    ):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        mock_load_prompt.return_value = "System prompt"

        result = run_refinement(
            resume_data={"summary": "", "experience": [], "skills": []},
            screener_report={},
            narratives_text="Narratives",
            jd_content="JD",
            user_id="user-123",
        )

        assert result["refined_content"] == "Refined resume text"
        assert len(result["changes_made"]) == 1
        mock_client.messages.create.assert_called_once()

        # Verify API call parameters
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-5"
        assert call_kwargs["max_tokens"] == 8192
        assert "job_description" in call_kwargs["messages"][0]["content"]
        assert "generated_resume" in call_kwargs["messages"][0]["content"]


def _run_refinement_with_tool_input(tool_input: dict[str, Any]) -> dict[str, Any]:
    """Run run_refinement with a mocked client returning the given tool input."""
    mock_response = MagicMock()
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = tool_input
    mock_response.content = [mock_tool_block]

    with (
        patch("pipeline.anthropic_utils._get_anthropic_client") as mock_get_client,
        patch("pipeline.refinement.load_prompt") as mock_load_prompt,
    ):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        mock_load_prompt.return_value = "System prompt"

        return dict(
            run_refinement(
                resume_data={"summary": "", "experience": [], "skills": []},
                screener_report={},
                narratives_text="Narratives",
                jd_content="JD",
                user_id="user-123",
            )
        )


def test_run_refinement_normalizes_refined_resume_key_drift() -> None:
    """claude-sonnet-5 may return `refined_resume`; content must be preserved."""
    result = _run_refinement_with_tool_input(
        {"refined_resume": "Refined resume text", "changes_made": []}
    )
    assert result["refined_content"] == "Refined resume text"
    assert "refined_resume" not in result


def test_run_refinement_raises_when_no_refined_content_key() -> None:
    """A tool response missing both keys raises RuntimeError naming the keys."""
    with pytest.raises(RuntimeError, match=r"no refined_content \(keys: \['changes_made'\]\)"):
        _run_refinement_with_tool_input({"changes_made": []})
