#!/usr/bin/env bash
set -euo pipefail
# Atomic write of global env file then scaffold workspace and app
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
# Create /etc/profile.d/fastapi_env.sh with defaults (atomic via mktemp + sudo mv)
TMP=$(mktemp)
cat >"$TMP" <<'ENV'
#!/usr/bin/env bash
# Global defaults for headless FastAPI runs
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-8000}
ENV
sudo mv "$TMP" /etc/profile.d/fastapi_env.sh && sudo chmod 644 /etc/profile.d/fastapi_env.sh || true
# Ensure workspace exists
mkdir -p "$WORKSPACE" && cd "$WORKSPACE"
# minimal requirements
cat > requirements.txt <<'REQ'
fastapi
uvicorn[standard]
sqlmodel
REQ
# main.py supports TEST_ENGINE_MODULE injection: uses injected _test_engine when provided
cat > main.py <<'PY'
from os import environ
from typing import Optional
from pathlib import Path
from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select
import importlib

HOST = environ.get("HOST", "0.0.0.0")
PORT = int(environ.get("PORT", "8000"))

app = FastAPI(title="CoreAPI&Services")

# If TEST_ENGINE_MODULE is set, import that module and use its _test_engine (for tests)
_test_engine = None
if environ.get('TEST_ENGINE_MODULE'):
    try:
        mod = importlib.import_module(environ['TEST_ENGINE_MODULE'])
        _test_engine = getattr(mod, '_test_engine', None)
    except Exception:
        _test_engine = None

if _test_engine is not None:
    engine = _test_engine
else:
    # SQLite engine (file-based in workspace next to main.py)
    DB_PATH = Path(__file__).resolve().parent / "coreapi.db"
    DB_URL = f"sqlite:///{DB_PATH.as_posix()}"
    engine = create_engine(DB_URL, echo=False, connect_args={"check_same_thread": False})

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/", tags=["root"]) 
def read_root():
    return {"status": "ok", "host": HOST, "port": PORT}

@app.post("/items/", tags=["items"])  
def create_item(item: Item):
    with Session(engine) as session:
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

@app.get("/items/{item_id}")
def get_item(item_id: int):
    with Session(engine) as session:
        stmt = select(Item).where(Item.id == item_id)
        res = session.exec(stmt).first()
        if not res:
            raise HTTPException(status_code=404, detail="Not found")
        return res
PY
# start script
cat > start.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
cd "$WORKSPACE"
[ -f /etc/profile.d/fastapi_env.sh ] && source /etc/profile.d/fastapi_env.sh || true
# activate workspace venv if present
if [ -f "${WORKSPACE}/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "${WORKSPACE}/.venv/bin/activate"
fi
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}
RELOAD=--reload
for a in "$@"; do
  if [ "$a" = "--no-reload" ]; then RELOAD=; fi
done
exec uvicorn main:app --host "$HOST" --port "$PORT" $RELOAD
SH
chmod +x start.sh
cat > README.md <<'MD'
Run: ./start.sh (uses .venv if present). To run without reload: ./start.sh --no-reload
Tests inject an in-memory engine via TEST_ENGINE_MODULE for isolation. Logs created under ./logs during validation.
MD
# Ensure files are created with sane permissions
chmod 644 requirements.txt main.py README.md
chmod 755 start.sh

exit 0
