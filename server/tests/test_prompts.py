"""Verify that active pipeline prompt files exist and are non-empty."""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def test_all_prompt_files_exist() -> None:
    for filename in ["fit_assessment.md", "generator.md", "resume_screener.md", "refinement.md"]:
        path = _PROMPTS_DIR / filename
        assert path.exists(), f"Missing prompt file: {path}"


def test_all_prompt_files_nonempty() -> None:
    for filename in ["fit_assessment.md", "generator.md", "resume_screener.md", "refinement.md"]:
        path = _PROMPTS_DIR / filename
        content = path.read_text().strip()
        assert len(content) > 100, f"Prompt file suspiciously short: {path}"


def test_seed_prompts_reads_from_files() -> None:
    """seed_prompts.py must expose a _read_prompt helper that reads from server/prompts/."""
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from seeds.seed_prompts import _read_prompt  # noqa: PLC0415

    content = _read_prompt("generator.md")
    assert len(content) > 100
    assert "resume" in content.lower()
