#!/bin/bash

echo "Lancement API agent..."
uvicorn agent.AgentApi:app --reload --port 8000 &

echo "Lancement API LLM..."
uvicorn agent.llm:app --reload --port 8010 &

echo "Lancement front Streamlit..."
streamlit run agent_demo_streamlit.py &

echo "C'est lancé."
echo "API agent : http://127.0.0.1:8000"
echo "API LLM   : http://127.0.0.1:8010"
echo "Front     : http://127.0.0.1:8501"