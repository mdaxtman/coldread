Score and compare the pipeline and control resumes for job: $ARGUMENTS

## Precondition checks

Check these in order. Stop at the first failure.

1. Read `poc/input/narratives.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
2. Read `poc/jobs/$ARGUMENTS/jd.md`. If it does not exist: print "Create `poc/jobs/$ARGUMENTS/jd.md` first." and stop.
3. Use Bash to list `poc/jobs/$ARGUMENTS/runs/` sorted alphabetically descending; take the first result as the latest run directory. Save this name — it is `<latest>` everywhere below. If the directory does not exist or is empty: print "No run directory found. Run `/pipeline-run $ARGUMENTS` first." and stop.
4. Read `poc/jobs/$ARGUMENTS/runs/<latest>/refined_resume.md`. If it does not exist: print "Run `/pipeline-run $ARGUMENTS` or `/pipeline-refine $ARGUMENTS` first." and stop.
5. Read `poc/jobs/$ARGUMENTS/runs/<latest>/control_resume.md`. If it does not exist: print "Run `/resume-control $ARGUMENTS` first." and stop.
6. Read `poc/config.json`. If it does not exist: print "Run `/pipeline-setup` first." and stop.

## Evaluation

You now have both resumes and the source material. Score each resume **independently** — evaluate one fully before looking at the other.

Use the weights from `poc/config.json`.

**Criterion 1 — JD Alignment (0–10)**
How well does the resume address the key requirements of the job description? Does it use the JD's terminology?
- 9–10: Addresses all key requirements with correct terminology
- 7–8: Addresses most requirements, minor gaps or terminology issues
- 4–6: Addresses some requirements, notable omissions
- 0–3: Misses most key requirements

**Criterion 2 — Recruiter Readability (0–10)**
Would a recruiter spend more than 10 seconds on this? Is it scannable, structured, concise?
- 9–10: Immediately scannable, tight bullets, strong opening, logical structure
- 7–8: Clear and readable, minor structural issues
- 4–6: Readable but verbose, inconsistent structure, or weak opening
- 0–3: Hard to scan, poor structure, or unclear bullets

**Criterion 3 — Authenticity (0–10)**
Every claim must be traceable to `poc/input/narratives.md`.
- Start at 10
- Deduct 2 points per claim not traceable to the narratives
- Deduct 1 point per claim that overstates what the narratives support
- Minimum score: 0

**Composite score:**
`composite = (jd_alignment × weights.jd_alignment) + (recruiter_readability × weights.recruiter_readability) + (authenticity × weights.authenticity)`

The weight keys in `poc/config.json` are `jd_alignment`, `recruiter_readability`, and `authenticity` (as created by `/pipeline-setup`). Weights sum to 1.0, so the composite is on the same 0–10 scale as the individual scores.

## Output

Determine `run` from the latest run directory name (the directory basename, e.g. `2026-06-04`).

`delta` = pipeline.composite − control.composite (signed; positive means pipeline won)

`abs_delta` = absolute value of `delta` (used in the print line below)

`winner`:
- `"pipeline"` if delta > 0.1
- `"control"` if delta < −0.1
- `"tie"` if |delta| ≤ 0.1

Write `poc/jobs/$ARGUMENTS/runs/<latest>/evaluation_report.json`:

```json
{
  "run": "YYYY-MM-DD",
  "job": "$ARGUMENTS",
  "pipeline": {
    "jd_alignment": 0.0,
    "recruiter_readability": 0.0,
    "authenticity": 0.0,
    "composite": 0.0,
    "notes": {
      "jd_alignment": "string — key reasons for this score",
      "recruiter_readability": "string — key reasons for this score",
      "authenticity": "string — any unsupported claims found, or 'No issues'"
    }
  },
  "control": {
    "jd_alignment": 0.0,
    "recruiter_readability": 0.0,
    "authenticity": 0.0,
    "composite": 0.0,
    "notes": {
      "jd_alignment": "string",
      "recruiter_readability": "string",
      "authenticity": "string"
    }
  },
  "winner": "<pipeline|control|tie>",
  "delta": 0.0
}
```

Print:
```
Evaluation complete.
  Pipeline:  <composite> (alignment=<jd_alignment>, readability=<recruiter_readability>, authenticity=<authenticity>)
  Control:   <composite> (alignment=<jd_alignment>, readability=<recruiter_readability>, authenticity=<authenticity>)
  Winner: <winner> (<abs_delta> points)
```
