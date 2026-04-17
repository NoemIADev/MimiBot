from actions.create_file import create_file
from agent import do
from actions.delete_file import delete_file
from actions.rename_file import rename_file


# create_file("coucou.txt")

test_list = [
    
    {
        "action": "create_file",
        "params": ["coucou.txt"]
    },
{
        "action": "rename_file",
        "params": ["coucou.txt","salut.txt"]
    },
{
        "action": "delete_file",
        "params": ["salut.txt"]
    },
{
        "action": "create_file",
        "params": ["coucou.txt"]
    }
]

do(test_list)
