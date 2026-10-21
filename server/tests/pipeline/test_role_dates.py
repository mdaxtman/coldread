"""Role dates and order: facts from the career overview, kept in code.

Measured in resume-bench on 39 resumes from this pipeline's prompts: the
generator copied every role's dates from the career overview correctly, but
one draft listed the current role second. The resume screener, which did not
know today's date, flagged the current role's recent start as a future typo in
4 of 39, and refinement moved it back a year or two in exactly those four.
"""

from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from features import resume_generation
from pipeline.generator import order_roles
from pipeline.prompt_loader import load_prompt
from pipeline.refinement import _format_resume_for_screener, keep_role_dates, run_refinement

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def _role(company: str, title: str, dates: str) -> dict[str, Any]:
    return {"company": company, "title": title, "dates": dates, "projects": []}


CURRENT = _role("Globex", "Senior Engineer", "March 2025 – present")
PREVIOUS = _role("Initech", "Engineer II", "June 2019 – March 2025")
FIRST = _role("Springfield Labs", "Engineer I", "February 2016 – June 2019")


def _companies(data: dict[str, Any]) -> list[str]:
    return [role["company"] for role in data["experience"]]


def test_the_current_role_listed_second_is_put_first() -> None:
    data = {"experience": [PREVIOUS, CURRENT, FIRST], "skills": ["React"]}
    assert _companies(order_roles(data)) == ["Globex", "Initech", "Springfield Labs"]


def test_roles_already_in_order_are_unchanged() -> None:
    data = {"experience": [CURRENT, PREVIOUS, FIRST]}
    assert order_roles(data) == data


@pytest.mark.parametrize(
    ("newer", "older"),
    [
        ("2021–present", "2018 – 2021"),
        ("Sept. 2023 – Current", "Jan 2019 – Aug 2023"),
        ("2022", "2016 – 2019"),
        ("March 2024 – June 2024", "January 2024 – March 2024"),
    ],
)
def test_date_formats_order_by_end_then_start(newer: str, older: str) -> None:
    data = {"experience": [_role("Older", "Engineer", older), _role("Newer", "Engineer", newer)]}
    assert _companies(order_roles(data)) == ["Newer", "Older"]


def test_a_role_without_a_year_leaves_the_order_alone() -> None:
    data = {"experience": [PREVIOUS, _role("Globex", "Engineer", "Recent"), FIRST]}
    assert order_roles(data) == data


RESUME = {
    "summary": "Frontend engineer.",
    "experience": [
        {**CURRENT, "projects": [{"name": "Globex Scheduling", "bullets": ["Built it."]}]},
        PREVIOUS,
    ],
    "skills": ["React"],
}
DRAFT = _format_resume_for_screener(RESUME)


def test_a_date_refinement_moved_is_restored() -> None:
    refined = DRAFT.replace("March 2025 – present", "March 2023 – present")
    assert refined != DRAFT
    assert keep_role_dates(RESUME, refined) == DRAFT


def test_a_role_heading_in_another_layout_is_restored() -> None:
    refined = "### Globex — Senior Engineer (March 2024 – present)\n- Built it.\n"
    assert keep_role_dates(RESUME, refined) == (
        "### Globex — Senior Engineer (March 2025 – present)\n- Built it.\n"
    )


def test_a_project_line_naming_the_company_is_not_a_role() -> None:
    refined = DRAFT.replace("**Globex Scheduling**", "**Globex Scheduling** (2024 – 2025)")
    assert keep_role_dates(RESUME, refined) == refined


def test_a_reworded_title_is_left_alone() -> None:
    refined = DRAFT.replace(
        "**Senior Engineer** at Globex (March 2025", "**Staff Engineer** at Globex (March 2023"
    )
    assert keep_role_dates(RESUME, refined) == refined


def test_other_edits_are_untouched() -> None:
    refined = DRAFT.replace("Frontend engineer.", "Frontend engineer, tightened.")
    assert keep_role_dates(RESUME, refined) == refined


def test_refinement_returns_the_generators_dates() -> None:
    moved = DRAFT.replace("March 2025 – present", "March 2024 – present")
    with (
        patch("pipeline.refinement.load_prompt", return_value="System prompt"),
        patch("pipeline.refinement.call_model", return_value={"refined_content": moved}),
    ):
        result = run_refinement(RESUME, {}, "narratives", "jd", "user-1")
    assert result["refined_content"] == DRAFT


def test_the_pipeline_screens_and_refines_the_ordered_roles() -> None:
    unordered = {**RESUME, "experience": RESUME["experience"][::-1]}
    with (
        patch("features.resume_generation.job_descriptions.get_jd", return_value={"content": "jd"}),
        patch("features.resume_generation.narratives.list_narratives", return_value=[]),
        patch("features.resume_generation.resume_variants.get_latest_variant", return_value=None),
        patch("features.resume_generation.resume_variants.create_resume_variant", return_value={}),
        patch.object(resume_generation, "run_generator", return_value=unordered),
        patch.object(resume_generation, "run_screener", return_value={}) as screener,
        patch.object(
            resume_generation, "run_refinement", return_value={"refined_content": ""}
        ) as refine,
    ):
        resume_generation.run_resume_generation("jd-1", "user-1", {}, mode="full")
    screened = screener.call_args.args[1]
    assert screened.index("Globex") < screened.index("Initech")
    assert _companies(refine.call_args.args[0]) == ["Globex", "Initech"]


def test_load_prompt_fills_in_today() -> None:
    row = {"template": "Today's date is {today}.", "version": 1}
    with patch("pipeline.prompt_loader.prompts.get_active_prompt", return_value=row):
        assert (
            load_prompt("resume_screener", "user-1")
            == f"Today's date is {date.today().isoformat()}."
        )


@pytest.mark.parametrize("filename", ["resume_screener.md", "refinement.md"])
def test_the_stages_that_read_dates_are_told_today(filename: str) -> None:
    text = (_PROMPTS_DIR / filename).read_text()
    assert "Today's date is {today}." in text
    assert "a recent start date is not a typo" in text
