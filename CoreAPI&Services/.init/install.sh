#!/usr/bin/env bash
set -euo pipefail
# install: install runtime & test deps into /opt/venv and produce requirements-dev.txt
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
# ensure venv exists
if [ ! -x /opt/venv/bin/python ]; then echo "ERROR: /opt/venv not found; run env install (env step)" >&2; exit 2; fi
# packages to install
PKGS=(fastapi "uvicorn[standard]" pytest httpx pytest-asyncio)
# opt-in packages via env vars
: "${ENABLE_CELERY:-0}" >/dev/null
if [ "${ENABLE_CELERY:-0}" = "1" ]; then PKGS+=("celery[redis]"); fi
: "${ENABLE_DB_CLIENTS:-0}" >/dev/null
if [ "${ENABLE_DB_CLIENTS:-0}" = "1" ]; then PKGS+=(psycopg2-binary mysqlclient); fi
# run pip install with explicit flags; do NOT swallow output. Fail with meaningful exit codes
/opt/venv/bin/python -m pip install --upgrade --prefer-binary --no-cache-dir "${PKGS[@]}" || { echo "ERROR: pip install failed" >&2; /opt/venv/bin/python -m pip check || true; exit 3; }
# verify uvicorn present in venv
if [ ! -x /opt/venv/bin/uvicorn ]; then echo "ERROR: uvicorn not installed in venv" >&2; exit 4; fi
# produce reproducible requirements file in workspace
/opt/venv/bin/pip freeze > "$WORKSPACE/requirements-dev.txt"
# print key package versions for quick confirmation
/opt/venv/bin/python - <<'PY'
import sys
for name in ('fastapi','uvicorn','pytest','httpx'):
    try:
        m=__import__(name)
        v=getattr(m,'__version__',None)
    except Exception:
        v=None
    print(f'{name}:{v or "unknown"}')
PY
