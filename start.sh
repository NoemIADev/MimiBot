#!/bin/bash

echo "Activation du venv..."
source mimivenv/bin/activate

echo "Lancement de l'API FastAPI..."
cd app
uvicorn main:app --reload &
API_PID=$!

echo "Lancement du front Vite..."
cd ../Frontend
npm run dev &
FRONT_PID=$!

echo "API lancée sur http://127.0.0.1:8000"
echo "Front lancé sur http://127.0.0.1:5173"

trap "echo 'Arrêt des serveurs...'; kill $API_PID $FRONT_PID" EXIT

wait