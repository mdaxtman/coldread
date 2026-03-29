-- Enable Row Level Security on all tables and create policies
--
-- Policies allow access when:
-- 1. The row's user_id matches the authenticated user's ID
-- 2. The service role key is used (for ColdRead's single-user setup)
--
-- When forking to Candor (multi-user), remove the service role bypass
-- and switch to per-request JWTs from your auth provider.

-- Narratives
ALTER TABLE narratives ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read narratives for their user_id"
  ON narratives FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Service role can read all narratives"
  ON narratives FOR SELECT
  USING (auth.role() = 'service_role');

-- Prompts
ALTER TABLE prompts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read prompts for their user_id"
  ON prompts FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Service role can read all prompts"
  ON prompts FOR SELECT
  USING (auth.role() = 'service_role');

-- Job Descriptions
ALTER TABLE job_descriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own job descriptions"
  ON job_descriptions FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can insert job descriptions for themselves"
  ON job_descriptions FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Service role can manage all job descriptions"
  ON job_descriptions
  USING (auth.role() = 'service_role');

-- Fit Reports
ALTER TABLE fit_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own fit reports"
  ON fit_reports FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can insert fit reports for themselves"
  ON fit_reports FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Service role can manage all fit reports"
  ON fit_reports
  USING (auth.role() = 'service_role');

-- Resume Variants
ALTER TABLE resume_variants ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own resume variants"
  ON resume_variants FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can insert resume variants for themselves"
  ON resume_variants FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Service role can manage all resume variants"
  ON resume_variants
  USING (auth.role() = 'service_role');
