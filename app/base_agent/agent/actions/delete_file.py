import os

def delete_file(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)
    else:
        print(f"Le fichier '{file_name}' n'existe pas.")