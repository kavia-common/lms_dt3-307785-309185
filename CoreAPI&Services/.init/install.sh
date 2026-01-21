#!/usr/bin/env bash
set -euo pipefail

# Workspace from container info
WS="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
mkdir -p "$WS"

# Verify python3 available
command -v python3 >/dev/null 2>&1 || { echo "python3 not found in PATH" >&2; exit 1; }

# Ensure venv support; if missing attempt non-interactive apt install
if ! python3 -c 'import venv, sys' >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -q >/dev/null && sudo apt-get install -y -q python3-venv >/dev/null || { echo "failed to install python3-venv via apt-get" >&2; exit 2; }
  else
    echo "python venv support missing and apt-get not available; please install python3-venv" >&2
    exit 3
  fi
fi

# Create venv if missing
if [ ! -d "$WS/.venv" ]; then
  python3 -m venv "$WS/.venv"
fi
PIP="$WS/.venv/bin/pip"
PY="$WS/.venv/bin/python"
if [ ! -x "$PY" ] || [ ! -x "$PIP" ]; then
  echo "created venv but expected binaries missing at $WS/.venv" >&2
  exit 4
fi

# Upgrade packaging tools inside venv non-interactively and quietly
"$PIP" install --disable-pip-version-check --no-input --no-cache-dir --upgrade pip setuptools wheel >/dev/null

# Verify python inside venv is runnable
"$PY" -V >/dev/null

exit 0
