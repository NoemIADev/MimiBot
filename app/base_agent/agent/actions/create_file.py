from pathlib import Path


def create_file(file_name: str, content: str = "") -> str:
    """Crée un fichier texte et retourne son chemin absolu.

    Args:
        file_name: Chemin du fichier à créer (relatif ou absolu).
        content: Contenu à écrire dans le fichier.

    Returns:
        Le chemin absolu du fichier créé.
    """
    print(f"[ACTION] Création du fichier : {file_name}")
    file_path = Path(file_name).expanduser().resolve()

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")

    print(f"[OK] Fichier créé : {file_path}")
    return str(file_path)
