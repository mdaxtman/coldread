"""Model pricing — cost estimation for observability records."""

import logging

logger = logging.getLogger(__name__)

# USD per million tokens. Update as models/prices change; historical
# model_calls rows keep the cost computed at record time.
#
# claude-sonnet-5 has intro pricing of $2/$10 per MTok through 2026-08-31;
# we keep the durable $3/$15 sticker rate here, so estimates slightly
# overstate actual cost until intro pricing ends.
PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-5": {"input_per_mtok": 3.0, "output_per_mtok": 15.0},
}


def _cost(prices: dict[str, float], tokens_in: int, tokens_out: int) -> float:
    return (
        tokens_in * prices["input_per_mtok"] + tokens_out * prices["output_per_mtok"]
    ) / 1_000_000


def estimate_cost_usd(
    model: str,
    tokens_in: int,
    tokens_out: int,
    fallback_model: str | None = None,
) -> float:
    """Estimate USD cost of a model call.

    `model` is the response's echoed model id (ground truth) and is tried
    first. If the API returned an id we don't have pricing for yet — e.g. a
    dated snapshot — fall back to `fallback_model` (typically the id that
    was requested). If neither is priced, the cost is 0.0 and a warning is
    logged naming both ids so a silent $0 doesn't go unnoticed.
    """
    prices = PRICING.get(model)
    if prices is not None:
        return _cost(prices, tokens_in, tokens_out)

    if fallback_model is not None:
        prices = PRICING.get(fallback_model)
        if prices is not None:
            return _cost(prices, tokens_in, tokens_out)

    logger.warning(
        "no pricing found for response model=%r or requested fallback model=%r; "
        "recording cost as $0",
        model,
        fallback_model,
    )
    return 0.0
