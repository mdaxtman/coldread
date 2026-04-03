from unittest.mock import MagicMock, patch

from pipeline.generator import _format_fit_report, _format_narratives, run_generator


def test_format_narratives_empty_list() -> None:
    """Verify formatting handles empty narratives."""
    result = _format_narratives([])
    assert result == "No candidate background narratives available."


def test_format_narratives_with_overview_and_roles() -> None:
    """Verify narratives are formatted into sections."""
    narratives = [
        {
            "title": "Career Overview",
            "content": "10 years in software",
            "category": "career_overview",
        },
        {"title": "Senior Engineer at Acme", "content": "Led team of 5", "category": "role"},
    ]
    result = _format_narratives(narratives)
    assert "## Career Overview" in result
    assert "### Career Overview" in result
    assert "## Role Narratives" in result
    assert "### Senior Engineer at Acme" in result
    assert "10 years in software" in result
    assert "Led team of 5" in result


def test_format_fit_report_all_sections() -> None:
    """Verify fit report is formatted with all sections."""
    fit_report = {
        "matches": [{"priority": "required", "requirement": "Python", "notes": "primary language"}],
        "gaps": [
            {"type": "soft", "requirement": "Go", "notes": None},
            {"type": "hard", "requirement": "Top secret clearance", "notes": None},
        ],
        "terminology": [{"my_term": "backend", "jd_term": "server-side"}],
    }
    result = _format_fit_report(fit_report)
    assert "MATCHES" in result
    assert "[REQUIRED] Python" in result
    assert "[SOFT] Go" in result
    assert "[HARD] Top secret clearance" in result
    assert "backend → server-side" in result


def test_run_generator_calls_api_and_returns_structured_data() -> None:
    """Verify run_generator calls Anthropic and extracts tool response."""
    mock_response = MagicMock()
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = {
        "summary": "Experienced engineer",
        "experience": [],
        "skills": ["Python", "Go"],
    }
    mock_response.content = [mock_tool_block]

    with (
        patch("pipeline.generator._get_anthropic_client") as mock_get_client,
        patch("pipeline.generator.load_prompt") as mock_load_prompt,
    ):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        mock_load_prompt.return_value = "System prompt"

        result = run_generator(
            narratives_text="Narrative text",
            fit_report={"matches": [], "gaps": [], "terminology": []},
            user_id="user-123",
        )

        assert result["summary"] == "Experienced engineer"
        assert result["skills"] == ["Python", "Go"]
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_kwargs["max_tokens"] == 4096
