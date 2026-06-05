Run the fit assessment stage of the resume pipeline for job: $ARGUMENTS

## Precondition checks

Check these in order. Stop at the first failure.

1. Read `poc/input/narratives.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
2. Read `poc/prompts/fit_assessment.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
3. Read `poc/jobs/$ARGUMENTS/jd.md`. If it does not exist: print "Create `poc/jobs/$ARGUMENTS/jd.md` with the job description first." and stop.
4. Use Bash to list `poc/jobs/$ARGUMENTS/runs/` sorted descending, take the first result as the latest run directory. If the directory does not exist or is empty: print "No run directory found. Run `/pipeline-run $ARGUMENTS` first to create one." and stop.

## Analysis

You now have:
- The analysis framework from `poc/prompts/fit_assessment.md`
- The candidate's background from `poc/input/narratives.md`
- The job description from `poc/jobs/$ARGUMENTS/jd.md`

Apply the framework from `poc/prompts/fit_assessment.md` to evaluate how well the candidate's background matches the job description.

Produce a JSON object with this exact schema:

```json
{
  "fit_level": "<strong|moderate|borderline|poor>",
  "matches": [
    { "requirement": "string", "priority": "<required|preferred|implied>", "notes": "string" }
  ],
  "gaps": [
    { "requirement": "string", "type": "<hard|soft>", "notes": "string" }
  ],
  "terminology": [
    { "my_term": "string", "jd_term": "string", "confidence": 0.0 }
  ],
  "reasoning": "string"
}
```

Rules:
- `terminology`: only include mappings with confidence ≥ 0.8
- `reasoning`: 2–3 sentences summarizing the fit level and key determining factors

## Output

Write the JSON to `poc/jobs/$ARGUMENTS/runs/<latest>/fit_assessment.json`.

Print one line: `[fit] <fit_level> → <matches count> matches, <hard count> hard gaps, <soft count> soft gaps`
