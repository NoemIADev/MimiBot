"""Check PostgreSQL and optional RAG retrieval without ingesting or deleting data."""
import argparse
from contextlib import closing
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

import config
from db import get_db_connection
import psycopg2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply-schema", action="store_true", help="Explicitly apply create.sql using the direct URL")
    parser.add_argument("--rag", action="store_true", help="Call the existing embedding provider and test retrieval (API usage)")
    args = parser.parse_args()

    if args.apply_schema:
        direct_url = os.getenv("DATABASE_URL_UNPOOLED")
        if not direct_url:
            raise RuntimeError("DATABASE_URL_UNPOOLED is required to apply create.sql")
        with closing(psycopg2.connect(direct_url, connect_timeout=15)) as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL lock_timeout = '5s'")
                    cur.execute((ROOT / "create.sql").read_text(encoding="utf-8"))
        print("PASS create.sql applied; no data deleted")

    with closing(get_db_connection()) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone() == (1,)
            print(f"PASS PostgreSQL connection; TLS={conn.info.ssl_in_use}")
            cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            extension = cur.fetchone()
            if not extension:
                raise RuntimeError("pgvector is not enabled; apply create.sql explicitly")
            print(f"PASS pgvector {extension[0]}")
            for table in ("documents", "chunks", "qa_history"):
                cur.execute(f"SELECT count(*) FROM {table}")
                print(f"PASS {table}: {cur.fetchone()[0]} rows")
            for table, column in (("chunks", "embedding"), ("qa_history", "question_embedding")):
                cur.execute("""
                    SELECT format_type(atttypid, atttypmod)
                    FROM pg_attribute
                    WHERE attrelid = %s::regclass AND attname = %s AND NOT attisdropped
                """, (table, column))
                actual = cur.fetchone()
                if actual != ("vector(1536)",):
                    raise RuntimeError(f"Unexpected type for {table}.{column}: {actual}")
                print(f"PASS {table}.{column}: vector(1536)")
            cur.execute("SELECT '[1,0,0]'::vector <=> '[1,0,0]'::vector")
            assert cur.fetchone()[0] == 0
            print("PASS cosine distance operator")

    if args.rag:
        from embeddings import get_embedding
        from rag import retrieve_bdd

        question = "Quels sont les projets de Noemie ?"
        dimension = len(get_embedding(question))
        if dimension != 1536:
            raise RuntimeError(f"Embedding dimension {dimension} differs from schema dimension 1536; model and schema left unchanged")
        chunks = retrieve_bdd(question)
        print(f"PASS RAG retrieval: {len(chunks)} matching chunks")
        if not chunks:
            print("LIMITATION: no matching context; grounded RAG answer not verified; no ingestion performed")


if __name__ == "__main__":
    main()
