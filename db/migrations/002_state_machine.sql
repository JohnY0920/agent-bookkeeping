-- Migration 002: State machine tables for processing runs and human evaluation events

CREATE TABLE IF NOT EXISTS processing_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id       UUID NOT NULL REFERENCES engagements(id),
    firm_id             UUID NOT NULL,
    agent_type          TEXT NOT NULL,
    task_description    TEXT,
    status              TEXT NOT NULL DEFAULT 'RUNNING'
                            CHECK (status IN ('RUNNING', 'COMPLETE', 'FAILED', 'WAITING_HUMAN')),
    prompt_version      TEXT,
    result_summary      TEXT,
    error_message       TEXT,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- human_evaluation_events tracks every CPA touchpoint in the pipeline
-- Used for audit trail and evaluation analytics
CREATE TABLE IF NOT EXISTS human_evaluation_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    processing_run_id   UUID REFERENCES processing_runs(id),
    engagement_id       UUID NOT NULL REFERENCES engagements(id),
    firm_id             UUID NOT NULL,
    review_item_id      UUID REFERENCES review_items(id),
    pipeline_stage      TEXT NOT NULL,
    evaluator_user_id   UUID,
    decision            TEXT CHECK (decision IN ('APPROVED', 'REJECTED', 'MODIFIED')),
    decision_note       TEXT,
    occurred_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_processing_runs_engagement ON processing_runs(engagement_id);
CREATE INDEX IF NOT EXISTS idx_processing_runs_status ON processing_runs(status);
CREATE INDEX IF NOT EXISTS idx_processing_runs_agent ON processing_runs(agent_type, status);
CREATE INDEX IF NOT EXISTS idx_human_eval_engagement ON human_evaluation_events(engagement_id);
CREATE INDEX IF NOT EXISTS idx_human_eval_review_item ON human_evaluation_events(review_item_id);
CREATE INDEX IF NOT EXISTS idx_human_eval_stage ON human_evaluation_events(pipeline_stage);
