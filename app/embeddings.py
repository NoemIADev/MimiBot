import os
import config  # Load .env.local / .env without overriding Azure settings.
from openai import OpenAI

# charge explicitement le .env à la racine du projet

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
)

def get_embedding(text):
    dimensions = os.getenv("OPENROUTER_EMBEDDING_DIMENSIONS")
    options = {"dimensions": int(dimensions)} if dimensions else {}
    response = client.embeddings.create(
        model=os.getenv("OPENROUTER_EMBEDDING_MODEL"),
        input=text,
        **options,
    )
    embedding = response.data[0].embedding
    if dimensions and len(embedding) != int(dimensions):
        raise ValueError(f"Embedding provider returned {len(embedding)} dimensions; expected {dimensions}")
    return embedding
