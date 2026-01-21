#!/usr/bin/env bash
set -euo pipefail
# Validation: start uvicorn from /opt/venv with nohup+setsid, wait for TCP + /health, determine PGID, and stop cleanly
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
cd "$WORKSPACE"
# Source global profile if present
source /etc/profile.d/coreapi_services.sh || true
LOG=/tmp/coreapi_uvicorn.log
PORT_NOW="${PORT:-8000}"
HOST_NOW="${HOST:-0.0.0.0}"
# Ensure uvicorn binary in venv
if [ ! -x "/opt/venv/bin/uvicorn" ]; then
  echo "ERROR: /opt/venv/bin/uvicorn missing" >&2
  exit 2
fi
# Start uvicorn with nohup+setsid into background, capture starter PID
nohup setsid /opt/venv/bin/uvicorn app.main:app --host "$HOST_NOW" --port "$PORT_NOW" >"$LOG" 2>&1 &
START_PID=$!
# small settle
sleep 0.5
# Resolve PGID: prefer actual uvicorn process pgid if found, else use starter pid pgid
PGID=""
V_PID=$(pgrep -f -n "/opt/venv/bin/uvicorn app.main:app" || true)
if [ -n "$V_PID" ]; then
  PGID=$(ps -o pgid= -p "$V_PID" | tr -d ' ' || true)
fi
if [ -z "$PGID" ]; then
  PGID=$(ps -o pgid= -p "$START_PID" | tr -d ' ' || true)
fi
_cleanup(){
  # Prefer terminating the whole process group if available
  if [ -n "$PGID" ]; then
    kill -TERM -"$PGID" 2>/dev/null || true
  else
    kill "$START_PID" 2>/dev/null || true
  fi
  # give time to exit
  sleep 0.2
}
trap _cleanup EXIT
# Wait for TCP port to accept connections (max 15s)
READY=0
for i in $(seq 1 15); do
  if /opt/venv/bin/python - <<PY 2>/dev/null
import socket,sys
s=socket.socket()
s.settimeout(0.5)
try:
    s.connect(('127.0.0.1', int(${PORT_NOW})))
    s.close(); print('ok')
except Exception:
    sys.exit(1)
PY
  then
    READY=1; break
  fi
  sleep 1
done
if [ "$READY" -ne 1 ]; then
  echo "status:FAIL:port-not-ready"
  echo "--- uvicorn log tail ---"
  tail -n 200 "$LOG" || true
  exit 3
fi
# Probe /health endpoint using venv python + httpx
/opt/venv/bin/python - <<PY 2>/dev/null
import sys
from httpx import Client
try:
    r=Client().get(f'http://127.0.0.1:{int(${PORT_NOW})}/health', timeout=5.0)
    if r.status_code==200:
        print('status:OK')
        sys.exit(0)
    else:
        print('status:FAIL', r.status_code)
        sys.exit(4)
except Exception as e:
    print('status:ERR', e)
    sys.exit(5)
PY
RES=$?
# cleanup now (trap also ensures cleanup on unexpected exit)
_cleanup
# Emit concise log path for debugging and exit with probe result
echo "log:$LOG"
exit $RES
