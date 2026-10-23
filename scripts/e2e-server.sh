#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="${E2E_DATA_DIR:-/tmp/cad-agent-e2e}"
rm -rf "$DATA"
mkdir -p "$DATA"
export DATA_DIR="$DATA"
export STORAGE_DIR="$DATA/storage"
export DATABASE_URL="sqlite:///$DATA/app.db"
export EXECUTION_MODE=inline
export AUTO_CREATE_SCHEMA=true
exec "$ROOT/.venv/bin/uvicorn" app.main:app --app-dir "$ROOT/backend" --host 127.0.0.1 --port 8000
