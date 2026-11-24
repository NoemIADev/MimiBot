import json
import logging
import os
import sys
from contextlib import aclosing, asynccontextmanager, closing

import anyio
from limit import compter_message
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from db import get_db_connection, save_qa_history, get_recent_qa_history
from rag import retrieve_bdd, build_prompt, stream_gpt, rewrite_query
load_dotenv()

app = FastAPI()
logger = logging.getLogger(__name__)

# Les attentes de quota ont leur propre limite de workers pour laisser les
# transactions déjà ouvertes avancer et libérer leurs verrous.
quota_workers = anyio.CapacityLimiter(8)


class MimiStream(StreamingResponse):
    async def __call__(self, scope, receive, send):
        async with anyio.create_task_group() as tasks:
            async def watch_disconnect():
                while (await receive())["type"] != "http.disconnect":
                    pass
                tasks.cancel_scope.cancel()

            tasks.start_soon(watch_disconnect)
            try:
                await self.stream_response(send)
            finally:
                tasks.cancel_scope.cancel()
                with anyio.CancelScope(shield=True):
                    await self.body_iterator.aclose()


@asynccontextmanager
async def transaction_reponse(session_id, adresse_ip):
    transaction = compter_message(session_id, adresse_ip)
    connexion = await anyio.to_thread.run_sync(transaction.__enter__, limiter=quota_workers)
    try:
        yield connexion
        await anyio.lowlevel.checkpoint()
    finally:
        exception = sys.exc_info()
        with anyio.CancelScope(shield=True):
            await anyio.to_thread.run_sync(transaction.__exit__, *exception)


def stream_event(event_type, **data):
    return json.dumps({"type": event_type, **data}, ensure_ascii=False) + "\n"


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
    adresse_ip = request.client.host

    async def events():
        try:
            async with transaction_reponse(data.session_id, adresse_ip) as connexion:
                history = await anyio.to_thread.run_sync(get_recent_qa_history, data.session_id)
                rewritten_query = await anyio.to_thread.run_sync(rewrite_query, data.question, history)
                print("\n=== QUESTION ORIGINALE ===")
                print(data.question)
                print("\n=== QUESTION REFORMULÉE ===")
                print(rewritten_query)

                chunks = await anyio.to_thread.run_sync(retrieve_bdd, rewritten_query)
                system_prompt, user_prompt = build_prompt(
                    question=data.question,
                    chunks=chunks,
                    history=history,
                )

                parts = []
                async with aclosing(stream_gpt(system_prompt, user_prompt)) as stream:
                    async for part in stream:
                        if not parts:
                            part = part.lstrip()
                        if part:
                            parts.append(part)
                            yield stream_event("delta", text=part)

                answer = "".join(parts).rstrip()
                if not answer:
                    raise HTTPException(status_code=502, detail="Mimi a renvoyé une réponse vide.")

                await anyio.to_thread.run_sync(
                    save_qa_history, data.session_id, data.question, answer, connexion
                )
            yield stream_event("done")
        except HTTPException as exc:
            yield stream_event("error", message=exc.detail)
        except Exception:
            logger.exception("Échec de la réponse de Mimi")
            yield stream_event("error", message="Désolée, je n’ai pas pu répondre pour le moment. Tu peux réessayer dans un instant.")

    return MimiStream(
        events(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )
