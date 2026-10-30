CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id         SERIAL PRIMARY KEY,
    source     TEXT NOT NULL,
    content    TEXT NOT NULL,
    -- shortcut: không cố định số chiều nên chưa tạo được index HNSW; dữ liệu vài nghìn đoạn trở lên thì cố định số chiều và thêm index
    embedding  vector NOT NULL
);
