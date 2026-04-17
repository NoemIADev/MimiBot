from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any

from agent.agent import do


app = FastAPI()


class ActionCall(BaseModel):
    action: str
    params: list[Any]


class AgentRequest(BaseModel):
    actions: list[ActionCall]


@app.get("/")
def read_root():
    return {"message": "API agent active"}


@app.post("/run")
def run_agent(request: AgentRequest):
    do([action.model_dump() for action in request.actions])
    return {
        "message": "Actions exécutées avec succès",
        "nb_actions": len(request.actions)
    }