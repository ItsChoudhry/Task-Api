-- 1. Task status lookup table (enum as real table)
CREATE TABLE IF NOT EXISTS task_status (
    name TEXT PRIMARY KEY CHECK (name IN ('pending', 'processing', 'completed', 'failed', 'callback_sent'))
);

-- Insert default statuses if not exist
INSERT INTO task_status (name)
VALUES ('pending'), ('processing'), ('completed'), ('failed'), ('callback_sent')
ON CONFLICT (name) DO NOTHING;

-- 2. Main tasks table with proper foreign key
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    idempotency_key TEXT UNIQUE NOT NULL,
    model TEXT NOT NULL,
    param JSONB DEFAULT '{}',
    inputs JSONB DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending' REFERENCES task_status(name),
    result_url TEXT,
    error TEXT,
    callback_url TEXT,
    api_key_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS ix_tasks_idempotency ON tasks(idempotency_key);
CREATE INDEX IF NOT EXISTS ix_tasks_created ON tasks(created_at DESC);
