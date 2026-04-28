import os

import requests
import streamlit as st


API_URL = "http://127.0.0.1:8010/run"


st.set_page_config(page_title="Agent Chat", page_icon="🤖")
st.title("🤖 Agent Chat")
st.caption("Interface simple pour parler au bot")


if "messages" not in st.session_state:
    st.session_state.messages = []


# affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# champ de saisie utilisateur
user_input = st.chat_input("Écris ton message ici...")


if user_input:
    # on ajoute le message user dans l'historique
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # on affiche directement le message user
    with st.chat_message("user"):
        st.write(user_input)

    try:
        payload = {"message": user_input}

        response = requests.post(API_URL, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        # on récupère la réponse du bot
        bot_response = data.get("response", "Pas de réponse renvoyée par l'API.")

    except Exception as exc:
        bot_response = f"Erreur pendant l'appel API : {exc}"

    # on ajoute la réponse bot dans l'historique
    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_response
    })

    # on affiche la réponse bot
    with st.chat_message("assistant"):
        st.write(bot_response)