import os
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

from embeddings import get_embedding
from db import get_db_connection

# charge explicitement le .env à la racine du projet
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# client Azure OpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version="2024-02-01"
)

def retrieve_bdd(question, search_limit=15, final_limit=6, max_distance=0.75):
    # embedding de la question
    question_embedding = get_embedding(question)

    # format attendu par pgvector
    vector_str = "[" + ",".join(str(x) for x in question_embedding) + "]"

    conn = get_db_connection()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                d.title,
                c.chunk_index,
                c.content,
                c.embedding <=> %s::vector AS distance
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            ORDER BY distance ASC
            LIMIT %s;
            """,
            (vector_str, search_limit)
        )
        rows = cur.fetchall()

    conn.close()

    results = []
    for row in rows:
        results.append(
            {
                "title": row[0],
                "chunk_index": row[1],
                "content": row[2],
                "distance": row[3]
            }
        )

    filtered_results = [
        chunk for chunk in results
        if chunk["distance"] <= max_distance
    ]

    return filtered_results[:final_limit]


def build_prompt(question, chunks, history):
    # historique conversationnel
    if not history:
        history_text = "Aucun historique de conversation."
    else:
        history_parts = []
        for item in history:
            part = (
                f"Utilisateur : {item['question']}\n"
                f"Mimi : {item['answer']}"
            )
            history_parts.append(part)

        history_text = "\n\n".join(history_parts)

    # contexte RAG
    if not chunks:
        context = "Aucune information trouvée dans la base."
    else:
        context_parts = []

        for chunk in chunks:
            part = (
                f"Document : {chunk['title']}\n"
                f"Chunk : {chunk['chunk_index']}\n"
                f"Texte : {chunk['content']}"
            )
            context_parts.append(part)

        context = "\n\n---\n\n".join(context_parts)

    system_prompt = """
Tu es Mimi, l’assistante de Noémie.

Ta mission est d’aider les visiteurs à découvrir Noémie, son parcours, ses compétences et ses projets.

Ton style :
- Tu es enjouée, énergique, accueillante et naturelle.
- Tu as une petite personnalité chaleureuse et motivante.
- Tu restes professionnelle, mais pas froide ni robotique.
- Tu réponds de façon simple, fluide et agréable.

Règles de réponse :
- Réponds uniquement à partir du contexte fourni.
- Ne fabrique jamais d’informations.
- Si l’information n’est pas présente dans le contexte, dis :
  "Désolée, je ne peux pas t’aider avec ça pour le moment, mais je t’invite à prendre contact avec ma créatrice directement sur LinkedIn : www.linkedin.com/in/noemie-majerus-devia"
- Tes réponses doivent rester courtes.
- Fais en général un seul paragraphe.
- Évite les réponses trop longues.
- Ne dépasse pas environ 10 à 15 phrases maximum sauf si l'utilisateur demande une réponse plus longue.
- Quand c’est pertinent, termine par une ouverture naturelle comme :
  "Tu veux en savoir plus sur ce sujet ?"
  ou
  "Je peux aussi te donner plus de détails si tu veux."
- N’utilise jamais de markdown dans tes réponses.
- N’écris pas de gras, pas de listes markdown, pas de crochets autour des liens.
- Quand tu donnes un lien, écris-le une seule fois, proprement.

Si la question porte sur les projets :
- donne une vue globale
- ne te limite pas à un seul projet
- mentionne plusieurs types de projets si possible

Tu dois donner envie d’en apprendre plus sur Noémie, tout en restant concise et honnête.
""".strip()

    user_prompt = f"""
Historique de conversation :
{history_text}

Contexte :
{context}

Question actuelle :
{question}
""".strip()

    return system_prompt, user_prompt


def ask_gpt(system_prompt, user_prompt):
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


def ask_mimi_rag(question):
    chunks = retrieve_bdd(question)

    print("\n=== CHUNKS TROUVÉS ===")
    for chunk in chunks:
        print(
            f"- {chunk['title']} | chunk {chunk['chunk_index']} | distance {chunk['distance']}"
        )

    system_prompt, user_prompt = build_prompt(question, chunks, history=[])

    answer = ask_gpt(system_prompt, user_prompt)

    return answer