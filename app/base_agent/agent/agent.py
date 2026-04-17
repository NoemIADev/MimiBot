from actions.list_of_actions import LIST_OF_ACTIONS


def do(actions_list: list[dict]):
    for call in actions_list:
        LIST_OF_ACTIONS[call["action"]](*call["params"])