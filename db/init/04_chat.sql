CREATE TABLE IF NOT EXISTS messages (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS messages_session_idx ON messages (session_id, id);

CREATE TABLE IF NOT EXISTS handoffs (
    id          BIGSERIAL PRIMARY KEY,
    session_id  TEXT NOT NULL,
    reason      TEXT NOT NULL,
    phone       TEXT,
    status      TEXT NOT NULL DEFAULT 'moi',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
