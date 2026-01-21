#!/bin/bash

# Kill child processes on exit
trap 'kill $(jobs -p)' EXIT

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Start Backend
echo "Starting KOR Kanban Backend..."
cd server
source ../../../.venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 3001 --reload &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 2

# Start Frontend
echo "Starting KOR Kanban Frontend..."
cd ..
export FRONTEND_PORT=3000
export BACKEND_PORT=3001
export VITE_OPEN=true
npm run dev

wait $BACKEND_PID
