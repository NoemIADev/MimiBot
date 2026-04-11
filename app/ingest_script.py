from pathlib import Path  # pour gérer les chemins proprement
from db import get_db_connection  # ma connexion PostgreSQL
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from embeddings import get_embedding

load_dotenv()


def reset_documents_and_chunks(conn):
    """
    Supprime les documents existants.
    Les chunks liés seront supprimés automatiquement
    grâce au ON DELETE CASCADE.
    """
    with conn.cursor() as cur:
        cur.execute("DELETE FROM documents;")

    conn.commit()


# =========================
# RÉCUPÉRER LES FICHIERS
# =========================
def get_dataset_files():
    """
    Va chercher tous les fichiers .md dans le dossier dataset
    """
    # __file__ = chemin de ce fichier (ingest_script.py)
    # parent = dossier app/
    # parent.parent = racine du projet
    base_dir = Path(__file__).resolve().parent.parent

    # chemin vers dataset/
    dataset_dir = base_dir / "dataset"

    if not dataset_dir.exists():
        raise Exception("Le dossier dataset n'existe pas")

    # récupère tous les fichiers .md
    files = list(dataset_dir.glob("*.md"))

    return files


# =========================
# LIRE UN FICHIER
# =========================
def read_file(file_path):
    """
    Lit un fichier markdown et retourne son contenu
    """
    return file_path.read_text(encoding="utf-8")


# =========================
# CHUNKER LE TEXTE
# =========================
def chunk_text(text, chunk_size=800, overlap=100):
    """
    Découpe le texte en morceaux

    chunk_size = taille max
    overlap = chevauchement pour garder le contexte
    """
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk.strip())

        # on avance avec overlap
        start += chunk_size - overlap

    return chunks


# =========================
# INSERT DOCUMENT
# =========================
def insert_document(conn, title, source_name, content):
    """
    Insère un document complet en base
    retourne son ID
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO documents (title, source_name, content)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (title, source_name, content),
        )

        document_id = cur.fetchone()[0]

    conn.commit()
    return document_id


# =========================
# INSERT CHUNK
# =========================
def insert_chunk(conn, document_id, chunk_index, content, embedding):
    """
    Insère un chunk en base (sans embedding pour V1)
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chunks (document_id, chunk_index, content, embedding)
            VALUES (%s, %s, %s, %s);
            """,
            (document_id, chunk_index, content, embedding),
        )

    conn.commit()


# =========================
# PIPELINE COMPLET
# =========================
def run_ingest():
    """
    Pipeline complet :

    - récupère les fichiers
    - insère documents
    - découpe en chunks
    - insère chunks
    """

    conn = get_db_connection()
    #suprime avant nouveau ingest
    reset_documents_and_chunks(conn)

    files = get_dataset_files()

    print(f"{len(files)} fichiers trouvés")

    for file_path in files:
        print(f"\nTraitement : {file_path.name}")

        # lire le contenu
        content = read_file(file_path)

        if not content.strip():
            print("Fichier vide -> skip")
            continue

        # créer document
        document_id = insert_document(
            conn,
            title=file_path.stem,      # nom sans .md
            source_name=file_path.name,
            content=content
        )

        # chunk
        chunks = chunk_text(content)

        # insert chunks + embedding
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            insert_chunk(conn, document_id, i, chunk, embedding)

        print(f"OK -> {len(chunks)} chunks")

    conn.close()


# =========================
# LANCEMENT SCRIPT
# =========================
if __name__ == "__main__":
    run_ingest()