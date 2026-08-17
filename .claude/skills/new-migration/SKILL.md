---
name: new-migration
description: Use when creating or applying a ColdRead database migration — new tables, columns, indexes, RLS changes, or any schema work against the Supabase project.
---

# New ColdRead Migration

## File conventions

- Path: `supabase/migrations/NNN_snake_name.sql` — sequential numbering (`ls` the dir for the next number). The two date-prefixed files (`20260326…`, `20260329…`) are legacy one-offs, not the convention.
- Every table (multi-user invariant — the fork adds only auth + RLS, schema must already be ready):
  - `id UUID PRIMARY KEY DEFAULT gen_random_uuid()`
  - `user_id UUID NOT NULL` + `CREATE INDEX idx_<table>_user_id ON <table>(user_id);`
  - `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
  - FKs indexed: `idx_<table>_<ref>_id`
- Since `20260326_enable_rls.sql`, new tables get RLS in the same migration (copy the pattern from `005_observability.sql`): ENABLE ROW LEVEL SECURITY + user SELECT policy + user INSERT policy + service-role policy.
- Comment header explaining what/why, like existing migrations.

## Applying — pre-flight FIRST

1. **Restore the project** — it auto-pauses when idle. Check with Supabase MCP `get_project` (status); if paused, `restore_project` and wait (~3–4 min). Applying against a paused project fails.
2. `list_migrations` — reconcile drift before adding more. Known drift: 003, 004, and 20260329 were applied but are NOT in tracked history (they were run via raw SQL, not `apply_migration`).
3. `list_tables` — confirm the new table doesn't exist and FK targets do.

## Applying — the actual step

Use Supabase MCP **`apply_migration`** (project ref is the subdomain of `SUPABASE_URL` in `server/.env`; `list_projects` also resolves it), NOT `execute_sql`. `apply_migration` records the migration in tracked history; `execute_sql` is how the history drift happened. There is no linked local CLI (`supabase db push` also expects timestamp filenames — doesn't fit this repo).

## Verify

- `list_tables` → new table present with `rls_enabled: true`
- `get_advisors` (security) → no new findings
- RLS reality check: the 5 original tables (narratives, prompts, job_descriptions, fit_reports, resume_variants) have RLS **disabled** despite policies in migrations — don't extend that pattern; new tables enable it.

Commit the migration file on a feature branch; PR as usual (never merge).
