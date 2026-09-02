Show score trends across all runs for job: $ARGUMENTS

## Precondition checks

1. Use Bash to check if `poc/jobs/$ARGUMENTS/` exists. If it does not: print "No job found with slug `$ARGUMENTS`. Create `poc/jobs/$ARGUMENTS/jd.md` first." and stop.

## Collection

Use Bash to list all directories under `poc/jobs/$ARGUMENTS/runs/` sorted ascending. For each directory, check if `evaluation_report.json` exists inside it. Read each one that does.

Collect `rubric_version` from each report; a missing field means version 1. If the runs do not
all share one version, print this above the table and add a `Rub` column showing each run's
version:

```
!! Mixed rubric versions. v1 scored the control resume with a title naming it as the control,
!! did not normalise authenticity against claim count, and scored authenticity in the
!! orchestrator rather than in an isolated judge. Re-scoring identical documents under v2 moved
!! the composite gap from +0.93 to +0.14, so trends across the boundary are not real movement.
```

Leave the Trend cell blank on the first run of each new rubric version. A score change caused by
a change of ruler is not a score change.

If no `evaluation_report.json` files are found: print "No evaluated runs found for `$ARGUMENTS`. Run `/pipeline-evaluate $ARGUMENTS` after a pipeline run." and stop.

## Table

Sort runs by directory name ascending (chronological order).

For two or more runs, compute a trend indicator by comparing each run's pipeline composite to the previous run:
- `↑` if composite improved by more than 0.1
- `↓` if composite declined by more than 0.1
- `→` if within 0.1 of previous

For the first run, the Trend cell is blank.

The Trend indicator goes in its own column (not merged into the Pipeline column) so scores stay aligned.

Print:

```
<job-slug>
─────────────────────────────────────────────────────────────────────
Run             Trend    Pipeline    Control     Delta    Winner
YYYY-MM-DD               0.00        0.00        +0.00    pipeline
YYYY-MM-DD-2    ↑        0.00        0.00        +0.00    pipeline
─────────────────────────────────────────────────────────────────────
Runs: N  |  Pipeline wins: N  |  Control wins: N  |  Ties: N
Best pipeline score: 0.00 (YYYY-MM-DD)
```
