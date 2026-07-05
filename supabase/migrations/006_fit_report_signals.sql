-- Fit report signals: scores (#31) and cultural signals / product
-- connection (#32). The prompt (screener v3+) already asks the model for
-- these; the tool schema and this table now capture them.

ALTER TABLE fit_reports
    ADD COLUMN overall_score       NUMERIC(4, 3),
    ADD COLUMN semantic_score      NUMERIC(4, 3),
    ADD COLUMN cultural_signals    JSONB NOT NULL DEFAULT '[]',
    ADD COLUMN product_connection  TEXT;
