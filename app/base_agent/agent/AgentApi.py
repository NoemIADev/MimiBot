from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from .agent import process_user_message

app = FastAPI(title="Mimi Agent Demo API")


class AgentMessageRequest(BaseModel):
    """Body attendu pour exécuter une demande utilisateur sur l'agent."""

    message: str


@app.get("/")
def read_root() -> dict[str, str]:
    """Endpoint de santé de l'API agent."""
    return {"message": "API agent active"}


@app.post("/run")
def run_agent(request: AgentMessageRequest) -> dict[str, Any]:
    """Exécute le pipeline agent complet à partir d'un message utilisateur."""
    print(f"[API AGENT] Body reçu : {request.model_dump()}")
    response = process_user_message(request.message)
    print(f"[API AGENT] Réponse agent : {response}")
    return response
