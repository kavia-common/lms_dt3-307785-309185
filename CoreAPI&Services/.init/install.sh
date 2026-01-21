#!/usr/bin/env bash
set -euo pipefail
# install: install minimal python packages into /opt/venv using workspace requirements
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
VENV_DIR="/opt/venv"
PIP_BIN="${VENV_DIR}/bin/pip"
PY_BIN="${VENV_DIR}/bin/python"
REQ_FILE="${WORKSPACE}/requirements.txt"
# Ensure venv pip exists
if [ ! -x "${PIP_BIN}" ]; then
  echo "error: venv pip not found at ${PIP_BIN}; ensure env-01 completed successfully" >&2
  exit 3
fi
# Upgrade packaging tools inside venv deterministically
# Use --disable-pip-version-check to reduce noise; fail on error
"${PIP_BIN}" install --disable-pip-version-check --no-input --upgrade pip setuptools wheel || { echo "pip upgrade failed" >&2; exit 4; }
# Install from requirements.txt if present
if [ -f "${REQ_FILE}" ]; then
  "${PIP_BIN}" install --no-deps -r "${REQ_FILE}" || { echo "pip install -r failed" >&2; exit 5; }
else
  echo "note: requirements.txt not found at ${REQ_FILE}; installing minimal defaults" >&2
  "${PIP_BIN}" install fastapi "uvicorn[standard]" pytest requests || { echo "pip install defaults failed" >&2; exit 5; }
fi
# Respect optional DB flag
if [ "${DEV_USE_DB:-0}" != "0" ]; then
  "${PIP_BIN}" install sqlalchemy aiosqlite || echo "warning: optional DB install failed" >&2
fi
# Respect optional Celery flag
if [ "${DEV_USE_CELERY:-0}" = "1" ]; then
  "${PIP_BIN}" install "celery[redis]" || echo "warning: optional celery install failed" >&2
fi
# Compare venv uvicorn vs system uvicorn and warn if different
VENV_UVICORN_VER=$(${PY_BIN} -c "import importlib,sys
try:
  m=importlib.import_module('uvicorn')
  print(getattr(m,'__version__','(unknown)'))
except Exception:
  print('(not-installed)')" 2>/dev/null || echo "(not-installed)")
SYSTEM_UVICORN_VER=$(python3 -c "import importlib,sys
try:
  m=importlib.import_module('uvicorn')
  print(getattr(m,'__version__','(unknown)'))
except Exception:
  print('(not-installed)')" 2>/dev/null || echo "(not-installed)")
if [ "${VENV_UVICORN_VER}" != "${SYSTEM_UVICORN_VER}" ]; then
  echo "note: system uvicorn=${SYSTEM_UVICORN_VER}, venv uvicorn=${VENV_UVICORN_VER}; scripts use venv binaries explicitly" >&2
fi
# Verify imports using venv python
"${PY_BIN}" - <<'PY'
import sys
try:
    import fastapi, uvicorn, pytest, requests
except Exception as e:
    print('dependency import check failed:', e, file=sys.stderr)
    sys.exit(6)
print('deps_ok')
PY
