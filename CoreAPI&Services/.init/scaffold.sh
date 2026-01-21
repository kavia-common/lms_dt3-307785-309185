#!/usr/bin/env bash
set -euo pipefail
# Idempotent scaffolding for minimal FastAPI app, requirements, and start script
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
VENV_DIR="/opt/venv"
mkdir -p "${WORKSPACE}/app"
MAIN_PY="${WORKSPACE}/app/main.py"
if [ ! -f "${MAIN_PY}" ]; then
  cat > "${MAIN_PY}" <<'PY'
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}
PY
fi
REQ_FILE="${WORKSPACE}/requirements.txt"
if [ ! -f "${REQ_FILE}" ]; then
  cat > "${REQ_FILE}" <<'TXT'
fastapi==0.100.0
uvicorn==0.22.0
pytest==7.4.0
requests==2.31.0
# Optional: sqlalchemy, aiosqlite, celery[redis]
TXT
fi
# Create workspace-level start script that preserves runtime env overrides (do not expand variables now)
START_SH="${WORKSPACE}/start.sh"
if [ ! -f "${START_SH}" ]; then
  cat > "${START_SH}" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="${WORKSPACE}"
VENV_DIR="/opt/venv"
cd "${WORKSPACE}"
# Activate venv if present (non-interactive safe)
if [ -f "${VENV_DIR}/bin/activate" ]; then
  # shellcheck source=/dev/null
  . "${VENV_DIR}/bin/activate"
fi
export PYTHONPATH="${WORKSPACE}:${PYTHONPATH:-}"
# Allow runtime overrides; fallbacks read from /etc/profile.d COREAPI_* if present
APP_MODULE="${APP_MODULE:-${COREAPI_APP_MODULE:-app.main:app}}"
HOST="${HOST:-${COREAPI_HOST:-0.0.0.0}}"
PORT="${PORT:-${COREAPI_PORT:-8000}}"
# Use absolute venv uvicorn to avoid system binary ambiguity
exec "${VENV_DIR}/bin/uvicorn" "$APP_MODULE" --host "$HOST" --port "$PORT" --workers 1
SH
  chmod +x "${START_SH}"
  sudo chown "$(id -u):$(id -g)" "${START_SH}" >/dev/null 2>&1 || true
fi
# Also write a concise .init/scaffold.sh copy for reproducible execution (same content) for the orchestrator
INIT_DIR=".init"
mkdir -p "${INIT_DIR}"
cat > "${INIT_DIR}/scaffold.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
VENV_DIR="/opt/venv"
mkdir -p "${WORKSPACE}/app"
MAIN_PY="${WORKSPACE}/app/main.py"
if [ ! -f "${MAIN_PY}" ]; then
  cat > "${MAIN_PY}" <<'PY'
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}
PY
fi
REQ_FILE="${WORKSPACE}/requirements.txt"
if [ ! -f "${REQ_FILE}" ]; then
  cat > "${REQ_FILE}" <<'TXT'
fastapi==0.100.0
uvicorn==0.22.0
pytest==7.4.0
requests==2.31.0
# Optional: sqlalchemy, aiosqlite, celery[redis]
TXT
fi
START_SH="${WORKSPACE}/start.sh"
if [ ! -f "${START_SH}" ]; then
  cat > "${START_SH}" <<'SH2'
#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="${WORKSPACE}"
VENV_DIR="/opt/venv"
cd "${WORKSPACE}"
if [ -f "${VENV_DIR}/bin/activate" ]; then
  . "${VENV_DIR}/bin/activate"
fi
export PYTHONPATH="${WORKSPACE}:${PYTHONPATH:-}"
APP_MODULE="${APP_MODULE:-${COREAPI_APP_MODULE:-app.main:app}}"
HOST="${HOST:-${COREAPI_HOST:-0.0.0.0}}"
PORT="${PORT:-${COREAPI_PORT:-8000}}"
exec "${VENV_DIR}/bin/uvicorn" "$APP_MODULE" --host "$HOST" --port "$PORT" --workers 1
SH2
  chmod +x "${START_SH}"
  sudo chown "$(id -u):$(id -g)" "${START_SH}" >/dev/null 2>&1 || true
fi
SH
chmod +x "${INIT_DIR}/scaffold.sh"

# Print summary for operator
printf '%s\n' "scaffold: ensured app/, app/main.py, requirements.txt, and start.sh exist (idempotent)"
