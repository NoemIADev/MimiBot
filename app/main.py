import os
from contextlib import closing
from limit import compter_message
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from db import get_db_connection, save_qa_history, get_recent_qa_history
from rag import retrieve_bdd, build_prompt, ask_gpt, rewrite_query
load_dotenv()

app = FastAPI()


def get_allowed_origins():
    """
    Lit les origines autorisées depuis la variable d'environnement ALLOWED_ORIGINS.
    Format attendu :
    ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,https://ton-front.com
    """
    origins = os.getenv("ALLOWED_ORIGINS", "")
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


allowed_origins = get_allowed_origins()
print("ALLOWED_ORIGINS LOADED =", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str
    session_id: str


@app.get("/")
def root():
    return {
        "message": "API Mimi OK",
        "allowed_origins": allowed_origins,
    }


@app.get("/health")
def health():
    """Check API/database readiness without calling embeddings or the LLM."""
    try:
        with closing(get_db_connection()) as conn:
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = '3s'")
                cur.execute("SELECT 1")
                if cur.fetchone() != (1,):
                    raise RuntimeError("Unexpected database health result")
    except Exception:
        # Never expose connection strings or database errors to the browser.
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "api": "ok", "database": "unavailable"},
            headers={"Cache-Control": "no-store"},
        )
    return JSONResponse(
        content={"status": "ok", "api": "ok", "database": "ok"},
        headers={"Cache-Control": "no-store"},
    )


@app.post("/ask_mimi")
def ask_mimi(data: QuestionRequest, request: Request):
    if request.client is None:
        raise HTTPException(status_code=503, detail="Adresse client indisponible.")
    with compter_message(data.session_id, request.client.host):
        history = get_recent_qa_history(data.session_id)

        rewritten_query = rewrite_query(data.question, history)
        print("\n=== QUESTION ORIGINALE ===")
        print(data.question)
        print("\n=== QUESTION REFORMULÉE ===")
        print(rewritten_query)

        chunks = retrieve_bdd(rewritten_query)

        system_prompt, user_prompt = build_prompt(
            question=data.question,
            chunks=chunks,
            history=history,
        )

        answer = ask_gpt(system_prompt, user_prompt)
        if not answer or not answer.strip():
            raise HTTPException(status_code=502, detail="Mimi a renvoyé une réponse vide.")

        save_qa_history(data.session_id, data.question, answer)

        return {"response": answer}
