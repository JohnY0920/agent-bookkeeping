-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Firm (multi-tenant root)
CREATE TABLE firms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    logo_url TEXT,
    contact_email TEXT,
    branding JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id UUID NOT NULL REFERENCES firms(id),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('ADMIN', 'ACCOUNTANT', 'STAFF')),
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Clients
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id UUID NOT NULL REFERENCES firms(id),
    name TEXT NOT NULL,
    entity_type TEXT CHECK (entity_type IN ('CORPORATION', 'SOLE_PROPRIETOR', 'PARTNERSHIP', 'INDIVIDUAL')),
    contact_email TEXT,
    industry_code TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Engagements
CREATE TABLE engagements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    firm_id UUID NOT NULL REFERENCES firms(id),
    period_label TEXT NOT NULL,
    engagement_type TEXT NOT NULL CHECK (engagement_type IN ('BOOKKEEPING', 'T1', 'T2')),
    mode TEXT NOT NULL DEFAULT 'COLLECTION' CHECK (mode IN ('COLLECTION', 'PROCESSING', 'REVIEW', 'COMPLETE')),
    assigned_user_id UUID REFERENCES users(id),
    current_summary TEXT,
    last_sync_at TIMESTAMPTZ,
    last_reminder_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Task plans
CREATE TABLE task_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'PAUSED', 'COMPLETE', 'FAILED')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE plan_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES task_plans(id),
    agent_type TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETE', 'FAILED', 'WAITING_HUMAN', 'SKIPPED')),
    sort_order INT NOT NULL,
    depends_on UUID[],
    requires_human BOOLEAN DEFAULT FALSE,
    result_summary TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT
);

-- Checklist items
CREATE TABLE checklist_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    item_type TEXT NOT NULL,
    label TEXT NOT NULL,
    required BOOLEAN DEFAULT TRUE,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'RECEIVED', 'VERIFIED', 'NOT_APPLICABLE')),
    received_at TIMESTAMPTZ,
    document_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    engagement_id UUID REFERENCES engagements(id),
    firm_id UUID NOT NULL REFERENCES firms(id),
    filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_size INT,
    classification TEXT,
    classification_confidence FLOAT,
    extracted_data JSONB,
    uploaded_by UUID REFERENCES users(id),
    uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- GL entries (source_chain is mandatory)
CREATE TABLE gl_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    account_code TEXT NOT NULL,
    account_name TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    entry_date DATE NOT NULL,
    description TEXT,
    source_chain JSONB NOT NULL,
    created_by TEXT NOT NULL CHECK (created_by IN ('AGENT', 'USER', 'XERO_IMPORT')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Review items
CREATE TABLE review_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    processing_run_id UUID,
    item_type TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    confidence_score FLOAT,
    agent_reasoning JSONB,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'ADJUSTED')),
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Working paper entries
CREATE TABLE workpaper_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    entry_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_event JSONB,
    reference_id TEXT,
    created_by TEXT NOT NULL CHECK (created_by IN ('AGENT', 'USER')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Accounting connections (Xero/QBO OAuth — tokens encrypted at application level)
CREATE TABLE accounting_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id),
    firm_id UUID NOT NULL REFERENCES firms(id),
    platform TEXT NOT NULL CHECK (platform IN ('XERO', 'QBO')),
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    token_expiry TIMESTAMPTZ,
    tenant_id TEXT,
    status TEXT NOT NULL DEFAULT 'CONNECTED' CHECK (status IN ('CONNECTED', 'EXPIRED', 'ERROR')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Communication log
CREATE TABLE communication_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    engagement_id UUID NOT NULL REFERENCES engagements(id),
    firm_id UUID NOT NULL REFERENCES firms(id),
    direction TEXT NOT NULL CHECK (direction IN ('INBOUND', 'OUTBOUND')),
    channel TEXT NOT NULL CHECK (channel IN ('EMAIL', 'PORTAL')),
    subject TEXT,
    body TEXT,
    sent_by TEXT NOT NULL CHECK (sent_by IN ('AGENT', 'USER', 'CLIENT')),
    cc_users TEXT[],
    related_checklist_item_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Lessons (pgvector: 1024 dims to match Mistral embed)
CREATE TABLE lessons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id UUID NOT NULL REFERENCES firms(id),
    agent_type TEXT NOT NULL,
    client_id UUID REFERENCES clients(id),
    scenario_description TEXT NOT NULL,
    lesson_content TEXT NOT NULL,
    embedding VECTOR(1024),
    created_by TEXT NOT NULL CHECK (created_by IN ('AGENT', 'USER')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email templates
CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id UUID NOT NULL REFERENCES firms(id),
    template_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    is_customized BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit log
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id UUID NOT NULL REFERENCES firms(id),
    user_id UUID REFERENCES users(id),
    agent_type TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id UUID,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- API call log (cost tracking)
CREATE TABLE api_call_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id UUID,
    model TEXT NOT NULL,
    input_tokens INT,
    output_tokens INT,
    stop_reason TEXT,
    agent_type TEXT,
    engagement_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_engagements_client ON engagements(client_id);
CREATE INDEX idx_engagements_mode ON engagements(mode);
CREATE INDEX idx_engagements_firm ON engagements(firm_id);
CREATE INDEX idx_checklist_engagement ON checklist_items(engagement_id);
CREATE INDEX idx_documents_engagement ON documents(engagement_id);
CREATE INDEX idx_gl_entries_engagement ON gl_entries(engagement_id);
CREATE INDEX idx_gl_entries_account ON gl_entries(account_code);
CREATE INDEX idx_review_items_engagement ON review_items(engagement_id);
CREATE INDEX idx_review_items_status ON review_items(status);
CREATE INDEX idx_workpaper_engagement ON workpaper_entries(engagement_id);
CREATE INDEX idx_plan_steps_plan ON plan_steps(plan_id);
CREATE INDEX idx_lessons_agent ON lessons(agent_type);
CREATE INDEX idx_audit_firm ON audit_logs(firm_id);
