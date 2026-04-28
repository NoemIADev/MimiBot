"""Registre central des actions exécutables par l'agent."""

from .create_file import create_file
from .delete_file import delete_file
from .rename_file import rename_file
from .mimi_actions import create_markdown_file, ingest_single_document_to_db


LIST_OF_ACTIONS = {
    "create_file": create_file,
    "delete_file": delete_file,
    "rename_file": rename_file,
    "create_markdown_file": create_markdown_file,
    "ingest_single_document_to_db": ingest_single_document_to_db,
}