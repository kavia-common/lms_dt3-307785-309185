#!/usr/bin/env bash
set -euo pipefail
# validation: start venv uvicorn (single worker), poll /health, perform robust shutdown, copy logs to workspace/logs
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
VENV_DIR="/opt/venv"
UVICORN_BIN="${VENV_DIR}/bin/uvicorn"
LOGDIR="${WORKSPACE}/logs"
mkdir -p "${LOGDIR}"
LOG_FILE="/tmp/coreapi_uvicorn.log"
APP_MODULE="${APP_MODULE:-${COREAPI_APP_MODULE:-app.main:app}}"
HOST="${HOST:-${COREAPI_HOST:-0.0.0.0}}"
PORT="${PORT:-${COREAPI_PORT:-8000}}"
cd "${WORKSPACE}"
if [ ! -x "${UVICORN_BIN}" ]; then
  echo "error: uvicorn not found in venv: ${UVICORN_BIN}" >&2
  exit 4
fi
# Start uvicorn in foreground but background the process; enforce single worker
"${UVICORN_BIN}" "${APP_MODULE}" --host "${HOST}" --port "${PORT}" --workers 1 >"${LOG_FILE}" 2>&1 &
SERVER_PID=$!
# trap and cleanup on signals
trap 'echo "validation: cleaning up"; kill -INT ${SERVER_PID} 2>/dev/null || true; sleep 1; kill -TERM ${SERVER_PID} 2>/dev/null || true; sleep 1; kill -KILL ${SERVER_PID} 2>/dev/null || true; wait ${SERVER_PID} 2>/dev/null || true; exit 1' INT TERM EXIT
# Poll readiness using multiple addresses including container localhost and container IP
RETRIES=20
SLEEP=1
URLS=("http://127.0.0.1:${PORT}/health" "http://localhost:${PORT}/health")
CONTAINER_IP=$(hostname -I | awk '{print $1}' || echo "")
if [ -n "${CONTAINER_IP}" ]; then
  URLS+=("http://${CONTAINER_IP}:${PORT}/health")
fi
OK=0
for i in $(seq 1 ${RETRIES}); do
  for u in "${URLS[@]}"; do
    if curl -sS --max-time 2 "$u" 2>/dev/null | grep -q '"status": *"ok"'; then
      OK=1; break 2
    fi
  done
  if ! kill -0 ${SERVER_PID} 2>/dev/null; then
    echo "server process died early; see log ${LOG_FILE}" >&2
    sed -n '1,200p' "${LOG_FILE}" >&2 || true
    trap - INT TERM EXIT
    exit 5
  fi
  sleep ${SLEEP}
done
if [ ${OK} -ne 1 ]; then
  echo "validation failed: server did not respond" >&2
  sed -n '1,200p' "${LOG_FILE}" >&2 || true
  # cleanup
  kill -INT ${SERVER_PID} 2>/dev/null || true
  sleep 1
  kill -TERM ${SERVER_PID} 2>/dev/null || true
  sleep 1
  kill -KILL ${SERVER_PID} 2>/dev/null || true
  trap - INT TERM EXIT
  exit 2
fi
# Graceful shutdown
kill -INT ${SERVER_PID} 2>/dev/null || true
sleep 2
if kill -0 ${SERVER_PID} 2>/dev/null; then
  kill -TERM ${SERVER_PID} 2>/dev/null || true
  sleep 2
fi
if kill -0 ${SERVER_PID} 2>/dev/null; then
  kill -KILL ${SERVER_PID} 2>/dev/null || true
fi
wait ${SERVER_PID} 2>/dev/null || true
trap - INT TERM EXIT
cp "${LOG_FILE}" "${LOGDIR}/coreapi_uvicorn.log" || true
echo "validation OK, log: ${LOGDIR}/coreapi_uvicorn.log"
exit 0
