#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
if [ ! -f .env ]; then cp .env.example .env; fi
echo "Setup complete. Edit .env, then run the mock demo."
