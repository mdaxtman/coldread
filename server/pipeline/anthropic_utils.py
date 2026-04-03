"""Shared Anthropic integration utilities."""

from typing import Any, cast

import anthropic
from anthropic.types import Message

from config import get_anthropic_api_key

_client: anthropic.Anthropic | None = None


def _get_anthropic_client() -> anthropic.Anthropic:
    """Get or initialize the singleton Anthropic client."""
    global _client  # noqa: PLW0603
    if _client is None:
        _client = anthropic.Anthropic(api_key=get_anthropic_api_key())
    return _client


def _extract_tool_response(response: Message) -> dict[str, Any]:
    """Extract tool input from the first tool_use block in response.

    Args:
        response: Anthropic message response

    Returns:
        The input dict from the tool_use block

    Raises:
        RuntimeError: If no tool_use block found in response
    """
    try:
        tool_block = next(b for b in response.content if b.type == "tool_use")
    except StopIteration:
        raise RuntimeError("No tool_use block in response")

    return cast(dict[str, Any], tool_block.input)
