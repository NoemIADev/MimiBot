--==== Postgre + pgvector ====
CREATE EXTENSION IF NOT EXISTS vector;



-- =========================
-- TABLE DOCUMENTS
-- =========================
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    source_name TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================
-- TABLE CHUNKS
-- =========================
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    content TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================
-- TABLE QA HISTORY
-- =========================
CREATE TABLE IF NOT EXISTS qa_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    question TEXT,
    question_embedding VECTOR(1536),
    answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
