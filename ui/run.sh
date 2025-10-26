#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
source ../.venv313/bin/activate
exec streamlit run app.py
