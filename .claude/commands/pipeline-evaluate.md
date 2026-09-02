Score and compare the pipeline and control resumes for job: $ARGUMENTS

## Precondition checks

Check these in order. Stop at the first failure.

1. Read `poc/jobs/$ARGUMENTS/jd.md`. If it does not exist: print "Create `poc/jobs/$ARGUMENTS/jd.md` first." and stop.
2. Use Bash to list `poc/jobs/$ARGUMENTS/runs/` sorted alphabetically descending; take the first result as the latest run directory. Save this name — it is `<latest>` everywhere below. If the directory does not exist or is empty: print "No run directory found. Run `/pipeline-stages-all $ARGUMENTS` first." and stop.
3. Read `poc/jobs/$ARGUMENTS/runs/<latest>/refined_resume.md`. If it does not exist: print "Run `/pipeline-stages-all $ARGUMENTS` or `/pipeline-refine $ARGUMENTS` first." and stop.
4. Read `poc/jobs/$ARGUMENTS/runs/<latest>/control_resume.md`. If it does not exist: print "Run `/pipeline-control $ARGUMENTS` first." and stop.
5. Read `poc/config.json`. If it does not exist: print "Run `/pipeline-setup` first." and stop.

You now have the JD, both resumes, and the config in your context. Do not read `poc/input/narratives.md` yet — Phase 1 must be scored by isolated sub-agents with no knowledge of the candidate's background.

## Phase 1 — Cold Read (two isolated sub-agents, run in parallel)

Spawn two sub-agents in parallel using the Agent tool — one scores the pipeline resume, one scores the control resume. Each sub-agent receives only the JD and its single assigned resume; neither sees the other resume. This prevents comparative bias: each resume is scored against the JD on an absolute scale, not relative to the other.

Use Bash `date +%Y-%m-%d` and substitute the result for `{TODAY}`. Without it a scorer reads a
current start date as a future typo and penalises the document: this happened in 58% of a
76-document corpus, one scorer proposing the date was "possibly meant to be 2024".

Both sub-agents use the same prompt template below. For each, substitute `{JD}` with the full text of the JD and `{RESUME}` with the full text of its assigned resume (`refined_resume.md` for the pipeline sub-agent, `control_resume.md` for the control sub-agent).

---
You are a recruiter scoring a resume against a job description.

Today's date is {TODAY}. Employment dates on the resume are current as of that date — a recent
start date is not a typo and must not be treated as an error.

**ISOLATION REQUIREMENT: You have been given all the content you need inline below. Do not use Read, Bash, Glob, or any file-access tools. Do not read any files from disk. Your only inputs are the job description and the single resume provided here.**

## Job Description

{JD}

## Resume

{RESUME}

## Task

Score this resume against the job description. Score exactly as a recruiter would seeing this resume for the first time, with no other resumes for comparison — this is the only resume you are evaluating.

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

**Criterion 3 — Hire Intent (0–10)**
Cold-read gut check: after reading only this resume and the JD, would you move this candidate to a phone screen? Score this independently — do not let JD alignment or readability scores influence it. Ask: does this resume create a compelling, specific narrative for this candidate in this role? Is it memorable? Does it make you want to know more about this person?
- 9–10: Strong instinct to call; compelling, specific, and memorable — this person clearly wants this job and makes a credible case for it
- 7–8: Would likely follow up; solid but not immediately exciting
- 4–6: Maybe; some strengths but feels generic, forgettable, or unconvincing
- 0–3: Would pass; does not create confidence or interest in this candidate

Return a JSON object with this exact structure and nothing else:

```json
{
  "jd_alignment": 0.0,
  "recruiter_readability": 0.0,
  "hire_intent": 0.0,
  "notes": {
    "jd_alignment": "key reasons for this score",
    "recruiter_readability": "key reasons for this score",
    "hire_intent": "what made this compelling or forgettable as a cold read"
  }
}
```
---

Collect the JSON returned by each sub-agent. The pipeline sub-agent result is the pipeline Phase 1 scores; the control sub-agent result is the control Phase 1 scores.

## Phase 2 — Authenticity (narratives required)

Check that `poc/input/narratives.md` exists. If it does not: print "Run `/pipeline-setup` first." and stop.

**Do not read it yourself, and do not score this phase yourself.** By this point your context
holds both resumes, the fit report, and the arm labels — you cannot score either document
blind to which arm produced it. Spawn one sub-agent per resume, in parallel, each receiving
the narratives and its single assigned resume inline, with the same no-file-tools prohibition
used in Phase 1 and no indication of which arm it came from.

This is the phase that skewed every earlier run. Scoring it in the orchestrator produced an
authenticity gap of +1.78 between arms; re-scoring the identical documents with an isolated,
length-normalised judge produced -0.20.

Score each resume independently against the narratives. Authenticity is a grounded fact-check — every claim must trace back to the narratives. Score one resume fully before moving to the other.

**Criterion 4 — Authenticity (0–10)**
Every claim must be traceable to `poc/input/narratives.md`.
First count `claims_checked`: the number of discrete assertions you evaluated — roughly one
per bullet, plus assertions in the summary and any scope or seniority statement. Count a
skills list as one claim, not one per token.

