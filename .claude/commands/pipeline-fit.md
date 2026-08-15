Run the fit assessment stage of the resume pipeline for job: $ARGUMENTS

## Precondition checks

Check these in order. Stop at the first failure.

1. Read `poc/input/narratives.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
2. Read `poc/prompts/fit_assessment.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
3. Read `poc/jobs/$ARGUMENTS/jd.md`. If it does not exist: print "Create `poc/jobs/$ARGUMENTS/jd.md` with the job description first." and stop.
4. Use Bash to list `poc/jobs/$ARGUMENTS/runs/` sorted alphabetically descending; take the first result as the latest run directory. If the directory does not exist or is empty: print "No run directory found. Run `/pipeline-stages-all $ARGUMENTS` first to create one." and stop.

## Analysis

You now have:
- The analysis framework from `poc/prompts/fit_assessment.md`
- The candidate's background from `poc/input/narratives.md`
- The job description from `poc/jobs/$ARGUMENTS/jd.md`

Apply the framework from `poc/prompts/fit_assessment.md` to evaluate how well the candidate's background matches the job description — including its DIFFERENTIATING REQUIREMENTS, LEVEL GATE, and SCORING sections.

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
  "cultural_signals": [
    { "quality": "string", "jd_signal": "string", "evidence_hint": "string" }
  ],
  "product_connection": "string or null",
  "overall_score": 0.0,
  "semantic_score": 0.0,
  "reasoning": "string"
}
```

This schema must stay in sync with the OUTPUT FORMAT section of `poc/prompts/fit_assessment.md`, which is authoritative. The generation stage consumes `cultural_signals` and `product_connection` directly — the generator prompt requires a bullet of authentic evidence per cultural signal, and uses `product_connection` as the source for the summary's company-specific sentence. Omitting either field silently degrades the resume rather than raising an error.

Rules:
- `terminology`: only include mappings with confidence ≥ 0.8; an empty array is correct if none qualify
- `cultural_signals`: 2–3 entries
- `product_connection`: a single concise sentence, or `null` if the parallel would need to be argued rather than named
- `overall_score` / `semantic_score`: 0–1, applying the framework's scoring rules and caps on their merits
- `reasoning`: summarize the fit level and key determining factors, naming which differentiating requirements are met or absent

## Output

Write the JSON to `poc/jobs/$ARGUMENTS/runs/<latest>/fit_assessment.json`.

Print one line: `[fit] <fit_level> (<overall_score>) → <matches count> matches, <hard count> hard gaps, <soft count> soft gaps`

Where: `<hard count>` = number of entries in `gaps` where `type == "hard"`, `<soft count>` = number where `type == "soft"`.
