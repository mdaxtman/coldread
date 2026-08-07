-- 007_enable_rls_original_tables.sql
--
-- WHAT: Enable Row Level Security on the five original tables — narratives,
--       prompts, job_descriptions, fit_reports, resume_variants.
--
-- WHY:  These tables already have RLS *policies* (defined in 20260326_enable_rls.sql
--       and 20260329_fix_prompts_rls.sql), but RLS itself was never switched on, so
--       the policies were inert and the tables were fully exposed to the anon /
--       publishable key. This was pre-existing drift, flagged as a follow-up in PR #36,
--       and it is what triggers Supabase's recurring "RLS disabled" security advisory.
--
-- SAFETY: No functional impact.
--   - The server (server/db/client.py) connects with the service/secret key, which
--     BYPASSES RLS entirely — its access is unchanged.
--   - The frontend never talks to Supabase directly (no supabase-js dependency in
--     client/; all data access goes through the FastAPI server), so there is no
--     anon-key code path that RLS could block.
--   Enabling RLS simply activates the already-present policies and closes the
--   anon-exposure hole. This brings the original tables in line with the RLS posture
--   already applied to the observability tables (pipeline_runs, model_calls) in
--   005_observability.sql.
--
-- NOTE: ENABLE (not FORCE) ROW LEVEL SECURITY is intentional — the service_role must
--       continue to bypass RLS for the server to operate. Policy cleanup (the prompts
--       table has redundant/legacy policies) is deliberately out of scope here.

ALTER TABLE public.narratives       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.prompts          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_descriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fit_reports      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resume_variants  ENABLE ROW LEVEL SECURITY;
