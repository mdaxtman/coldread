from unittest.mock import MagicMock, patch

from pipeline.screener import run_screener


def test_run_screener_calls_api_and_returns_analysis() -> None:
    """Verify run_screener calls Anthropic and returns screener analysis."""
    mock_response = MagicMock()
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = {
        "keyword_coverage": {"Python": True},
        "semantic_score": 0.85,
        "terminology_mismatches": [],
        "overall_score": 0.85,
    }
    mock_response.content = [mock_tool_block]

    with (
        patch("pipeline.screener._get_anthropic_client") as mock_get_client,
        patch("pipeline.screener.load_prompt") as mock_load_prompt,
    ):
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        mock_load_prompt.return_value = "System prompt"

        result = run_screener(jd_content="JD text", resume_text="Resume text", user_id="user-123")

        assert result["overall_score"] == 0.85
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-20250514"
