def create_file(file_name):
    """
    Crée un fichier vide.

    Args:
        file_name: nom du fichier à créer
    """
    with open(file_name, "w"):
        pass

    return f"Fichier créé : {file_name}"