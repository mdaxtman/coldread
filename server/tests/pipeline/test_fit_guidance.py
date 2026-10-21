"""What the generator is told about the fit report.

Since the fit stage began producing cultural signals and a product connection
(#31/#32), the generator prompt has had sections telling it how to use both —
but `_format_fit_report` never forwarded either, so the generator was instructed
to act on inputs it never received. Found by resume-bench, which shares this
code. Nothing failed: a missing section reads to the model as an assessment that
found none.

The structural test below is the guard against that recurring. Every field the
fit schema defines must either reach the generator or be excluded by name here,
so a new fit field is forwarded or deliberately withheld — never dropped by
omission.
"""

from pipeline.fit_assessment import _FIT_REPORT_SCHEMA
from pipeline.generator import _format_fit_report

SIGNALS = [
    {
        "quality": "0-to-1 ownership",
        "jd_signal": "you thrive with ambiguity",
        "evidence_hint": "look for features built from scratch",
    }
]
CONNECTION = "Acme Flow parallels the target's notebook execution surface."

# Scores and the fit stage's own reasoning are its verdict on the candidate, not
# guidance for writing about them. The generator prompt names none of them.
NOT_FORWARDED = {"fit_level", "overall_score", "semantic_score", "reasoning"}

SENTINELS: dict[str, object] = {
    "matches": [{"requirement": "SENTINEL-matches", "priority": "required", "notes": ""}],
    "gaps": [{"requirement": "SENTINEL-gaps", "type": "soft", "notes": ""}],
    "terminology": [{"my_term": "SENTINEL-terminology", "jd_term": "x", "confidence": 0.9}],
    "cultural_signals": [
        {"quality": "SENTINEL-cultural_signals", "jd_signal": "x", "evidence_hint": "x"}
    ],
    "product_connection": "SENTINEL-product_connection",
}


def test_every_fit_field_is_forwarded_or_excluded_by_name() -> None:
    fields = set(_FIT_REPORT_SCHEMA["properties"])
    unaccounted = fields - NOT_FORWARDED - set(SENTINELS)
    assert not unaccounted, f"fit fields with no forwarding decision: {unaccounted}"
    for name, value in SENTINELS.items():
        assert f"SENTINEL-{name}" in _format_fit_report({name: value}), f"{name} is dropped"


def test_cultural_signals_carry_all_three_parts() -> None:
    out = _format_fit_report({"cultural_signals": SIGNALS})
    assert "CULTURAL SIGNALS" in out
    for part in SIGNALS[0].values():
        assert part in out


def test_product_connection_is_labelled_as_the_prompt_names_it() -> None:
    """The generator prompt says "if `product_connection` is present in the fit
    assessment"; the label must let it find the thing it is told to look for."""
    out = _format_fit_report({"product_connection": CONNECTION})
    assert "product_connection" in out and CONNECTION in out


def test_an_absent_product_connection_says_nothing() -> None:
    """The prompt has a fallback for absence. A placeholder line would read as
    presence and trigger the wrong branch."""
    for absent in (None, "", "   "):
        assert "product_connection" not in _format_fit_report({"product_connection": absent})
