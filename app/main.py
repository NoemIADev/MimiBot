import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import get_db_connection, save_qa_history, get_recent_qa_history
from rag import retrieve_bdd, build_prompt, ask_gpt

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


@app.post("/ask_mimi")
def ask_mimi(data: QuestionRequest):
    history = get_recent_qa_history(data.session_id)
    chunks = retrieve_bdd(data.question)

    system_prompt, user_prompt = build_prompt(
        question=data.question,
        chunks=chunks,
        history=history,
    )

    answer = ask_gpt(system_prompt, user_prompt)

    save_qa_history(data.session_id, data.question, answer)

    return {"response": answer}