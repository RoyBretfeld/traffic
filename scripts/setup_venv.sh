#!/usr/bin/env bash
# scripts/setup_venv.sh
set -e
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
if [ -f requirements.txt ]; then pip install -r requirements.txt; else echo "Keine requirements.txt gefunden."; fi
pre-commit install
echo "venv aktiv. Pakete & pre-commit installiert."