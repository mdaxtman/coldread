from unittest.mock import MagicMock, patch

import pytest

import pipeline.anthropic_utils
from pipeline.anthropic_utils import _get_anthropic_client


@pytest.fixture(autouse=True)
def reset_anthropic_client() -> None:
    """Reset the singleton client before each test."""
    pipeline.anthropic_utils._client = None
    yield
    pipeline.anthropic_utils._client = None


def test_get_anthropic_client_returns_singleton() -> None:
    """Verify that _get_anthropic_client returns the same instance."""
    with patch("pipeline.anthropic_utils.anthropic.Anthropic") as mock_client:
        client1 = _get_anthropic_client()
        client2 = _get_anthropic_client()
        assert client1 is client2
        # Only called once due to singleton pattern
        mock_client.assert_called_once()


def test_get_anthropic_client_initializes_with_api_key() -> None:
    """Verify that the client is initialized with the API key from config."""
    with (
        patch("pipeline.anthropic_utils.get_anthropic_api_key") as mock_get_key,
        patch("pipeline.anthropic_utils.anthropic.Anthropic") as mock_client_class,
    ):
        mock_get_key.return_value = "test-key-123"
        _get_anthropic_client()
        mock_client_class.assert_called_once_with(api_key="test-key-123")


def test_extract_tool_response_returns_tool_input() -> None:
    """Verify that tool input is extracted from response."""
    from pipeline.anthropic_utils import _extract_tool_response

    mock_response = MagicMock()
    mock_tool_block = MagicMock()
    mock_tool_block.type = "tool_use"
    mock_tool_block.input = {"key": "value"}

    mock_response.content = [mock_tool_block]

    result = _extract_tool_response(mock_response)
    assert result == {"key": "value"}


def test_extract_tool_response_raises_on_missing_tool() -> None:
    """Verify that RuntimeError is raised if no tool_use block found."""
    from pipeline.anthropic_utils import _extract_tool_response

    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="text")]

    with pytest.raises(RuntimeError, match="No tool_use block"):
        _extract_tool_response(mock_response)
