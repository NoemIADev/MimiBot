from fastapi import FastAPI
from pydantic import BaseModel

from agent.agent import do_actions

app = FastAPI(title="Agent Execution API")


class ActionType(BaseModel):
    """
    Représente une action à exécuter.
    """
    name: str
    param: list[str | int | tuple]


@app.get("/")
def read_root():
    """
    Vérifie que l'API agent fonctionne.
    """
    return {"message": "API agent active"}


@app.post("/agent")
def run_actions(list_of_actions: list[ActionType]):
    """
    Exécute une liste d'actions.
    """
    print("[POST AGENT] Body reçu :", list_of_actions)

    results = do_actions(list_of_actions)

    print("[POST AGENT] Résultats :", results)

    return {
        "message": "actions executees",
        "results": results
    }