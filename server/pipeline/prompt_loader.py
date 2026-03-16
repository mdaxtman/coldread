"""Loads prompts from the database rather than hardcoding them.

Prompts are versioned in DB to allow iteration without redeployment.
"""

from db import prompts


def load_prompt(stage: str, user_id: str) -> str:
    row = prompts.get_active_prompt(stage, user_id)
    if row is None:
        raise ValueError(f"No active prompt found for stage: {stage!r}")
    return str(row["template"])