Then count `untraceable` (no support in the narratives) and `overstatements` (supported in
kind but not in degree).

Score: `10 x (1 - (2 x untraceable + 1 x overstatements) / (2 x claims_checked))`, floored at 0.

The normalisation is the point. A flat "start at 10, deduct 2 each" penalises a document for
having more claims to check, which is a proxy for length rather than for honesty. Measured on
this corpus: control resumes ran 29% longer than pipeline resumes, and under the flat rule a
roughly 95%-accurate control accumulated -11 and floored at 0. That single axis supplied 76%
of the pipeline's apparent advantage. Report `claims_checked`, `untraceable`, and
`overstatements` alongside the score so the raw counts survive.

When assessing overstatement, apply the interview test: would this claim cause a problem if the interviewer asked about it directly? Terminology substitutions where the underlying capability is the same do not overstate — e.g., "Redux" when the resume shows RTK (RTK is Redux), or "SpringBoot" when the experience is Spring MVC (same programming model, same annotations, configuration wrapper differs). A substitution *does* overstate if the candidate would be exposed in an interview — e.g., claiming Zustand experience based on Jotai (different APIs, different mental models despite both being atomic state managers).

## Scoring

Use the weights from `poc/config.json`. The weight keys are `jd_alignment`, `recruiter_readability`, and `authenticity`. Weights sum to 1.0.

`composite = (jd_alignment × weights.jd_alignment) + (recruiter_readability × weights.recruiter_readability) + (authenticity × weights.authenticity)`

**Hire Intent is NOT part of the composite.** It is a standalone signal reported separately. The composite answers "how well does this resume perform on the rubric?" Hire Intent answers "would I actually hire this person?"

## Output

Determine `run` from the latest run directory name (the directory basename, e.g. `2026-06-04`).

`delta` = pipeline.composite − control.composite (signed; positive means pipeline won)

`abs_delta` = absolute value of `delta` (used in the print line below)

`winner` (composite-based):
- `"pipeline"` if delta > 0.1
- `"control"` if delta < −0.1
- `"tie"` if |delta| ≤ 0.1

`hire_intent_winner`:
- `"pipeline"` if pipeline.hire_intent > control.hire_intent + 0.5
- `"control"` if control.hire_intent > pipeline.hire_intent + 0.5
- `"tie"` if scores are within 0.5 of each other

`rubric_version` is **2**. Emit it verbatim.

Reports lacking this field were produced by v1, which differed in three ways that all moved
scores: the control resume carried a `# Control Resume` title, so the "blind" scorer could read
the arm off line one; authenticity deductions were not normalised against claim count, so the
longer arm was penalised for length rather than for dishonesty; and authenticity was scored by
the orchestrator holding both documents rather than by an isolated judge. Re-scoring the same
50 documents under v2 moved the authenticity gap from +1.78 to -0.20 and the composite gap from
+0.93 to +0.14. **v1 and v2 scores are not comparable.**

Bump to 3 if any scoring rule, weight, or isolation property changes again. The number is
worthless if it tracks edits to prose; it exists to mark runs whose numbers mean different
things.

Write `poc/jobs/$ARGUMENTS/runs/<latest>/evaluation_report.json`:

```json
{
  "run": "YYYY-MM-DD",
  "job": "$ARGUMENTS",
  "rubric_version": 2,
  "pipeline": {
    "jd_alignment": 0.0,
    "recruiter_readability": 0.0,
    "hire_intent": 0.0,
    "authenticity": 0.0,
    "claims_checked": 0,
    "untraceable": 0,
    "overstatements": 0,
    "composite": 0.0,
    "notes": {
      "jd_alignment": "string — key reasons for this score",
      "recruiter_readability": "string — key reasons for this score",
      "hire_intent": "string — what made this compelling or forgettable as a cold read",
      "authenticity": "string — any unsupported claims found, or 'No issues'"
    }
  },
  "control": {
    "jd_alignment": 0.0,
    "recruiter_readability": 0.0,
    "hire_intent": 0.0,
    "authenticity": 0.0,
    "claims_checked": 0,
    "untraceable": 0,
    "overstatements": 0,
    "composite": 0.0,
    "notes": {
      "jd_alignment": "string",
      "recruiter_readability": "string",
      "hire_intent": "string",
      "authenticity": "string"
    }
  },
  "winner": "<pipeline|control|tie>",
  "delta": 0.0,
  "hire_intent_winner": "<pipeline|control|tie>"
}
```

Print:
```
Evaluation complete.
  Pipeline:  <composite> composite (alignment=<jd_alignment>, readability=<recruiter_readability>, authenticity=<authenticity>) | hire intent: <hire_intent>
  Control:   <composite> composite (alignment=<jd_alignment>, readability=<recruiter_readability>, authenticity=<authenticity>) | hire intent: <hire_intent>
  Rubric winner:      <winner> (<abs_delta> points)
  Hire intent winner: <hire_intent_winner>
```
