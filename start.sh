#!/bin/bash
set -e

# Start FastAPI backend (internal only)
cd /app/backend
uvicorn main:app --host 127.0.0.1 --port 8000 &

# Start Next.js frontend (exposed port — Railway/Render set $PORT)
cd /app/frontend
exec npx next start --port "${PORT:-3000}"
