#!/usr/bin/env bash
set -euo pipefail
WS="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
PY="$WS/.venv/bin/python"
if [ ! -x "$PY" ]; then
  echo "venv python missing; run env-01 and deps-01 first" >&2
  exit 2
fi
mkdir -p "$WS/tests"
cat > "$WS/tests/test_health.py" <<'PY'
from fastapi.testclient import TestClient
from app.main import app

def test_health():
    client = TestClient(app)
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'
PY
USE_PYTEST="${USE_PYTEST:-1}"
if [ "${USE_PYTEST}" != "1" ]; then
  echo "pytest disabled (set USE_PYTEST=1 to enable)"
  exit 0
fi
# Import-smoke check
$PY - <<'PY' || { echo "import smoke test failed: ensure fastapi/testclient and app.main are importable in venv" >&2; exit 3; }
from fastapi.testclient import TestClient
from app.main import app
print('smoke-ok')
PY
# Run pytest from venv
if [ -x "$WS/.venv/bin/pytest" ]; then
  "$WS/.venv/bin/pytest" -q "$WS/tests" || (echo "pytest failed" >&2 && exit 4)
else
  echo "ERROR: pytest not found in venv. Ensure deps-01 installed pytest." >&2
  exit 5
fi
exit 0
