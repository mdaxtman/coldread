Run the refinement stage of the pipeline for job: $ARGUMENTS

## Precondition checks

Check these in order. Stop at the first failure.

1. Read `poc/input/narratives.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
2. Read `poc/prompts/refinement.md`. If it does not exist: print "Run `/pipeline-setup` first." and stop.
3. Read `poc/jobs/$ARGUMENTS/jd.md`. If it does not exist: print "Create `poc/jobs/$ARGUMENTS/jd.md` first." and stop.
4. Use Bash to list `poc/jobs/$ARGUMENTS/runs/` sorted alphabetically descending; take the first result as the latest run directory. If the directory does not exist or is empty: print "No run directory found. Run `/pipeline-run $ARGUMENTS` first to create one." and stop.
5. Read `poc/jobs/$ARGUMENTS/runs/<latest>/resume_draft.md`. If it does not exist: print "Run `/pipeline-generate $ARGUMENTS` first." and stop.
6. Read `poc/jobs/$ARGUMENTS/runs/<latest>/screener_report.json`. If it does not exist: print "Run `/pipeline-screen $ARGUMENTS` first." and stop.

## Refinement

You now have:
- The refinement framework from `poc/prompts/refinement.md`
- The job description from `poc/jobs/$ARGUMENTS/jd.md`
- The resume draft from `resume_draft.md`
- The screener feedback from `screener_report.json`
- The candidate narratives from `poc/input/narratives.md` — for voice reference; do not add claims absent from the draft

Apply the framework from `poc/prompts/refinement.md`:
- **Terminology mismatches**: replace candidate terms with JD equivalents where meaning is genuinely equivalent
- **Soft gaps**: if already partially addressed in the draft, sharpen the existing language; if absent from the draft, leave it absent — do not add new bullets
- **Hard gaps**: do not bridge; if a section would be empty without the gap, leave the section out

Track every change you make: for each modification, note the section and what changed.

## Output

Write the refined resume to `poc/jobs/$ARGUMENTS/runs/<latest>/refined_resume.md`.

Use the same markdown structure as the draft (Summary → Experience → Skills).

Print one line: `[refine] done — <number of changes> changes, <remaining_gaps count> remaining gaps`

Where: `<remaining_gaps count>` = number of `coverage_gaps` entries from `screener_report.json` that were not addressed in this refinement pass.
