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


def ingest_single_document_to_db(file_path: str) -> int:
    """Ingère un document markdown unique dans PostgreSQL sans reset global.

    Args:
        file_path: Chemin du fichier markdown à ingérer.

    Returns:
        Le nombre de chunks insérés pour ce document.
    """
    # Import local pour éviter de charger ingest_script tant que non nécessaire.
    from ingest_script import ingest_single_document

    print(f"[ACTION] Ingestion du document en base : {file_path}")
    inserted_chunks = ingest_single_document(Path(file_path))
    print(f"[OK] Document ajouté avec succès ({inserted_chunks} chunks)")
    return inserted_chunks
