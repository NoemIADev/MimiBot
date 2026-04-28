# lancer api
cd app
``uvicorn base_agent.agent.AgentApi:app --host 0.0.0.0 --port 8010 --reload

# lancer front 

``streamlit run app/base_agent/agent_demo_streamlit.py