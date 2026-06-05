Generate the baseline control resume for job: $ARGUMENTS

The control resume is written directly — no pipeline stages, no fit analysis, no screener loop. It is the baseline for comparison with the pipeline output.

## Precondition checks

1. Read `poc/input/narratives.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
2. Read `poc/jobs/$ARGUMENTS/jd.md`. If it does not exist: print "Create `poc/jobs/$ARGUMENTS/jd.md` first." and stop.
3. Use Bash to list `poc/jobs/$ARGUMENTS/runs/` sorted alphabetically descending; take the first result as the latest run directory. If the directory does not exist or is empty: print "No run directory found. Run `/pipeline-run $ARGUMENTS` first." and stop.

## Task

You are an expert resume writer with deep knowledge of what makes a resume effective for technical roles.

Read the candidate's background from `poc/input/narratives.md` and the target job description from `poc/jobs/$ARGUMENTS/jd.md`.

Write the best possible resume for this candidate targeting this specific role. You have full discretion — choose the most relevant experience, use strong language, make strategic emphasis decisions. You do not need to explain your choices.

Constraint: every claim must be grounded in `poc/input/narratives.md`. Do not invent experience, metrics, or skills not mentioned there.

Format as markdown:

```
# Control Resume

## Summary
[2–3 sentence professional summary]

## Experience

### [Company] — [Title] ([Dates])

**[Project Name]**
- [bullet]
- [bullet]

[repeat for each role and project]

## Skills
[comma-separated list]
```

## Output

Write the resume to `poc/jobs/$ARGUMENTS/runs/<latest>/control_resume.md`.

Print one line: `[control] resume written`
