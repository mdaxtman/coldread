-- Add INSERT and UPDATE policies to prompts table
-- The seed script uses the service role key to insert/update prompts

-- Allow service role to insert prompts
CREATE POLICY "Service role can insert prompts"
  ON prompts FOR INSERT
  WITH CHECK (auth.role() = 'service_role');

-- Allow service role to update prompts
CREATE POLICY "Service role can update prompts"
  ON prompts FOR UPDATE
  WITH CHECK (auth.role() = 'service_role');

-- Allow service role to delete prompts
CREATE POLICY "Service role can delete prompts"
  ON prompts FOR DELETE
  USING (auth.role() = 'service_role');
