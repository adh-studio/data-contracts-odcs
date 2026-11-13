#!/usr/bin/env bash
# Test e2e local : venv, dependances, generation des donnees, pytest, rapport.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

if [ ! -d .venv ]; then
  "$PYTHON" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "==> Generation des jeux de donnees synthetiques"
python scripts/genere_donnees.py

echo "==> Tests pytest"
PYTHONPATH=src python -m pytest tests/ -v

echo "==> Generation du rapport de conformite docs/index.html"
python scripts/genere_rapport.py

echo "==> E2E termine avec succes"
