#!/bin/bash
set -e

echo "🛡️  Warstwa Anonimizacji — uruchamianie..."
echo ""

# Start backend
echo "📦 Backend (FastAPI) na http://localhost:8000"
cd "$(dirname "$0")/backend"
../.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "🖥️  Frontend (Next.js) na http://localhost:3000"
cd "$(dirname "$0")/frontend"
npm run dev -- --port 3000 &
FRONTEND_PID=$!

echo ""
echo "✅ Otwórz http://localhost:3000 w przeglądarce"
echo "   Ctrl+C aby zatrzymać"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
