#!/usr/bin/env bash
set -euo pipefail
# Start script to launch uvicorn from venv with single worker, writes logs to workspace/logs/start_uvicorn.log
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
VENV_DIR="/opt/venv"
UVICORN_BIN="${VENV_DIR}/bin/uvicorn"
LOGDIR="${WORKSPACE}/logs"
mkdir -p "${LOGDIR}"
APP_MODULE="${APP_MODULE:-${COREAPI_APP_MODULE:-app.main:app}}"
HOST="${HOST:-${COREAPI_HOST:-0.0.0.0}}"
PORT="${PORT:-${COREAPI_PORT:-8000}}"
cd "${WORKSPACE}"
if [ ! -x "${UVICORN_BIN}" ]; then
  echo "error: uvicorn binary not found or not executable: ${UVICORN_BIN}" >&2
  exit 4
fi
# start uvicorn in foreground (but this script backgrounds it for lifecycle management)
"${UVICORN_BIN}" "${APP_MODULE}" --host "${HOST}" --port "${PORT}" --workers 1 >>"${LOGDIR}/start_uvicorn.log" 2>&1 &
echo $! >"${LOGDIR}/start_uvicorn.pid"
# leave process running
exit 0
