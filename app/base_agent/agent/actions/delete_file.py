from pathlib import Path


def delete_file(file_name: str) -> str:
    """Supprime un fichier existant.

    Args:
        file_name: Chemin du fichier à supprimer.

    Returns:
        Un message décrivant le résultat de la suppression.
    """
    print(f"[ACTION] Suppression du fichier : {file_name}")
    file_path = Path(file_name).expanduser().resolve()

    if not file_path.exists():
        message = f"Le fichier '{file_path}' n'existe pas."
        print(f"[ACTION][WARN] {message}")
        return message

    file_path.unlink()
    message = f"Fichier supprimé : {file_path}"
    print(f"[OK] {message}")
    return message
