Run the ATS screener stage of the pipeline for job: $ARGUMENTS

## Precondition checks

Check these in order. Stop at the first failure.

1. Read `poc/prompts/resume_screener.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
2. Read `poc/jobs/$ARGUMENTS/jd.md`. If it does not exist: print "Create `poc/jobs/$ARGUMENTS/jd.md` first." and stop.
3. Use Bash to list `poc/jobs/$ARGUMENTS/runs/` sorted alphabetically descending; take the first result as the latest run directory. If the directory does not exist or is empty: print "No run directory found. Run `/pipeline-run $ARGUMENTS` first to create one." and stop.
4. Read `poc/jobs/$ARGUMENTS/runs/<latest>/resume_draft.md`. If it does not exist: print "Run `/pipeline-generate $ARGUMENTS` first." and stop.

## Screening

You now have:
- The screening framework from `poc/prompts/resume_screener.md`
- The job description from `poc/jobs/$ARGUMENTS/jd.md`
- The resume draft from `resume_draft.md`

Note: `poc/input/narratives.md` is intentionally not loaded here — this stage simulates an ATS that sees only the resume, not the underlying candidate background.

Apply the framework from `poc/prompts/resume_screener.md`. Evaluate the resume from an ATS/recruiter perspective — keyword coverage, semantic alignment, terminology mismatches.

Produce a JSON object with this exact schema:

```json
{
  "overall_score": 0.0,
  "semantic_score": 0.0,
  "keyword_coverage": { "keyword": true },
  "terminology_mismatches": [
    { "my_term": "string", "jd_term": "string" }
  ],
  "coverage_gaps": [
    { "requirement": "string", "gap_type": "<hard|soft>", "impact": "string" }
  ]
}
```

Rules:
- `overall_score` and `semantic_score`: 0.0–1.0
- `keyword_coverage`: one entry per meaningful keyword or skill mentioned in the JD; value `true` if evidenced in the resume, `false` if absent

## Output

Write the JSON to `poc/jobs/$ARGUMENTS/runs/<latest>/screener_report.json`.

Print one line: `[screen] overall score <overall_score>, <coverage_gaps count> gaps`
