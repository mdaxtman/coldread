Run the full resume pipeline for job: $ARGUMENTS

## Precondition checks

1. Read `poc/input/narratives.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
2. Read `poc/jobs/$ARGUMENTS/jd.md`. If it does not exist: print "Create `poc/jobs/$ARGUMENTS/jd.md` with the job description first." and stop.
3. Read `poc/prompts/fit_assessment.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
4. Read `poc/prompts/generator.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
5. Read `poc/prompts/resume_screener.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
6. Read `poc/prompts/refinement.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.

## Create run directory

Use Bash to get today's date in YYYY-MM-DD format: `date +%Y-%m-%d`

List directories under `poc/jobs/$ARGUMENTS/runs/` that begin with today's date. If none exist, the run directory name is `YYYY-MM-DD`. If `YYYY-MM-DD` already exists, try `YYYY-MM-DD-2`, then `YYYY-MM-DD-3`, and so on until an unused name is found.

Create the run directory: `poc/jobs/$ARGUMENTS/runs/<run-dir-name>/`

## Stage 1 — Fit Assessment

Read:
- `poc/prompts/fit_assessment.md` — analysis framework
- `poc/input/narratives.md` — candidate background
- `poc/jobs/$ARGUMENTS/jd.md` — job description

Apply the framework from `poc/prompts/fit_assessment.md` to evaluate fit. Produce JSON matching this schema:

```json
{
  "fit_level": "<strong|moderate|borderline|poor>",
  "matches": [{ "requirement": "string", "priority": "<required|preferred|implied>", "notes": "string" }],
  "gaps": [{ "requirement": "string", "type": "<hard|soft>", "notes": "string" }],
  "terminology": [{ "my_term": "string", "jd_term": "string", "confidence": 0.0 }],
  "reasoning": "string"
}
```

Only include terminology mappings with confidence ≥ 0.8. Write to `poc/jobs/$ARGUMENTS/runs/<run-dir-name>/fit_assessment.json`.

Print: `[1/4] Fit assessment → <fit_level>, <matches count> matches, <hard count> hard gaps, <soft count> soft gaps`

## Stage 2 — Resume Generation

Read:
- `poc/prompts/generator.md` — generation framework
- `poc/input/narratives.md` — source of truth; every claim must trace here
- `poc/jobs/$ARGUMENTS/jd.md` — for role title, company name, and targeted emphasis
- `fit_assessment.json` just written

Apply the framework from `poc/prompts/generator.md`. Emphasize matches, handle soft gaps only if definitionally supported by narratives, omit hard gaps entirely. Use JD terminology from the terminology mappings.

Write the resume as markdown to `poc/jobs/$ARGUMENTS/runs/<run-dir-name>/resume_draft.md`:

```
# Resume Draft

## Summary
[2–3 sentence professional summary]

## Experience

### [Company] — [Title] ([Dates])

**[Project Name]**
- [bullet]

## Skills
[comma-separated list]
```

Print: `[2/4] Resume draft → generated`

## Stage 3 — ATS Screening

Read:
- `poc/prompts/resume_screener.md` — screening framework
- `poc/jobs/$ARGUMENTS/jd.md`
- `resume_draft.md` just written

Note: `poc/input/narratives.md` is intentionally not loaded here — this stage simulates an ATS that sees only the resume, not the underlying candidate background.

Apply the framework from `poc/prompts/resume_screener.md`. Produce JSON:

```json
{
  "overall_score": 0.0,
  "semantic_score": 0.0,
  "keyword_coverage": { "keyword": true },
  "terminology_mismatches": [{ "my_term": "string", "jd_term": "string" }],
  "coverage_gaps": [{ "requirement": "string", "gap_type": "<hard|soft>", "impact": "string" }]
}
```

Write to `poc/jobs/$ARGUMENTS/runs/<run-dir-name>/screener_report.json`.

Print: `[3/4] Screener report → overall score <overall_score>`

## Stage 4 — Refinement

Read:
- `poc/prompts/refinement.md` — refinement framework
- `poc/jobs/$ARGUMENTS/jd.md`
- `resume_draft.md` just written
- `screener_report.json` just written
- `poc/input/narratives.md` — for voice reference; do not add claims absent from the draft

Apply the framework from `poc/prompts/refinement.md`:
- **Terminology mismatches**: replace candidate terms with JD equivalents where meaning is genuinely equivalent
- **Soft gaps**: if already partially addressed in the draft, sharpen the existing language; if absent, leave absent — do not add new bullets
- **Hard gaps**: do not bridge; if a section would be empty without the gap, leave the section out

Write refined resume to `poc/jobs/$ARGUMENTS/runs/<run-dir-name>/refined_resume.md`.

Track number of changes made and count of `coverage_gaps` entries from `screener_report.json` not addressed in this pass.

Print: `[4/4] Refinement → <changes count> changes made, <remaining gaps count> remaining gaps`

## Completion

Print:
```
Done. Run saved to poc/jobs/$ARGUMENTS/runs/<run-dir-name>/

Next steps:
  /resume-control $ARGUMENTS    ← generate the control resume
  /resume-evaluate $ARGUMENTS   ← score and compare both
```
