#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
mkdir -p "$WORKSPACE" && cd "$WORKSPACE"
mkdir -p app
cat > "$WORKSPACE/app/main.py" <<'PY'
from fastapi import FastAPI
app = FastAPI()

@app.get('/health')
async def health():
    return {'status':'ok'}

@app.get('/')
async def root():
    return {'message':'CoreAPI&Services scaffold'}
PY
cat > "$WORKSPACE/start-dev.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
# start-dev: uses venv uvicorn; will add --reload only when ENV=development
[ -x /opt/venv/bin/python ] || { echo "ERROR: /opt/venv missing; run env install step" >&2; exit 2; }
# source global env if present
if [ -r /etc/profile.d/coreapi_services.sh ]; then
  # shellcheck disable=SC1090
  source /etc/profile.d/coreapi_services.sh
fi
# prefer venv binary explicitly
CMD=(/opt/venv/bin/uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}")
# --reload only intended for local development; CI should set ENV not equal to development
if [ "${ENV:-development}" = "development" ]; then
  CMD+=(--reload)
fi
exec "${CMD[@]}"
SH
chmod +x "$WORKSPACE/start-dev.sh"
