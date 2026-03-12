-- JD persistence & pipeline results tables.
-- Stores job descriptions, fit reports, and resume variants for linkable
-- results URLs and analysis history tracking.

-- =============================================================================
-- Tables
-- =============================================================================

CREATE TABLE job_descriptions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    title       TEXT,
    company     TEXT,
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE fit_reports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    job_description_id  UUID NOT NULL REFERENCES job_descriptions(id),
    fit_level           TEXT NOT NULL CHECK (fit_level IN ('strong', 'moderate', 'borderline', 'poor')),
    matches             JSONB NOT NULL DEFAULT '[]',
    gaps                JSONB NOT NULL DEFAULT '[]',
    terminology         JSONB NOT NULL DEFAULT '[]',
    reasoning           TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE resume_variants (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    job_description_id  UUID NOT NULL REFERENCES job_descriptions(id),
    content             TEXT NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    parent_variant_id   UUID REFERENCES resume_variants(id),
    screener_report     JSONB NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =============================================================================
-- Indexes
-- =============================================================================

CREATE INDEX idx_job_descriptions_user_id ON job_descriptions(user_id);
CREATE INDEX idx_fit_reports_user_id ON fit_reports(user_id);
CREATE INDEX idx_fit_reports_jd_id ON fit_reports(job_description_id);
CREATE INDEX idx_resume_variants_user_id ON resume_variants(user_id);
CREATE INDEX idx_resume_variants_jd_id ON resume_variants(job_description_id);
