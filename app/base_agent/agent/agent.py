import re
from pathlib import Path
from typing import Any

from .actions.list_of_actions import LIST_OF_ACTIONS


def _extract_between(message: str, start_pattern: str, end_pattern: str) -> str:
    """Extrait un segment de texte entre deux motifs regex."""
    match = re.search(start_pattern + r"(.*?)" + end_pattern, message, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def build_action_plan(user_message: str) -> list[dict[str, Any]]:
    """Construit une liste d'actions à exécuter à partir du message utilisateur.

    Args:
        user_message: Demande en langage naturel.

    Returns:
        Une liste d'actions au format {"action": str, "params": list[Any]}.
    """
    print(f"[AGENT] Message utilisateur : {user_message}")
    normalized = user_message.lower().strip()
    actions_plan: list[dict[str, Any]] = []

    # Cas 1: création d'un document markdown puis ingestion.
    if "document" in normalized and "texte" in normalized and "ajoute" in normalized:
        doc_match = re.search(r"nomm[ée]\s+(.+?)\s+avec\s+ce\s+texte", user_message, flags=re.IGNORECASE)
        content_match = re.search(r"texte\s*:\s*(.+)$", user_message, flags=re.IGNORECASE | re.DOTALL)

        if doc_match and content_match:
            document_name = doc_match.group(1).strip().replace(" ", "_")
            text = content_match.group(1).strip()

            dataset_file = Path(__file__).resolve().parents[3].parent / "dataset" / f"{document_name}.md"
            actions_plan.append({"action": "create_markdown_file", "params": [document_name, text]})
            actions_plan.append({"action": "ingest_single_document_to_db", "params": [str(dataset_file)]})

            print("[AGENT] Action détectée : create_markdown_file + ingest_single_document_to_db")
            print(f"[AGENT] Paramètres extraits : document_name={document_name}")
            return actions_plan

    # Cas 2: création fichier générique.
    if "crée" in normalized and "fichier" in normalized:
        file_match = re.search(r"fichier\s+([a-zA-Z0-9_\-./]+)", user_message, flags=re.IGNORECASE)
        content = _extract_between(user_message, r"contenu\s*:\s*", r"$")

        if file_match:
            file_name = file_match.group(1).strip()
            actions_plan.append({"action": "create_file", "params": [file_name, content]})
            print("[AGENT] Action détectée : create_file")
            print(f"[AGENT] Paramètres extraits : file_name={file_name}, content={content}")
            return actions_plan

    # Cas 3: suppression de fichier.
    if ("supprime" in normalized or "supprimer" in normalized) and "fichier" in normalized:
        file_match = re.search(r"fichier\s+([a-zA-Z0-9_\-./]+)", user_message, flags=re.IGNORECASE)
        if file_match:
            file_name = file_match.group(1).strip()
            actions_plan.append({"action": "delete_file", "params": [file_name]})
            print("[AGENT] Action détectée : delete_file")
            print(f"[AGENT] Paramètres extraits : file_name={file_name}")
            return actions_plan

    # Cas 4: renommage de fichier.
    if "renomme" in normalized and "fichier" in normalized:
        match = re.search(
            r"fichier\s+([a-zA-Z0-9_\-./]+)\s+(?:en|vers)\s+([a-zA-Z0-9_\-./]+)",
            user_message,
            flags=re.IGNORECASE,
        )
        if match:
            old_name, new_name = match.group(1).strip(), match.group(2).strip()
            actions_plan.append({"action": "rename_file", "params": [old_name, new_name]})
            print("[AGENT] Action détectée : rename_file")
            print(f"[AGENT] Paramètres extraits : old_name={old_name}, new_name={new_name}")
            return actions_plan

    print("[AGENT] Aucune action reconnue")
    return actions_plan


def execute_action_plan(actions_plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Exécute un plan d'actions et retourne les résultats."""
    results: list[dict[str, Any]] = []

    for call in actions_plan:
        action_name = call["action"]
        params = call.get("params", [])
        print(f"[AGENT] Exécution action : {action_name}")

        try:
            action_fn = LIST_OF_ACTIONS[action_name]
            result = action_fn(*params)
            results.append({"action": action_name, "status": "ok", "result": result})
            print(f"[AGENT] Action terminée : {action_name}")
        except Exception as exc:
            print(f"[AGENT][ERROR] Erreur pendant {action_name}: {exc}")
            results.append({"action": action_name, "status": "error", "error": str(exc)})
            break

    return results


def process_user_message(user_message: str) -> dict[str, Any]:
    """Pipeline agent complet : parse -> actions -> réponse finale."""
    plan = build_action_plan(user_message)

    if not plan:
        return {
            "message": "Je n'ai pas compris l'action demandée. Essaie une phrase plus explicite.",
            "actions": [],
            "results": [],
        }

    results = execute_action_plan(plan)

    has_error = any(item["status"] == "error" for item in results)
    final_message = "Actions exécutées avec succès." if not has_error else "Une erreur est survenue pendant l'exécution."

    return {
        "message": final_message,
        "actions": plan,
        "results": results,
    }
