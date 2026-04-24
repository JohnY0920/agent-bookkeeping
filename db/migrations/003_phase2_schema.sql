-- Migration 003: Phase 2 schema — transactions, knowledge base, schema fixes

-- Fix documents table (column names, add status, make client_id optional)
ALTER TABLE documents RENAME COLUMN filename TO file_name;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'UPLOADED'
    CHECK (status IN ('UPLOADED', 'PROCESSING', 'PROCESSED', 'FAILED', 'DELETED'));
ALTER TABLE documents ALTER COLUMN client_id DROP NOT NULL;

-- Add firm_id to tables that were missing it (needed for multi-tenant API scoping)
ALTER TABLE checklist_items ADD COLUMN IF NOT EXISTS firm_id UUID;
ALTER TABLE review_items    ADD COLUMN IF NOT EXISTS firm_id UUID;
ALTER TABLE workpaper_entries ADD COLUMN IF NOT EXISTS firm_id UUID;
ALTER TABLE gl_entries      ADD COLUMN IF NOT EXISTS firm_id UUID;
ALTER TABLE plan_steps      ADD COLUMN IF NOT EXISTS firm_id UUID;

-- Populate firm_id from parent engagement for existing rows
UPDATE checklist_items ci SET firm_id = e.firm_id FROM engagements e WHERE ci.engagement_id = e.id AND ci.firm_id IS NULL;
UPDATE review_items ri    SET firm_id = e.firm_id FROM engagements e WHERE ri.engagement_id = e.id AND ri.firm_id IS NULL;
UPDATE workpaper_entries w SET firm_id = e.firm_id FROM engagements e WHERE w.engagement_id = e.id AND w.firm_id IS NULL;
UPDATE gl_entries g        SET firm_id = e.firm_id FROM engagements e WHERE g.engagement_id = e.id AND g.firm_id IS NULL;

-- Transactions pulled from Xero (or other accounting software)
CREATE TABLE IF NOT EXISTS transactions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id           UUID NOT NULL REFERENCES engagements(id),
    firm_id                 UUID NOT NULL,
    xero_id                 TEXT,
    bank_account_id         TEXT,
    date                    DATE NOT NULL,
    amount                  DECIMAL(15,2) NOT NULL,
    description             TEXT,
    contact_name            TEXT,
    reference               TEXT,
    categorization_status   TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (categorization_status IN ('PENDING','AUTO_APPROVED','REVIEW_QUEUE','CRITICAL','APPROVED','ADJUSTED')),
    confidence_score        FLOAT,
    account_code            TEXT,
    account_name            TEXT,
    gl_entry_id             UUID REFERENCES gl_entries(id),
    source_chain            JSONB,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- CRA/ITA knowledge base for pgvector similarity search
CREATE TABLE IF NOT EXISTS knowledge_base (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source      TEXT NOT NULL,      -- 'ITA', 'ETA', 'CRA_GUIDE', 'ITC_RULES', 'CCA_CLASSES'
    section     TEXT,               -- e.g. 'ITA s.125', 'ETA s.169(1)'
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    embedding   VECTOR(1024),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_engagement ON transactions(engagement_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(categorization_status);
CREATE INDEX IF NOT EXISTS idx_transactions_xero ON transactions(xero_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date DESC);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_source ON knowledge_base(source);
CREATE INDEX IF NOT EXISTS idx_gl_entries_firm ON gl_entries(firm_id);
CREATE INDEX IF NOT EXISTS idx_checklist_firm ON checklist_items(firm_id);
CREATE INDEX IF NOT EXISTS idx_review_items_firm ON review_items(firm_id);
