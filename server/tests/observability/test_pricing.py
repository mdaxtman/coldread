"""Tests for model pricing estimates."""

from observability.pricing import estimate_cost_usd


def test_sonnet_cost() -> None:
    # 1M in @ $3 + 1M out @ $15
    assert estimate_cost_usd("claude-sonnet-4-20250514", 1_000_000, 1_000_000) == 18.0


def test_small_call_cost() -> None:
    cost = estimate_cost_usd("claude-sonnet-4-20250514", 3318, 1102)
    assert abs(cost - (3318 * 3.0 + 1102 * 15.0) / 1_000_000) < 1e-9


def test_unknown_model_is_zero() -> None:
    assert estimate_cost_usd("some-future-model", 5000, 5000) == 0.0
