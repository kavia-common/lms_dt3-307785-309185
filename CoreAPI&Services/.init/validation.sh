#!/usr/bin/env bash
set -euo pipefail
# validation: start server from venv, probe HOST/PORT, verify process, collect logs, stop cleanly
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
cd "$WORKSPACE"
LOGDIR="$WORKSPACE/logs"
mkdir -p "$LOGDIR"
[ -f /etc/profile.d/fastapi_env.sh ] && source /etc/profile.d/fastapi_env.sh || true
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
# activate venv if present
# shellcheck disable=SC1091
[ -f .venv/bin/activate ] && source .venv/bin/activate || true
# start server and capture PID, log to workspace/logs
TMPLOG=$(mktemp "$LOGDIR/uvicorn.XXXXXX.log")
./start.sh &> "$TMPLOG" &
SERVER_PID=$!
cleanup(){
  if ps -p "$SERVER_PID" >/dev/null 2>&1; then
    if [ -f "/proc/$SERVER_PID/cmdline" ]; then
      CMDLINE=$(tr '\0' ' ' < "/proc/$SERVER_PID/cmdline" || true)
      if echo "$CMDLINE" | grep -q "uvicorn"; then
        kill -TERM "$SERVER_PID" 2>/dev/null || true
        sleep 2
        if ps -p "$SERVER_PID" >/dev/null 2>&1; then
          kill -KILL "$SERVER_PID" 2>/dev/null || true
        fi
      else
        echo "warning: child pid $SERVER_PID cmdline does not contain 'uvicorn': $CMDLINE" >&2
      fi
    else
      kill -TERM "$SERVER_PID" 2>/dev/null || true
    fi
  fi
}
trap 'cleanup' EXIT
# readiness probe: try HOST then 127.0.0.1
TRIES=0
MAX=40
READY=0
while [ $TRIES -lt $MAX ]; do
  for T in "$HOST" "127.0.0.1"; do
    if python - <<'PY' "$T" "$PORT" >/dev/null 2>&1; then
import socket,sys
s=socket.socket()
try:
  s.settimeout(1.0)
  s.connect((sys.argv[1], int(sys.argv[2])))
  sys.exit(0)
except Exception:
  sys.exit(1)
finally:
  s.close()
PY
    then
      READY=1
      break 2
    fi
  done
  sleep 0.5
  TRIES=$((TRIES+1))
done
if [ $READY -ne 1 ]; then
  echo "server did not open port in time" >&2
  tail -n 200 "$TMPLOG" || true
  exit 3
fi
# probe endpoint with httpx
python - <<'PY' "$HOST" "$PORT"
import sys, httpx
host=sys.argv[1]
port=sys.argv[2]
url=f'http://{host}:{port}/'
try:
    r=httpx.get(url, timeout=5.0)
    print('status_code:', r.status_code)
    print('body:', r.text[:1000])
    if r.status_code!=200:
        sys.exit(4)
except Exception as e:
    print('probe failed', e)
    sys.exit(5)
PY
# show log path (do not remove it immediately)
echo "validation completed; logs: $TMPLOG"
exit 0
