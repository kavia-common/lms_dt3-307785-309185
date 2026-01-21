#!/usr/bin/env bash
set -euo pipefail
WS="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
mkdir -p "$WS/app" "$WS/logs"
# Minimal requirements (ranges kept; pinning optional)
cat > "$WS/requirements.txt" <<'REQ'
fastapi>=0.95,<1.0
uvicorn[standard]>=0.22,<1.0
REQ
# Minimal FastAPI app
cat > "$WS/app/main.py" <<'PY'
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
PY
# Start script: prefer venv uvicorn and fail fast if missing
cat > "$WS/start.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
WS="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
cd "$WS"
# Source venv activate if present (may not be executable)
if [ -f "$WS/.venv/bin/activate" ]; then
  # shellcheck disable=SC1090
  source "$WS/.venv/bin/activate"
fi
export PYTHONUNBUFFERED=1
UVICORN_BIN="$WS/.venv/bin/uvicorn"
if [ ! -x "$UVICORN_BIN" ]; then
  echo "ERROR: uvicorn not found in venv at $UVICORN_BIN. Run the build step to install dependencies into .venv." >&2
  exit 5
fi
exec "$UVICORN_BIN" app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
SH
chmod +x "$WS/start.sh"
chmod 644 "$WS/requirements.txt" || true
