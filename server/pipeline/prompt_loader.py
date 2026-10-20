"""Loads prompts from the database rather than hardcoding them.

Prompts are versioned in DB to allow iteration without redeployment.
"""

import logging
from datetime import date

from db import prompts

logger = logging.getLogger(__name__)


def load_prompt(stage: str, user_id: str) -> str:
    """The active prompt for a stage, with today's date substituted for `{today}`.

    The date is filled in when the prompt is served, not when it is seeded, so
    it never goes stale. Without it the resume screener reads a recent start
    date as a future one: in resume-bench it called the current role's start a
    likely typo in 4 of 39 resumes, and refinement moved the date back a year
    or two in exactly those four.
    """
    row = prompts.get_active_prompt(stage, user_id)
    if row is None:
        logger.debug("No prompt found for stage=%r, user_id=%r", stage, user_id)
        raise ValueError(f"No active prompt found for stage: {stage!r}")
    logger.debug("Loaded prompt for stage=%r, version=%s", stage, row.get("version"))
    return str(row["template"]).replace("{today}", date.today().isoformat())
