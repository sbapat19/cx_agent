#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

echo "Starting backend (FastAPI) on http://localhost:${BACKEND_PORT}"
echo "Starting frontend (Vite) on http://localhost:${FRONTEND_PORT}"
echo
echo "Backend:  http://localhost:${BACKEND_PORT}"
echo "Frontend: http://localhost:${FRONTEND_PORT}"
echo "Press Ctrl+C to stop both servers"
echo

cleanup() {
  echo
  echo "Stopping servers..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(
  cd "${ROOT_DIR}/backend"
  pipenv install --dev >/dev/null
  exec pipenv run uvicorn main:app --reload --host 0.0.0.0 --port "${BACKEND_PORT}"
) &
BACKEND_PID=$!

(
  cd "${ROOT_DIR}/frontend"
  npm install >/dev/null
  exec npm run dev -- --port "${FRONTEND_PORT}"
) &
FRONTEND_PID=$!

wait
