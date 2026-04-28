import os

def rename_file(old_name, new_name):
    """
    Renomme un fichier existant.

    Args:
        old_name: ancien nom du fichier
        new_name: nouveau nom du fichier
    """
    if os.path.exists(old_name):
        os.rename(old_name, new_name)
        return f"Fichier renommé : {old_name} -> {new_name}"
    else:
        return f"Le fichier n'existe pas : {old_name}"