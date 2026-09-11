"""Literal keyword coverage for the resume pipeline's two arms.

Every other axis in the evaluation is a model's judgement. This one is
arithmetic: a term appears in a document or it does not, and the answer is
identical every time it is computed. That is the whole point of the axis, so
the matching lives here as a pure function rather than in a judge prompt --
asking a model to decide whether a term is "present" would reintroduce exactly
the variance this measurement exists to avoid.

Terms are extracted once per posting by a call that sees only the posting, and
cached in `poc/jobs/<slug>/keywords.json`. Both arms are then matched against
that one identical list. This is what makes the *delta* trustworthy. The
absolute level is not a finding: it is bounded by extraction quality, and terms
like a job title are unmatchable for either arm.

Usage:
    python3 tools/keyword_coverage.py <job-slug> [<run-dir-name> ...]

With no run directories, every run under the slug is scored.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

JOBS = pathlib.Path("poc/jobs")

# Documents scored per arm. The pipeline arm is judged on its refined output,
# which is the document the cold-read and authenticity judges also see.
ARM_FILES = {"pipeline": "refined_resume.md", "control": "control_resume.md"}


def normalise(text: str) -> str:
    """Case-fold and collapse whitespace so a term spanning a line break matches.

    Markdown wraps at arbitrary columns, so "server-state caching" can arrive
    with a newline in the middle of it. Collapsing first means the matcher sees
    the prose a recruiter's search would see, not the file's line breaks.
    """
    return re.sub(r"\s+", " ", text).casefold()


# Inflections allowed on a term's final token: "mentor" matches "mentored" and
# "mentorship", "platform" matches "platforms". This is a fixed rule applied
# uniformly to every term, so the matcher stays deterministic -- the same
# document and list give the same answer every time. It exists because the
# mechanism being proxied is whether a document surfaces in a recruiter's
# search over parsed records, and those indexes stem. Without it, extraction
# has to guess which inflection a resume happened to use, which is a judgement
# call this axis is specifically built to avoid.
SUFFIXES = r"(?:s|es|ed|d|ing|ship|ments?)?"

# Proper nouns take a plural at most. Without this split, the verb inflections
# make "React" match "reacted" -- harmless to the delta, since neither arm's
# prose contains it, but wrong, and the kind of wrong that erodes trust in a
# number whose only virtue is being exactly reproducible. A term carrying any
# uppercase letter is treated as a name (React, TypeScript, Heroku, LLMs); an
# all-lowercase term is treated as a capability phrase and inflects freely.
# Extraction is instructed to capitalise names and lowercase phrases, so this
# reads a distinction the list already carries rather than guessing at one.
PROPER_SUFFIXES = r"(?:s)?"


def term_pattern(term: str) -> re.Pattern[str]:
    """Build a whole-token matcher for one term, tolerant of final inflection.

    Takes the term in its ORIGINAL casing, because casing is what distinguishes
    a proper noun from a capability phrase, and compiles case-insensitively so
    matching itself stays case-blind.

    `\\b` is only meaningful next to a word character, so a term that begins or
    ends with punctuation (C++, .NET) gets an unanchored edge on that side
    rather than a boundary that can never match. Internal whitespace is allowed
    to be any run of whitespace, for the same wrapping reason as `normalise`.
    """
    tokens = term.split()
    left = r"\b" if re.match(r"\w", term) else ""
    if not re.search(r"\w$", term):
        return re.compile(left + r"\s+".join(re.escape(t) for t in tokens), re.IGNORECASE)

    if any(c.isupper() for c in term):
        suffix = PROPER_SUFFIXES
    else:
        suffix = SUFFIXES
        # An extracted term may be plural where the document is singular
        # ("reusable components" vs "a reusable component package"). Suffixes
        # can add an inflection but not remove one, so strip a trailing plural
        # off the final token first and let SUFFIXES put it back optionally.
        # Guarded on length and on "ss" so "business" and "less" survive.
        last = tokens[-1]
        if len(last) >= 4 and last.endswith("s") and not last.endswith("ss"):
            tokens = tokens[:-1] + [last[:-1]]

    body = r"\s+".join(re.escape(t) for t in tokens)
    return re.compile(left + body + suffix + r"\b", re.IGNORECASE)


def coverage(terms: list[str], text: str) -> dict[str, bool]:
    """Map each term to whether it appears in the document. Order preserved."""
    haystack = re.sub(r"\s+", " ", text)
    return {t: bool(term_pattern(t).search(haystack)) for t in terms}


def score_run(slug: str, run: str, terms: list[str]) -> dict:
    run_dir = JOBS / slug / "runs" / run
    result: dict = {"run": run, "terms_total": len(terms), "arms": {}}

    for arm, filename in ARM_FILES.items():
        path = run_dir / filename
        if not path.exists():
            result["arms"][arm] = {"error": f"{filename} not found"}
            continue
        hits = coverage(terms, path.read_text())
        covered = [t for t, ok in hits.items() if ok]
        result["arms"][arm] = {
            "covered": len(covered),
            "total": len(terms),
            "pct": round(100.0 * len(covered) / len(terms), 1) if terms else 0.0,
            "matched": covered,
            "missed": [t for t, ok in hits.items() if not ok],
        }

    arms = result["arms"]
    if all("pct" in arms.get(a, {}) for a in ARM_FILES):
        result["delta_pp"] = round(arms["pipeline"]["pct"] - arms["control"]["pct"], 1)
    return result


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2

    slug, runs = argv[0], argv[1:]
    keywords_path = JOBS / slug / "keywords.json"
    if not keywords_path.exists():
        print(f"No {keywords_path}. Extract terms for this posting first.")
        return 1

    terms = json.loads(keywords_path.read_text())["terms"]
    if not runs:
        runs = sorted(p.name for p in (JOBS / slug / "runs").iterdir() if p.is_dir())

    results = [score_run(slug, r, terms) for r in runs]

    print(f"{slug} — {len(terms)} terms extracted from the posting\n")
    header = f"{'run':<16}{'pipeline':>18}{'control':>18}{'delta':>10}"
    print(header)
    print("-" * len(header))
    for res in results:
        arms = res["arms"]
        if "delta_pp" not in res:
            missing = [f"{a}: {v['error']}" for a, v in arms.items() if "error" in v]
            print(f"{res['run']:<16}{'; '.join(missing)}")
            continue
        p, c = arms["pipeline"], arms["control"]
        print(
            f"{res['run']:<16}"
            f"{p['covered']:>4}/{p['total']:<3}{p['pct']:>7.1f}%"
            f"{c['covered']:>7}/{c['total']:<3}{c['pct']:>7.1f}%"
            f"{res['delta_pp']:>+9.1f}pp"
        )

    for res in results:
        if "delta_pp" not in res:
            continue
        both = [
            t
            for t in res["arms"]["pipeline"]["missed"]
            if t in res["arms"]["control"]["missed"]
        ]
        print(f"\n{res['run']} — missed by BOTH arms ({len(both)}):")
        for t in both:
            print(f"    {t}")
        only_c = [
            t
            for t in res["arms"]["pipeline"]["missed"]
            if t not in res["arms"]["control"]["missed"]
        ]
        only_p = [
            t
            for t in res["arms"]["control"]["missed"]
            if t not in res["arms"]["pipeline"]["missed"]
        ]
        print(f"{res['run']} — pipeline only missed ({len(only_c)}): {only_c}")
        print(f"{res['run']} — control only missed ({len(only_p)}): {only_p}")

    out = JOBS / slug / "runs" / "keyword_coverage.json"
    out.write_text(json.dumps({"slug": slug, "results": results}, indent=2) + "\n")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
