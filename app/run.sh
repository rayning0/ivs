#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
source ../.venv313/bin/activate
export TOKENIZERS_PARALLELISM=false

# Kill any existing gunicorn processes
pkill -f gunicorn || true

exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000 --timeout 500
