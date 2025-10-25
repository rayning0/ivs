#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
exec gunicorn -w 1 -k uvicorn.workers.UvicornWorker app:app --bind 0.0.0.0:8000
