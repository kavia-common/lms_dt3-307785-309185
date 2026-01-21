#!/usr/bin/env bash
set -euo pipefail
WS="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
LOGDIR="$WS/logs"
mkdir -p "$LOGDIR"
PIP="$WS/.venv/bin/pip"
PY="$WS/.venv/bin/python"
# Ensure python3 venv support and create venv if missing
if [ ! -x "$PY" ] || [ ! -x "$PIP" ]; then
  command -v python3 >/dev/null 2>&1 || { echo "python3 not found" >&2; exit 2; }
  # ensure python3-venv available
  python3 -c "import venv" >/dev/null 2>&1 || (sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-venv)
  # create venv
  python3 -m venv "$WS/.venv"
  PIP="$WS/.venv/bin/pip"
  PY="$WS/.venv/bin/python"
fi
# Upgrade packaging tools in venv
"$PY" -m pip install --disable-pip-version-check --no-input --upgrade pip setuptools wheel >/dev/null 2>&1 || { echo "failed to upgrade pip/setuptools/wheel" >&2; exit 3; }
# Ensure requirements.txt exists
if [ ! -f "$WS/requirements.txt" ]; then
  echo "requirements.txt not found in $WS" >&2
  exit 4
fi
USE_PYTEST="${USE_PYTEST:-1}"
USE_DOTENV="${USE_DOTENV:-0}"
# Install base requirements and optionally pytest+requests/dotenv non-interactively
"$PIP" install --disable-pip-version-check --no-input --no-cache-dir -r "$WS/requirements.txt" 2>&1 | tee "$LOGDIR/pip-install.log" || { echo "pip install failed; see $LOGDIR/pip-install.log" >&2; tail -n 200 "$LOGDIR/pip-install.log" >&2; exit 5; }
if [ "$USE_PYTEST" = "1" ]; then
  "$PIP" install --disable-pip-version-check --no-input --no-cache-dir pytest requests 2>&1 | tee -a "$LOGDIR/pip-install.log" || { echo "pip install pytest/requests failed; see $LOGDIR/pip-install.log" >&2; tail -n 200 "$LOGDIR/pip-install.log" >&2; exit 6; }
fi
if [ "$USE_DOTENV" = "1" ]; then
  "$PIP" install --disable-pip-version-check --no-input --no-cache-dir python-dotenv 2>&1 | tee -a "$LOGDIR/pip-install.log" || { echo "pip install python-dotenv failed; see $LOGDIR/pip-install.log" >&2; tail -n 200 "$LOGDIR/pip-install.log" >&2; exit 7; }
fi
# Verify imports via venv python
"$PY" - <<'PY' || (echo "fastapi/uvicorn import check failed; see $LOGDIR/pip-install.log" >&2 && tail -n 200 "$LOGDIR/pip-install.log" >&2 && exit 8)
import importlib
importlib.import_module('fastapi')
importlib.import_module('uvicorn')
print('imports-ok')
PY
# Ensure venv uvicorn binary exists
if [ ! -x "$WS/.venv/bin/uvicorn" ]; then
  echo "ERROR: uvicorn binary not present in venv ($WS/.venv/bin/uvicorn). Build step may have failed." >&2
  tail -n 200 "$LOGDIR/pip-install.log" >&2 || true
  exit 9
fi
exit 0
