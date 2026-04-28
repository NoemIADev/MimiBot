from pathlib import Path
import sys

# On ajoute dynamiquement le dossier app/ au PYTHONPATH pour les imports runtime.
APP_DIR = Path(__file__).resolve().parents[3]
if str(APP_DIR) not in sys.path:
    sys.path.append(str(APP_DIR))


def create_markdown_file(document_name: str, text: str) -> str:
    """Crée un fichier markdown dans le dossier dataset du projet.

    Args:
        document_name: Nom du document sans extension.
        text: Contenu texte du markdown.

    Returns:
        Le chemin absolu du fichier markdown créé.
    """
    print(f"[ACTION] Création d'un markdown dataset : {document_name}")

    project_root = APP_DIR.parent
    dataset_dir = project_root / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    safe_name = document_name.strip().replace(" ", "_")
    file_path = dataset_dir / f"{safe_name}.md"

    file_path.write_text(text.strip() + "\n", encoding="utf-8")
    print(f"[OK] Markdown créé : {file_path}")
    return str(file_path)


def ingest_single_document_to_db(document_name: str) -> int:
    """
    Ingère un document markdown depuis le dossier dataset.

    Args:
        document_name: nom du fichier (ex: "test" ou "test.md")

    Returns:
        nombre de chunks insérés
    """
    from ingest_script import ingest_single_document

    print(f"[ACTION] Ingestion demandée : {document_name}")
    
    project_root = APP_DIR.parent
    dataset_dir = project_root / "dataset"

    # on ajoute .md si besoin
    if not document_name.endswith(".md"):
        document_name += ".md"

    file_path = dataset_dir / document_name

    if not file_path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    print(f"[ACTION] Ingestion du fichier : {file_path}")

    inserted_chunks = ingest_single_document(file_path)

    print(f"[OK] Document ajouté ({inserted_chunks} chunks)")
    return inserted_chunks
