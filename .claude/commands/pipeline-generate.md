Run the resume generation stage of the pipeline for job: $ARGUMENTS

## Precondition checks

Check these in order. Stop at the first failure.

1. Read `poc/input/narratives.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
2. Read `poc/prompts/generator.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
3. Read `poc/jobs/$ARGUMENTS/jd.md`. If it does not exist: print "Create `poc/jobs/$ARGUMENTS/jd.md` first." and stop.
4. Use Bash to list `poc/jobs/$ARGUMENTS/runs/` sorted alphabetically descending; take the first result as the latest run directory. If the directory does not exist or is empty: print "No run directory found. Run `/pipeline-stages-all $ARGUMENTS` first to create one." and stop.
5. Read `poc/jobs/$ARGUMENTS/runs/<latest>/fit_assessment.json`. If it does not exist: print "Run `/pipeline-fit $ARGUMENTS` first." and stop.

## Generation

You now have:
- The generation framework from `poc/prompts/generator.md`
- The candidate's background from `poc/input/narratives.md` — this is the source of truth; every claim in the resume must trace back here
- The job description from `poc/jobs/$ARGUMENTS/jd.md` — for role title, company name, and targeted emphasis
- The fit assessment from `fit_assessment.json` — use this for strategic emphasis

Apply the framework from `poc/prompts/generator.md`. From the fit assessment:
- **matches**: emphasize these requirements; use terminology from the `terminology` mappings
- **soft gaps**: only address if definitionally supported by the narratives (same paradigm, wrapping library — not inferred similarity)
- **hard gaps**: omit entirely; do not attempt to bridge

## Output

Write the resume as markdown to `poc/jobs/$ARGUMENTS/runs/<latest>/resume_draft.md`.

Use this structure:
```
# Resume Draft

## Summary
[2–3 sentence professional summary targeting the role]

## Experience

### [Company] — [Title] ([Dates])

**[Project Name]**
- [bullet]
- [bullet]

[repeat for each role and project]

## Skills
[comma-separated list of 5–10 skills prioritizing matched requirements]
```

Print one line: `[generate] resume draft written`
