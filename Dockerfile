# Single service: builds the React UI, then serves UI + API from FastAPI. Works on Render, Fly.io, Railway, Cloud Run.
FROM node:20-slim AS ui
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_BRAND_TITLE=Beauty Assistant
ENV VITE_BRAND_TITLE=$VITE_BRAND_TITLE
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" python-dotenv langgraph langchain-core langchain-google-genai sqlalchemy certifi "psycopg[binary]"
COPY backend/ ./backend/
COPY --from=ui /ui/dist ./frontend/dist
ENV APP_ENV=production PYTHONUNBUFFERED=1
WORKDIR /app/backend
# GOOGLE_API_KEY and DATABASE_URL come from the host's environment settings, never from the image.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
