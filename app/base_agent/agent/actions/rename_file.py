from pathlib import Path


def rename_file(old_name: str, new_name: str) -> str:
    """Renomme un fichier existant.

    Args:
        old_name: Ancien chemin du fichier.
        new_name: Nouveau chemin du fichier.

    Returns:
        Un message décrivant le résultat du renommage.
    """
    print(f"[ACTION] Renommage du fichier : {old_name} -> {new_name}")
    old_path = Path(old_name).expanduser().resolve()
    new_path = Path(new_name).expanduser().resolve()

    if not old_path.exists():
        message = f"Le fichier source '{old_path}' n'existe pas."
        print(f"[ACTION][WARN] {message}")
        return message

    new_path.parent.mkdir(parents=True, exist_ok=True)
    old_path.rename(new_path)

    message = f"Fichier renommé : {old_path} -> {new_path}"
    print(f"[OK] {message}")
    return message
