Show score trends across all runs for job: $ARGUMENTS

## Precondition checks

1. Use Bash to check if `poc/jobs/$ARGUMENTS/` exists. If it does not: print "No job found with slug `$ARGUMENTS`. Create `poc/jobs/$ARGUMENTS/jd.md` first." and stop.

## Collection

Use Bash to list all directories under `poc/jobs/$ARGUMENTS/runs/` sorted ascending. For each directory, check if `evaluation_report.json` exists inside it. Read each one that does.

If no `evaluation_report.json` files are found: print "No evaluated runs found for `$ARGUMENTS`. Run `/resume-evaluate $ARGUMENTS` after a pipeline run." and stop.

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
