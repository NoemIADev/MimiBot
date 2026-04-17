"""Front Streamlit minimal pour parler à l'API agent de démo."""

import os

import requests
import streamlit as st


API_URL = os.getenv("AGENT_API_URL", "http://127.0.0.1:8010/run")


st.set_page_config(page_title="Mimi Agent Demo", page_icon="🤖")
st.title("🤖 Mimi Agent Demo")
st.caption("Interface simple pour tester les actions de l'agent")

if "history" not in st.session_state:
    st.session_state.history = []

user_input = st.text_area(
    "Message utilisateur",
    placeholder="Ex: Ajoute un document nommé test_agent avec ce texte : Bonjour ceci est un test",
    height=120,
)

if st.button("Envoyer au bot"):
    if not user_input.strip():
        st.warning("Merci d'écrire un message.")
    else:
        payload = {"message": user_input}
        st.write("Payload envoyé :", payload)

        try:
            response = requests.post(API_URL, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            st.session_state.history.append({"request": payload, "response": data})
            st.success("Réponse reçue")
            st.json(data)
        except Exception as exc:
            st.error(f"Erreur pendant l'appel API : {exc}")

st.subheader("Historique local")
for idx, item in enumerate(reversed(st.session_state.history), start=1):
    st.markdown(f"### Échange {idx}")
    st.write("Requête :", item["request"])
    st.json(item["response"])
