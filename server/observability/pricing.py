"""Model pricing — cost estimation for observability records."""

# USD per million tokens. Update as models/prices change; historical
# model_calls rows keep the cost computed at record time.
PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-20250514": {"input_per_mtok": 3.0, "output_per_mtok": 15.0},
}


def estimate_cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    """Estimate USD cost of a model call. Unknown models cost 0.0."""
    prices = PRICING.get(model)
    if prices is None:
        return 0.0
    return (
        tokens_in * prices["input_per_mtok"] + tokens_out * prices["output_per_mtok"]
    ) / 1_000_000
