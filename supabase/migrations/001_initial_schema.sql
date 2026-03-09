-- ColdRead initial schema
-- Only tables needed at runtime: narratives (seeded) and prompts (seeded).
-- Job descriptions, resume variants, and fit reports are pipeline I/O —
-- handled in-memory in ColdRead, persisted in Candor.

-- =============================================================================
-- Tables
-- =============================================================================

CREATE TABLE narratives (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    category    TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE prompts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    stage       TEXT NOT NULL,
    name        TEXT NOT NULL,
    template    TEXT NOT NULL,
    version     INTEGER NOT NULL DEFAULT 1,
    active      BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, stage, name, version)
);

-- =============================================================================
-- Indexes
-- =============================================================================

CREATE INDEX idx_narratives_user_id ON narratives(user_id);
CREATE INDEX idx_prompts_user_id ON prompts(user_id);

-- =============================================================================
-- Trigger: auto-update updated_at on narratives
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_narratives_updated_at
    BEFORE UPDATE ON narratives
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
