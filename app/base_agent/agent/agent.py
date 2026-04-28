import inspect
from agent.actions.list_of_actions import LIST_OF_ACTIONS


def do_actions(actions):
    """
    Exécute une liste d'actions et retourne les résultats.
    """
    results = []

    for action in actions:
        result = LIST_OF_ACTIONS[action.name](*action.param)
        results.append(result)

    return results


def get_actions():
    """
    Retourne la liste des actions disponibles avec leur signature et leur docstring.
    """
    list_signature = []

    for key, value in LIST_OF_ACTIONS.items():
        signature = {}
        signature["name"] = key
        signature["params"] = str(inspect.signature(value))
        signature["doc"] = value.__doc__

        list_signature.append(signature)

    return list_signature