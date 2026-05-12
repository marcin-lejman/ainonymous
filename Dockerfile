# Combined single-container build for Railway / Render deployment.
# For local dev, use docker-compose.yml instead.

# --- Stage 1: Build the Next.js frontend ---
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
ENV NEXT_PUBLIC_API_URL=
RUN npm run build

# --- Stage 2: Python runtime with Node ---
FROM python:3.11-slim

# Install Node.js (needed for `next start`)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps + spaCy models
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt && \
    python -m spacy download pl_core_news_lg && \
    python -m spacy download en_core_web_lg

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend (only what next start needs)
COPY --from=frontend-build /app/.next ./frontend/.next
COPY --from=frontend-build /app/node_modules ./frontend/node_modules
COPY --from=frontend-build /app/package.json ./frontend/package.json
COPY --from=frontend-build /app/next.config.ts ./frontend/next.config.ts
COPY frontend/public ./frontend/public

# Data directory
RUN mkdir -p /data

COPY start.sh .
RUN chmod +x start.sh

EXPOSE 3000

CMD ["./start.sh"]
