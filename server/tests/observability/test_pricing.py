"""Tests for model pricing estimates."""

import logging

import pytest

from observability.pricing import estimate_cost_usd


def test_sonnet_cost() -> None:
    # 1M in @ $3 + 1M out @ $15
    assert estimate_cost_usd("claude-sonnet-5", 1_000_000, 1_000_000) == 18.0


def test_small_call_cost() -> None:
    cost = estimate_cost_usd("claude-sonnet-5", 3318, 1102)
    assert abs(cost - (3318 * 3.0 + 1102 * 15.0) / 1_000_000) < 1e-9


def test_unknown_model_is_zero() -> None:
    assert estimate_cost_usd("some-future-model", 5000, 5000) == 0.0


def test_unknown_response_model_falls_back_to_known_requested_model() -> None:
    # Response echoes a dated snapshot id we haven't priced yet, but the
    # caller requested a model we do have pricing for — use that instead
    # of silently recording $0.
    cost = estimate_cost_usd(
        "claude-sonnet-5-20260315", 1_000_000, 1_000_000, fallback_model="claude-sonnet-5"
    )
    assert cost == 18.0


def test_unknown_response_and_fallback_model_is_zero_and_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING, logger="observability.pricing"):
        cost = estimate_cost_usd(
            "some-future-model", 5000, 5000, fallback_model="also-unknown-model"
        )
    assert cost == 0.0
    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert "some-future-model" in message
    assert "also-unknown-model" in message
