#!/usr/bin/env bash
# Run the whole app locally: backend on :8000, frontend on :5173. Open http://localhost:5173
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
[ -f .env ] || { echo "No .env found in $ROOT. Create it with GOOGLE_API_KEY=... (see .env.example)"; exit 1; }
exec ./start.sh
