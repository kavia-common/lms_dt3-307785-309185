#!/usr/bin/env bash
set -euo pipefail
# Minimal, idempotent scaffold for FastAPI app in the authoritative workspace
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
mkdir -p "$WORKSPACE"
cd "$WORKSPACE"
# Ensure venv exists (use system python3 - venv is available per container info)
if [ ! -d "$WORKSPACE/.venv" ]; then
  python3 -m venv "$WORKSPACE/.venv"
fi
# App package
mkdir -p "$WORKSPACE/app"
cat > "$WORKSPACE/app/__init__.py" <<'PY'
# app package
PY
cat > "$WORKSPACE/app/main.py" <<'PY'
from fastapi import FastAPI
app = FastAPI()

@app.get('/health')
def health():
    return {'status': 'ok'}
PY
# Minimal pinned requirements: fastapi (latest), uvicorn and pytest-timeout pinned minor versions
cat > "$WORKSPACE/requirements.txt" <<'REQ'
fastapi
uvicorn[standard]==0.22.0
pytest==7.4.0
requests
pytest-timeout==2.2.0
REQ
# start-dev helper (runs uvicorn from venv)
cat > "$WORKSPACE/start-dev.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1090
source "$HERE/.venv/bin/activate"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
SH
chmod +x "$WORKSPACE/start-dev.sh"
# .gitignore and README
printf ".venv\n__pycache__/\n*.py[cod]\n" > "$WORKSPACE/.gitignore"
cat > "$WORKSPACE/README.md" <<'MD'
Minimal FastAPI app scaffold.

- Use start-dev.sh to run the app (it activates .venv and runs uvicorn with --reload).
- requirements.txt pins uvicorn and pytest for reproducible dev installs; fastapi uses the latest available when installing.
- Environment and dependency installation are handled in subsequent steps.
MD
# Ensure files owned by current user (in container context this is typically fine)
: # scaffold complete
