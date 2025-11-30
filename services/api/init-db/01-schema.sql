DROP TABLE IF EXISTS tasks CASCADE;

CREATE TYPE task_status AS ENUM (
    'received',
    'pending',
    'processing',
    'completed',
    'failed',
    'callback_sent'
);

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    idempotency_key TEXT UNIQUE NOT NULL,
    model TEXT NOT NULL,
    param JSONB DEFAULT '{}',
    inputs JSONB DEFAULT '{}',
    status task_status NOT NULL DEFAULT 'received',
    result_url TEXT,
    error TEXT,
    callback_url TEXT,
    api_key_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ix_tasks_status ON tasks(status);
CREATE INDEX ix_tasks_idempotency ON tasks(idempotency_key);
CREATE INDEX ix_tasks_created ON tasks(created_at DESC);
