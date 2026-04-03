from unittest.mock import MagicMock, patch

from pipeline.fit_assessment import run_fit_assessment


def test_run_fit_assessment_calls_api_and_returns_result() -> None:
    """Verify fit assessment calls Anthropic and returns structured result."""
    mock_response = MagicMock()
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = {
        "fit_level": "strong",
        "matches": [{"requirement": "Python", "priority": "required", "notes": "primary"}],
        "gaps": [],
        "terminology": [],
        "reasoning": "Strong match",
    }
    mock_response.content = [mock_tool_block]

    with (
        patch("pipeline.fit_assessment._get_anthropic_client") as mock_get_client,
        patch("pipeline.fit_assessment.load_prompt") as mock_load_prompt,
    ):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        mock_load_prompt.return_value = "System prompt"

        result = run_fit_assessment(
            jd_content="JD text", narratives_text="Narratives", user_id="user-123"
        )

        assert result["fit_level"] == "strong"
        assert len(result["matches"]) == 1
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-20250514"
        assert call_kwargs["max_tokens"] == 4096
