import os

def delete_file(file_name):
    """
    Supprime un fichier existant.

    Args:
        file_name: nom du fichier à supprimer
    """
    if os.path.exists(file_name):
        os.remove(file_name)
        return f"Fichier supprimé : {file_name}"
    else:
        return f"Le fichier n'existe pas : {file_name}"