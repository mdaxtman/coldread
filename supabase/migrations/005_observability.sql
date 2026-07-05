-- Observability: pipeline run + per-model-call telemetry.
-- A run is one pipeline execution (fit | generate | refine); each Anthropic
-- API call within it becomes a model_calls row, persisted as it finishes so
-- failed runs keep their partial trace.

CREATE TABLE pipeline_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    job_description_id  UUID NOT NULL REFERENCES job_descriptions(id),
    kind                TEXT NOT NULL CHECK (kind IN ('fit', 'generate', 'refine')),
    status              TEXT NOT NULL DEFAULT 'running'
                        CHECK (status IN ('running', 'completed', 'failed')),
    error               TEXT,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at         TIMESTAMPTZ,
    duration_ms         INTEGER,
    tokens_in           INTEGER NOT NULL DEFAULT 0,
    tokens_out          INTEGER NOT NULL DEFAULT 0,
    est_cost_usd        NUMERIC(10, 6) NOT NULL DEFAULT 0
);

CREATE TABLE model_calls (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID NOT NULL,
    run_id        UUID NOT NULL REFERENCES pipeline_runs(id),
    stage         TEXT NOT NULL,
    seq           INTEGER NOT NULL,
    model         TEXT NOT NULL,
    latency_ms    INTEGER NOT NULL,
    tokens_in     INTEGER NOT NULL,
    tokens_out    INTEGER NOT NULL,
    stop_reason   TEXT,
    est_cost_usd  NUMERIC(10, 6) NOT NULL DEFAULT 0,
    request       JSONB NOT NULL,
    response      JSONB NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_pipeline_runs_user_id ON pipeline_runs(user_id);
CREATE INDEX idx_pipeline_runs_jd_id ON pipeline_runs(job_description_id);
CREATE INDEX idx_pipeline_runs_started_at ON pipeline_runs(started_at DESC);
CREATE INDEX idx_model_calls_user_id ON model_calls(user_id);
CREATE INDEX idx_model_calls_run_id ON model_calls(run_id);

ALTER TABLE pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_calls ENABLE ROW LEVEL SECURITY;

-- Pipeline Runs
CREATE POLICY "Users can view their own pipeline runs"
  ON pipeline_runs FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can insert pipeline runs for themselves"
  ON pipeline_runs FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Service role can manage all pipeline runs"
  ON pipeline_runs
  USING (auth.role() = 'service_role');

-- Model Calls
CREATE POLICY "Users can view their own model calls"
  ON model_calls FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can insert model calls for themselves"
  ON model_calls FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Service role can manage all model calls"
  ON model_calls
  USING (auth.role() = 'service_role');
