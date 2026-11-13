#!/usr/bin/env bash
# Test e2e local : venv, dependances, generation des donnees, pytest, rapport.
set -euo pipefail
cd "$(dirname "$0")"

# Les dependances epinglees (pandas 2.2.3) sont validees sur Python 3.11 a 3.13.
# On choisit le premier interpreteur compatible disponible, sauf si PYTHON est fourni.
if [ -z "${PYTHON:-}" ]; then
  for candidat in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidat" >/dev/null 2>&1; then
      PYTHON="$candidat"
      break
    fi
  done
fi

verifie_version() {
  "$1" -c 'import sys; raise SystemExit(0 if (3, 11) <= sys.version_info[:2] <= (3, 13) else 1)'
}

if ! verifie_version "$PYTHON"; then
  echo "Erreur : $PYTHON ($("$PYTHON" --version 2>&1)) n'est pas supporte." >&2
  echo "Installez Python 3.11, 3.12 ou 3.13 puis relancez (ou PYTHON=python3.13 ./run_e2e.sh)." >&2
  exit 1
fi

# Un venv cree avec un interpreteur non supporte est reconstruit.
if [ -d .venv ] && ! verifie_version .venv/bin/python; then
  echo "==> Le venv existant utilise un Python non supporte, reconstruction"
  rm -rf .venv
fi

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
