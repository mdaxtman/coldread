Generate the baseline control resume for job: $ARGUMENTS

The control resume is the uncontaminated baseline — written by an isolated sub-agent with access only to the candidate narratives and job description. The sub-agent has no knowledge of the fit assessment, screener report, resume draft, or any other pipeline artifact.

## Precondition checks

1. Read `poc/input/narratives.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
2. Read `poc/jobs/$ARGUMENTS/jd.md`. If it does not exist: print "Create `poc/jobs/$ARGUMENTS/jd.md` first." and stop.
3. Use Bash to list `poc/jobs/$ARGUMENTS/runs/` sorted alphabetically descending; take the first result as the latest run directory. Save this name — it is `<latest>` everywhere below. If the directory does not exist or is empty: print "No run directory found. Run `/pipeline-stages-all $ARGUMENTS` first." and stop.

## Sub-agent isolation

You now have the content of both files in your context. Do not pass file paths to the sub-agent — pass the file contents inline so the sub-agent has no reason to access the filesystem.

Spawn a sub-agent (Agent tool) with the following prompt. Substitute `{NARRATIVES}` with the full text of `poc/input/narratives.md` and `{JD}` with the full text of `poc/jobs/$ARGUMENTS/jd.md`:

---
You are an expert resume writer with deep knowledge of what makes a resume effective for technical roles.

**ISOLATION REQUIREMENT: You have been given all the content you need inline below. Do not use Read, Bash, Glob, or any file-access tools. Do not read any files from disk. The run directory for this job contains pipeline artifacts (fit assessment, screener report, resume drafts) that you must not access — doing so would contaminate the control baseline.**

## Candidate Background Narratives

{NARRATIVES}

## Job Description

{JD}

## Task

Write the best possible resume for this candidate targeting this specific role. You have full discretion — choose the most relevant experience, use strong language, make strategic emphasis decisions. You do not need to explain your choices.

Constraint: every claim must be grounded in the candidate narratives above. Do not invent experience, metrics, or skills not mentioned there.

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

Return the complete resume as markdown. Do not write to any files — return the content only.
---

## Output

Take the resume content returned by the sub-agent and write it to `poc/jobs/$ARGUMENTS/runs/<latest>/control_resume.md`.

Print one line: `[control] resume written`
