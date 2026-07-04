"""Loads prompts from the database rather than hardcoding them.

Prompts are versioned in DB to allow iteration without redeployment.
"""

import logging

from db import prompts

logger = logging.getLogger(__name__)


def load_prompt(stage: str, user_id: str) -> str:
    row = prompts.get_active_prompt(stage, user_id)
    if row is None:
        logger.debug("No prompt found for stage=%r, user_id=%r", stage, user_id)
        raise ValueError(f"No active prompt found for stage: {stage!r}")
    logger.debug("Loaded prompt for stage=%r, version=%s", stage, row.get("version"))
    return str(row["template"])
