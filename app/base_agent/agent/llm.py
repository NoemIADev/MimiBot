import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from openai import AzureOpenAI
from pydantic import BaseModel

from agent.agent import get_actions

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)

app = FastAPI(title="LLM API")

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

AGENT_API_URL = "http://127.0.0.1:8000/agent"


class UserMessageRequest(BaseModel):
    """
    Message envoyé par l'utilisateur.
    """
    message: str


def call_llm(user_message: str):
    """
    Envoie le message utilisateur au LLM pour obtenir une liste d'actions JSON.
    """
    actions = get_actions()

    json_example = """
[
    {
        "name": "create_file",
        "param": ["test.txt"]
    }
]
"""

    history = [
        {
            "role": "system",
            "content": f"""
You are a helpful assistant.
You must choose actions only from this list: {actions}.

Return only valid JSON.
The JSON must be an array of actions.
Use this format:
{json_example}
"""
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    response = client.chat.completions.create(
        messages=history,
        max_tokens=1000,
        temperature=0,
        top_p=1,
        model="gpt-5-chat"
    )

    return response.choices[0].message.content


@app.get("/")
def read_root():
    """
    Vérifie que l'API LLM fonctionne.
    """
    return {"message": "API LLM active"}


@app.post("/run")
def run_pipeline(request: UserMessageRequest):
    """
    Reçoit une question utilisateur, appelle le LLM,
    envoie les actions à l'API agent, puis retourne le résultat final.
    """
    print("[LLM API] Question reçue :", request.message)

    llm_output = call_llm(request.message)
    print("[LLM API] Réponse brute du LLM :", llm_output)

    try:
        actions_json = json.loads(llm_output)
    except Exception as e:
        print("[LLM API] Erreur parsing JSON :", e)
        return {
            "response": "Le LLM n'a pas renvoyé un JSON valide.",
            "llm_output": llm_output
        }

    print("[LLM API] JSON envoyé à POST /agent :", actions_json)

    try:
        agent_response = requests.post(AGENT_API_URL, json=actions_json, timeout=60)
        agent_response.raise_for_status()
        agent_data = agent_response.json()
    except Exception as e:
        print("[LLM API] Erreur appel POST /agent :", e)
        return {
            "response": "Erreur pendant l'appel à l'API agent.",
            "error": str(e)
        }

    print("[LLM API] Réponse reçue de POST /agent :", agent_data)

    return {
        "response": "Pipeline exécutée avec succès.",
        "llm_actions": actions_json,
        "agent_result": agent_data
    }