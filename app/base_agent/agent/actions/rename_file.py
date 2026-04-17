import os

def rename_file(old_name, new_name):
    if os.path.exists(old_name):
        os.rename(old_name, new_name)
    else:
        print(f"Le fichier '{old_name}' n'existe pas.")