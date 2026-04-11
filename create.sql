--==== Postgre + pgvector ====



-- =========================
-- TABLE DOCUMENTS
-- =========================
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT,
    source_name TEXT,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =========================
-- TABLE CHUNKS
-- =========================
CREATE TABLE chunks (
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
CREATE TABLE qa_history (
    id SERIAL PRIMARY KEY,
    session_id TEXT,
    question TEXT,
    question_embedding VECTOR(1536),
    answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);