#!/usr/bin/env bash
set -euo pipefail
# validation: start uvicorn, check /health, staged shutdown
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
cd "$WORKSPACE"
# load global env if present, ignore failures
source /etc/profile.d/coreapi_services_env.sh >/dev/null 2>&1 || true
# activate venv if present
if [ -f "$WORKSPACE/.venv/bin/activate" ]; then
  # shellcheck disable=SC1090
  source "$WORKSPACE/.venv/bin/activate"
fi
LOG="$WORKSPACE/uvicorn.log"
: >"$LOG" || true
# tcp connect helper
tcp_listening() {
  local host=$1 port=$2
  if timeout 1 bash -c "</dev/tcp/${host}/${port}" >/dev/null 2>&1; then
    return 0
  fi
  return 1
}
# choose port: try 8000 else ephemeral
PORT=8000
if tcp_listening 127.0.0.1 $PORT; then
  PORT=$(python - <<'PY'
import socket
s=socket.socket(); s.bind(('127.0.0.1',0)); p=s.getsockname()[1]; s.close(); print(p)
PY
)
fi
# Start uvicorn in background; ensure using current venv python if available
UVICORN_CMD=(python -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --log-level info)
nohup "${UVICORN_CMD[@]}" >"$LOG" 2>&1 &
# give short initial time for process to appear
sleep 0.5
# discover uvicorn PID (may return multiple; narrow to pattern)
UVICORN_PID=""
for i in $(seq 1 10); do
  UVICORN_PID=$(pgrep -f "uvicorn.*app.main:app" || true)
  if [ -n "$UVICORN_PID" ]; then break; fi
  sleep 1
done
if [ -z "$UVICORN_PID" ]; then
  echo "ERROR: failed to find uvicorn PID; see log $LOG" >&2
  tail -n 200 "$LOG" >&2 || true
  exit 3
fi
# Wait for readiness (max ~20s)
READY=0
for i in $(seq 1 20); do
  if tcp_listening 127.0.0.1 $PORT && curl -sS --fail "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 1
done
if [ "$READY" -ne 1 ]; then
  echo "ERROR: server did not become ready within timeout; see log $LOG" >&2
  tail -n 200 "$LOG" >&2 || true
  # attempt best-effort shutdown
  kill $UVICORN_PID 2>/dev/null || true
  exit 4
fi
# fetch health output
HEALTH_OUTPUT=$(curl -sS --fail "http://127.0.0.1:$PORT/health") || {
  echo "ERROR: curl to /health failed" >&2
  tail -n 200 "$LOG" >&2 || true
  kill $UVICORN_PID 2>/dev/null || true
  exit 5
}
echo "HEALTH_OUTPUT:$HEALTH_OUTPUT"
# staged shutdown: send TERM to process group if possible
PGID=$(ps -o pgid= -p "$UVICORN_PID" | tr -d ' ' || true)
if [ -n "$PGID" ]; then
  kill -TERM -- -$PGID 2>/dev/null || true
else
  kill -TERM "$UVICORN_PID" 2>/dev/null || true
fi
# wait up to 10s for process to exit
for i in $(seq 1 10); do
  if ! kill -0 "$UVICORN_PID" 2>/dev/null; then
    break
  fi
  sleep 1
done
if kill -0 "$UVICORN_PID" 2>/dev/null; then
  # escalate: kill process group then PID
  if [ -n "$PGID" ]; then
    kill -KILL -- -$PGID 2>/dev/null || true
  fi
  kill -KILL "$UVICORN_PID" 2>/dev/null || true
fi
# Final cleanup: remove any stray uvicorn for this app
pkill -f "uvicorn.*app.main:app" || true
[ -s "$LOG" ] && echo 'uvicorn log exists at:' "$LOG"
exit 0
