Set up the POC working directory for the resume pipeline POC.

## Steps

### 1. Extract narratives

If `server/seeds/seed_narratives.py` does not exist, stop and print: "`server/seeds/seed_narratives.py` not found — is this the right repo root?" If any `server/prompts/*.md` file listed in Step 2 is missing, stop and print which file is missing and suggest running `git status` to check.

Read `server/seeds/seed_narratives.py`.

Extract the string content of these constants (text between the triple-quote delimiters, stripped of leading/trailing whitespace):
- `CAREER_OVERVIEW`
- `NARRATIVE_1` through `NARRATIVE_7`

Create directory `poc/input/` if it does not exist.

Write `poc/input/narratives.md` with this exact structure:

```
# Candidate Narratives

## Career Overview

{CAREER_OVERVIEW content}

---

## Ekko Media

{NARRATIVE_1 content}

---

## Formidable Labs

{NARRATIVE_2 content}

---

## Nordstrom Technology

{NARRATIVE_3 content}

---

## AWS Service Catalog

{NARRATIVE_4 content}

---

## AWS Control Tower

{NARRATIVE_5 content}

---

## QuickAutomate

{NARRATIVE_6 content}

---

## Amazon Retail Consumables

{NARRATIVE_7 content}
```

### 2. Copy prompts

Create directory `poc/prompts/` if it does not exist.

Read each of the following files and write their content to the corresponding `poc/prompts/` path:
- `server/prompts/fit_assessment.md` → `poc/prompts/fit_assessment.md`
- `server/prompts/generator.md` → `poc/prompts/generator.md`
- `server/prompts/resume_screener.md` → `poc/prompts/resume_screener.md`
- `server/prompts/refinement.md` → `poc/prompts/refinement.md`

### 3. Create config

If `poc/config.json` does not already exist, create it with these exact contents:

```json
{
  "weights": {
    "jd_alignment": 0.4,
    "recruiter_readability": 0.2,
    "authenticity": 0.4
  }
}
```

If it already exists, do not overwrite it — the user may have customized the weights.

### 4. Print summary

```
Setup complete.
  poc/input/narratives.md  ← 8 sections extracted
  poc/prompts/             ← 4 prompt files copied
  poc/config.json          ← created (or already exists, not overwritten)

To run the pipeline:
  1. Create poc/jobs/<job-slug>/jd.md with the job description
  2. /pipeline-run <job-slug>
```
