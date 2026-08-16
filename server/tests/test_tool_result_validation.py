"""Tool `input_schema` is advisory, not enforced.

The API guarantees a well-formed tool call, not that nested structures match the
declared types. A real fit run returned `terminology` as a list of bare strings
even though the schema declares its items as objects with three required fields,
and `term.get("confidence", 0)` raised AttributeError on a str after the model
call had already succeeded and been paid for.

Every stage reads nested tool-result items the same way — `match.get(...)`,
`gap.get(...)`, `term.get(...)` — so the guard belongs at the boundary.
"""

from typing import Any
from unittest.mock import patch

from pipeline import fit_assessment
from pipeline.anthropic_utils import dict_items


class TestDictItems:
    def test_drops_scalars_where_objects_were_declared(self) -> None:
        assert dict_items(["React ↔ React", {"my_term": "RTK", "confidence": 0.9}]) == [
            {"my_term": "RTK", "confidence": 0.9}
        ]

    def test_keeps_every_dict(self) -> None:
        items = [{"a": 1}, {"b": 2}]
        assert dict_items(items) == items

    def test_returns_empty_list_when_field_is_missing(self) -> None:
        assert dict_items(None) == []

    def test_returns_empty_list_when_field_is_not_a_list(self) -> None:
        # The model can collapse an array field to a single scalar or object.
        assert dict_items("terminology") == []
        assert dict_items({"my_term": "RTK"}) == []


class TestFitAssessmentSurvivesMalformedToolResult:
    """Regression for the 2026-08-15 failure: model call ok, post-processing crash."""

    def _run(self, model_result: dict[str, Any]) -> dict[str, Any]:
        with (
            patch.object(fit_assessment, "call_model", return_value=model_result),
            patch.object(fit_assessment, "load_prompt", return_value="system prompt"),
        ):
            return fit_assessment.run_fit_assessment("jd", "narratives", "user-1")

    def test_string_terminology_items_are_dropped_not_raised(self) -> None:
        result = self._run(
            {
                "fit_level": "moderate",
                "terminology": [
                    "React ↔ React",
                    {"my_term": "RTK Query", "jd_term": "server state", "confidence": 0.9},
                ],
            }
        )

        assert result["terminology"] == [
            {"my_term": "RTK Query", "jd_term": "server state", "confidence": 0.9}
        ]

    def test_low_confidence_filtering_still_applies(self) -> None:
        result = self._run(
            {
                "terminology": [
                    {"my_term": "a", "jd_term": "b", "confidence": 0.9},
                    {"my_term": "c", "jd_term": "d", "confidence": 0.4},
                ]
            }
        )

        assert [t["my_term"] for t in result["terminology"]] == ["a"]

    def test_item_missing_confidence_is_dropped_not_raised(self) -> None:
        result = self._run({"terminology": [{"my_term": "a", "jd_term": "b"}]})

        assert result["terminology"] == []


class TestSiblingCallSites:
    """The same unchecked pattern exists wherever a stage reads tool-result items."""

    def test_extract_keywords_skips_scalar_matches_and_gaps(self) -> None:
        from pipeline.fit_assessment_stage import _extract_keywords

        coverage = _extract_keywords(
            ["React expertise", {"requirement": "TypeScript"}],
            ["Bun and Deno", {"requirement": "Evals"}],
        )

        assert coverage == {"typescript": True, "evals": False}

    def test_format_fit_report_skips_scalar_matches_and_gaps(self) -> None:
        from pipeline.generator import _format_fit_report

        rendered = _format_fit_report(
            {
                "matches": ["React expertise", {"requirement": "TypeScript"}],
                "gaps": ["Bun and Deno", {"requirement": "Evals", "type": "hard"}],
            }
        )

        assert "TypeScript" in rendered
        assert "Evals" in rendered
