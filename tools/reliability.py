"""Judge reliability: how much of an axis's spread is the document?

Re-scoring the same document repeatedly separates two situations the aggregate
cannot tell apart: a judge that fails to discriminate between documents, and
documents that genuinely do not differ. Both look like "all the scores are the
same" in a sweep.

ICC is between-document variance over total variance. Near 1 the axis measures
the document; near 0 it measures noise. An axis whose within-document variation
rivals its between-document variation cannot detect a prompt change however
large that change is -- so this is what to run BEFORE tuning a prompt, not
after being surprised by the result.

Reported as ICC(1,1), one-way random effects, which is the right model here:
each document is scored by k independent judge calls drawn from the same pool,
and no judge is shared across documents.

Input JSON, keyed axis -> document -> list of repeated scores:

    { "jd_alignment": { "doc_a": [8.0, 8.5, 8.0], "doc_b": [9.0, 9.0, 8.5] } }

Usage:
    python3 tools/reliability.py <observations.json>
"""

from __future__ import annotations

import json
import pathlib
import statistics as st
import sys


def icc1(groups: list[list[float]]) -> dict[str, float]:
    """One-way random effects ICC(1,1) plus the variance components behind it.

    Returns the raw between/within standard deviations alongside the ratio,
    because the ratio alone hides which term moved. An ICC can fall either
    because the judge got noisier or because the documents got more alike, and
    only the components distinguish those.
    """
    n = len(groups)
    k = len(groups[0])
    if any(len(g) != k for g in groups):
        raise ValueError("every document needs the same number of repeats")
    if n < 2 or k < 2:
        raise ValueError("need at least 2 documents and 2 repeats")

    means = [st.mean(g) for g in groups]
    grand = st.mean([x for g in groups for x in g])

    ms_between = k * sum((m - grand) ** 2 for m in means) / (n - 1)
    ms_within = sum((x - m) ** 2 for g, m in zip(groups, means) for x in g) / (
        n * (k - 1)
    )

    denom = ms_between + (k - 1) * ms_within
    icc = (ms_between - ms_within) / denom if denom else 0.0

    return {
        # sd of the per-document means: how much the documents actually differ
        "between_sd": st.stdev(means) if n > 1 else 0.0,
        # sqrt of mean square within: how much one document's score wanders
        "within_sd": ms_within**0.5,
        # ICC is defined on [0, 1]; the estimator can go negative when within
        # exceeds between, which means "no document-level signal", not "-0.3".
        "icc": max(0.0, icc),
        "icc_raw": icc,
        "n_documents": n,
        "k_repeats": k,
    }


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2

    data = json.loads(pathlib.Path(argv[0]).read_text())

    header = f"{'axis':<26}{'between sd':>12}{'within sd':>11}{'ICC':>8}"
    print(header)
    print("-" * len(header))

    rows = []
    for axis, by_doc in data.items():
        groups = list(by_doc.values())
        try:
            r = icc1(groups)
        except ValueError as exc:
            print(f"{axis:<26}{exc}")
            continue
        rows.append((axis, r))
        print(
            f"{axis:<26}{r['between_sd']:>12.2f}{r['within_sd']:>11.2f}{r['icc']:>8.2f}"
        )

    print()
    for axis, r in rows:
        if r["icc"] < 0.5:
            print(
                f"  {axis}: ICC {r['icc']:.2f} — within-document variation "
                f"({r['within_sd']:.2f}) rivals or exceeds between-document "
                f"({r['between_sd']:.2f}). This axis cannot detect a prompt "
                f"change; do not tune against it, and do not read a movement "
                f"in it as a result."
            )
    if rows:
        n, k = rows[0][1]["n_documents"], rows[0][1]["k_repeats"]
        print(f"\n  {n} documents x {k} repeats. ICC is sensitive to the range it is")
        print("  computed over, so a clustered corpus gives a lower bound.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
