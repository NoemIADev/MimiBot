from .create_file import create_file
from .delete_file import delete_file
from .rename_file import rename_file

LIST_OF_ACTIONS = {
    "create_file": create_file,
    "delete_file": delete_file,
    "rename_file": rename_file,
    
}