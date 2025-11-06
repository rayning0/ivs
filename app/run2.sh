#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
source ../.venv/bin/activate
export TOKENIZERS_PARALLELISM=false

# Kill any existing gunicorn processes
pkill -f gunicorn || true

# Bind ONLY to localhost; Nginx /api/ will proxy to this
exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker app:app \
  --bind 127.0.0.1:8000 \
  --timeout 500 \
  --access-logfile - \
  --error-logfile -
