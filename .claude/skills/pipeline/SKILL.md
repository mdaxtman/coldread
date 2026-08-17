# Run Resume Pipeline

Runs a full scored pipeline for a job slug and reports it against prior runs.

## Isolation invariants — read first

The value of this pipeline is that each stage sees a defined input set and nothing else.
A run that peeks at earlier results is not a measurement, it is an echo. These rules bind
you, not just the sub-agents you spawn.

**Never read anything under `poc/jobs/<slug>/runs/` except artifacts this run produced.**
That means no prior `fit_assessment.json`, no prior `resume_draft.md` or `refined_resume.md`,
no prior `screener_report.json`, and no prior `evaluation_report.json` — not for a baseline,
not for scoring calibration, not "to stay consistent," and not to match formatting. Output
formats are specified in the commands; take them from there.

**Never anchor a judgment to a previous run.** If a scoring rule in a prompt appears to
apply, decide it on that prompt's wording. Do not preserve an earlier interpretation to keep
numbers comparable — a run that reproduces a prior mistake for the sake of a clean delta is
worse than a run that disagrees with history.

**Never overwrite an existing run directory.** Each invocation creates a new dated directory.

**If your own context is already contaminated** — you read a prior artifact earlier in the
session, or the user pasted one — delegate the affected stage to a sub-agent with the
stage's specified inputs and an explicit prohibition on the runs directory, the way
`/pipeline-control` does. Say so in the final report rather than proceeding quietly.

Cross-run comparison is legitimate and expected, but only **after** this run is fully scored.
It is reporting, never an input.

## Steps

1. **Sync the POC inputs.** Run `/pipeline-setup`. It regenerates `poc/input/narratives.md`
   from `server/seeds/seed_narratives.py` and copies `server/prompts/*.md` into
   `poc/prompts/`. Do this whenever narratives or prompts changed.

   Note: the `/pipeline-*` commands read `poc/prompts/` and `poc/input/`. They never read the
   `prompts` database table. Re-seeding the DB does not affect this workflow — it only affects
   the FastAPI app. If you changed a prompt and want both paths current, publish the DB
   version separately and run `/pipeline-setup` for this one.

2. **Run the pipeline into a new run directory.** Run `/pipeline-stages-all <slug>`. This creates
   `poc/jobs/<slug>/runs/<YYYY-MM-DD>/` and executes fit assessment → generation → screening
   → refinement.

   Do **not** substitute `/pipeline-generate` here. That command writes into the *latest
   existing* run directory and will overwrite a prior run's artifacts. The single-stage
   commands (`/pipeline-fit`, `/pipeline-generate`, `/pipeline-screen`, `/pipeline-refine`)
   are for iterating within a run you already created, not for starting one.

3. **Generate the control.** Run `/pipeline-control <slug>`. The sub-agent must receive the
   narratives and JD inline and must not touch the filesystem.

4. **Score both.** Run `/pipeline-evaluate <slug>`. Phase 1 spawns two isolated scorers in
   parallel — each sees the JD and exactly one resume, never the other, and never the
   narratives. Phase 2 scores authenticity against the narratives.

5. **Only now, compare across runs.** Read prior `evaluation_report.json` files for this slug
   and report the trend. `/pipeline-compare <slug>` does this.

## Report

Produce a table with one row per run: composite, jd_alignment, recruiter_readability,
authenticity, hire_intent, and winner — pipeline and control side by side for the current
run, and composites for prior runs as trend.

State what changed since the last run (narratives, prompts, prompt versions) so a score
movement can be attributed. If nothing changed but scores moved, say so plainly — that is
run-to-run variance and it is worth knowing.
