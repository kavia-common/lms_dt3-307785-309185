#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
cd "$WORKSPACE"

# activate venv
# shellcheck disable=SC1091
if [ ! -f .venv/bin/activate ]; then
  echo "ERROR: virtualenv not found at .venv. Ensure dependencies step created the venv and installed required packages." >&2
  exit 3
fi
source .venv/bin/activate

mkdir -p tests
cat > tests/test_app.py <<'PY'
import importlib
import pytest
from sqlmodel import SQLModel, create_engine
from httpx import AsyncClient

@pytest.fixture(autouse=True)
def use_memory_db(monkeypatch):
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    # create a temporary module object and register it so main can import it by name
    import types, sys
    modname = 'test_engine_inject'
    m = types.ModuleType(modname)
    m._test_engine = engine
    sys.modules[modname] = m
    monkeypatch.setenv('TEST_ENGINE_MODULE', modname)
    yield
    try:
        del sys.modules[modname]
    except Exception:
        pass

@pytest.mark.asyncio
async def test_root_and_item():
    import importlib
    import main as main_mod
    importlib.reload(main_mod)
    async with AsyncClient(app=main_mod.app, base_url='http://test') as ac:
        r = await ac.get('/')
        assert r.status_code == 200
        data = r.json()
        assert data.get('status') == 'ok'
        r = await ac.post('/items/', json={'name': 'x'})
        assert r.status_code == 200
        item = r.json()
        assert item.get('name') == 'x'
        r = await ac.get(f"/items/{item.get('id')}")
        assert r.status_code == 200
        got = r.json()
        assert got.get('name') == 'x'
PY

# Run tests
python -m pytest -q tests || { echo "tests failed" >&2; exit 2; }

echo "tests passed"
exit 0
