from pathlib import Path  # pour gérer les chemins proprement

from dotenv import load_dotenv

from db import get_db_connection  # ma connexion PostgreSQL
from embeddings import get_embedding

load_dotenv()


def reset_documents_and_chunks(conn):
    """Supprime tous les documents existants (et leurs chunks)."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM documents;")
    conn.commit()


def get_dataset_files() -> list[Path]:
    """Retourne tous les fichiers .md du dossier dataset à la racine projet."""
    base_dir = Path(__file__).resolve().parent.parent
    dataset_dir = base_dir / "dataset"

    if not dataset_dir.exists():
        raise Exception("Le dossier dataset n'existe pas")

    return list(dataset_dir.glob("*.md"))


def read_file(file_path: Path) -> str:
    """Lit un fichier markdown et retourne son contenu texte."""
    return file_path.read_text(encoding="utf-8")


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Découpe un texte en morceaux avec un chevauchement."""
    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks


def insert_document(conn, title: str, source_name: str, content: str) -> int:
    """Insère un document en base et retourne son ID."""
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


def insert_chunk(conn, document_id: int, chunk_index: int, content: str, embedding: list[float]) -> None:
    """Insère un chunk en base avec son embedding."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chunks (document_id, chunk_index, content, embedding)
            VALUES (%s, %s, %s, %s);
            """,
            (document_id, chunk_index, content, embedding),
        )


def delete_document_by_source_name(conn, source_name: str) -> None:
    """Supprime le document existant pour un même fichier source (évite les doublons)."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM documents WHERE source_name = %s;", (source_name,))


def ingest_document_file(conn, file_path: Path) -> int:
    """Ingère un document markdown unique dans la base et retourne le nombre de chunks.

    Args:
        conn: Connexion psycopg2 déjà ouverte.
        file_path: Chemin du fichier markdown à ingérer.

    Returns:
        Nombre de chunks insérés pour ce document.
    """
    print(f"[INGEST] Début ingestion document: {file_path}")

    content = read_file(file_path)
    if not content.strip():
        print("[INGEST][WARN] Fichier vide, ingestion ignorée")
        return 0

    delete_document_by_source_name(conn, file_path.name)

    document_id = insert_document(
        conn,
        title=file_path.stem,
        source_name=file_path.name,
        content=content,
    )

    chunks = chunk_text(content)
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        insert_chunk(conn, document_id, i, chunk, embedding)

    conn.commit()
    print(f"[INGEST] Fin ingestion document: {file_path.name} ({len(chunks)} chunks)")
    return len(chunks)


def ingest_single_document(file_path: Path) -> int:
    """Ingère un seul document markdown dans PostgreSQL, sans reset global.

    Args:
        file_path: Chemin vers un fichier markdown.

    Returns:
        Le nombre de chunks insérés en base pour ce document.
    """
    print(f"[INGEST] Demande d'ingestion d'un seul document: {file_path}")
    resolved_path = file_path.expanduser().resolve()

    if not resolved_path.exists():
        raise FileNotFoundError(f"Le fichier n'existe pas: {resolved_path}")

    conn = get_db_connection()
    try:
        inserted_chunks = ingest_document_file(conn, resolved_path)
        return inserted_chunks
    finally:
        conn.close()
        print("[INGEST] Connexion base fermée")


def run_ingest() -> None:
    """Pipeline complet d'ingestion (avec reset total de la base documents/chunks)."""
    conn = get_db_connection()
    reset_documents_and_chunks(conn)

    files = get_dataset_files()
    print(f"{len(files)} fichiers trouvés")

    for file_path in files:
        print(f"\nTraitement : {file_path.name}")
        ingest_document_file(conn, file_path)

    conn.close()


if __name__ == "__main__":
    run_ingest()
