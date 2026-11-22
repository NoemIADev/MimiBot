import os

import psycopg2
import config  # Load local env files before resolving the connection string.

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Run neon deploy or configure the backend environment.")
    return psycopg2.connect(database_url, connect_timeout=15)




def save_qa_history(session_id, question, answer):
    from embeddings import get_embedding

    question_embedding = get_embedding(question)
    vector_str = "[" + ",".join(str(x) for x in question_embedding) + "]"

    conn = get_db_connection()

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO qa_history (session_id, question, question_embedding, answer)
            VALUES (%s, %s, %s::vector, %s);
            """,
            (session_id, question, vector_str, answer),
        )

    conn.commit()
    conn.close()


def get_recent_qa_history(session_id, limit=10):
    conn = get_db_connection()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT question, answer, created_at
            FROM qa_history
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s;
            """,
            (session_id, limit),
        )

        rows = cur.fetchall()

    conn.close()

    # on remet dans l'ordre ancien -> récent pour le prompt
    rows.reverse()

    history = []
    for row in rows:
        history.append(
            {
                "question": row[0],
                "answer": row[1],
                "created_at": row[2],
            }
        )

    return history
