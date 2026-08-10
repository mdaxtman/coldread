"""Guard against drift between server/prompts/*.md and the active `prompts` rows.

At runtime `prompt_loader.load_prompt` reads the DB, never these files, so the
files are documentation. When they disagree with the active row, it fails quietly
in two ways:

  - Code review reads a prompt that is not the one in production.
  - `seeds/seed_prompts.py` rebuilds rows via `_read_prompt()`, so re-seeding a
    database publishes whatever the file happens to hold under whichever version
    label the seed assigns.

Both directions have happened in this repo: files behind the DB (generator was a
full version behind; refinement two) and files ahead of it (resume_screener
carried unpublished edits for two months).

These tests need live Supabase credentials and skip without them, so forks and
credential-less CI runs are unaffected.
"""

import difflib
import os
from pathlib import Path
from typing import Any, cast

import pytest
from dotenv import load_dotenv

# skipif below is evaluated at collection time, before any test body imports
# config — so .env has to be loaded here or the check silently skips locally.
load_dotenv()

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# `prompts.stage` value -> the file that documents it. These names differ:
# the fit-assessment prompt is stored under stage "screener".
STAGE_FILES = {
    "generator": "generator.md",
    "refinement": "refinement.md",
    "screener": "fit_assessment.md",
    "resume_screener": "resume_screener.md",
}

requires_supabase = pytest.mark.skipif(
    not (os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY")),
    reason="needs live Supabase credentials",
)


@requires_supabase
@pytest.mark.parametrize("stage,filename", sorted(STAGE_FILES.items()))
def test_prompt_file_matches_active_db_row(stage: str, filename: str) -> None:
    """The documented prompt must match the one actually being served."""
    from config import DEFAULT_USER_ID
    from db.prompts import get_active_prompt

    row = get_active_prompt(stage, DEFAULT_USER_ID)
    assert row is not None, (
        f"No active prompt for stage {stage!r} — load_prompt() raises at runtime "
        f"and the pipeline fails at that stage."
    )

    path = _PROMPTS_DIR / filename
    assert path.exists(), f"{path} is missing, but stage {stage!r} is active in the DB"

    file_text = path.read_text().strip()
    db_text = str(row["template"]).strip()
    if file_text == db_text:
        return

    diff = "\n".join(
        difflib.unified_diff(
            db_text.splitlines(),
            file_text.splitlines(),
            fromfile=f"DB (active, v{row['version']})",
            tofile=f"server/prompts/{filename}",
            lineterm="",
            n=1,
        )
    )
    direction = (
        "the file has edits that were never published"
        if len(file_text) > len(db_text)
        else "the file is behind what is running"
    )
    pytest.fail(
        f"{stage!r} prompt drift — {direction}.\n"
        f"Active row: v{row['version']} {row['name']!r} ({len(db_text)} chars); "
        f"file: {len(file_text)} chars.\n"
        f"Publish a new version, or sync the file from the active row.\n\n{diff}"
    )


@requires_supabase
@pytest.mark.parametrize("stage", sorted(STAGE_FILES))
def test_exactly_one_active_prompt_per_stage(stage: str) -> None:
    """Two active rows makes the served prompt depend on version ordering; zero raises."""
    from config import DEFAULT_USER_ID
    from db.client import get_client

    response = (
        get_client()
        .table("prompts")
        .select("version, name")
        .eq("user_id", DEFAULT_USER_ID)
        .eq("stage", stage)
        .eq("active", True)
        .execute()
    )
    rows = cast(list[dict[str, Any]], response.data)

    versions = sorted(int(r["version"]) for r in rows)
    assert len(rows) == 1, (
        f"stage {stage!r} has {len(rows)} active prompts (versions {versions}); "
        f"expected exactly 1. Fix with: "
        f"update prompts set active = (version = <n>) where stage = '{stage}';"
    )
