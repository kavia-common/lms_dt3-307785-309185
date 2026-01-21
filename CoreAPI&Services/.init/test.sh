#!/usr/bin/env bash
set -euo pipefail
# Minimal test runner for STEP: testing
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
cd "$WORKSPACE"
mkdir -p "$WORKSPACE/tests"
cat > "$WORKSPACE/tests/test_health.py" <<'PY'
from fastapi.testclient import TestClient
from app.main import app
import os

def test_health():
    client = TestClient(app)
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'

def test_env_database_url():
    # Ensure the env var is present when profile is sourced
    assert os.environ.get('DATABASE_URL', '').startswith('sqlite:///')
PY

# Source global profile if available (idempotent)
if [ -r /etc/profile.d/coreapi_services_env.sh ]; then
  # shellcheck disable=SC1090
  source /etc/profile.d/coreapi_services_env.sh || true
fi

# Activate venv
if [ -f "$WORKSPACE/.venv/bin/activate" ]; then
  # shellcheck disable=SC1090
  source "$WORKSPACE/.venv/bin/activate"
else
  echo ".venv not found at $WORKSPACE/.venv. Create venv and install deps before running tests." >&2
  exit 3
fi

# Ensure workspace is on PYTHONPATH
export PYTHONPATH="$WORKSPACE:${PYTHONPATH:-}"

# Quick check for pytest-timeout plugin availability
python - <<'PY'
import sys, importlib
ok = False
for name in ('pytest_timeout','pytest-timeout'):
    try:
        importlib.import_module(name)
        ok = True
        break
    except Exception:
        pass
# Some installs only register plugin via pytest entry points; try importing pytest and listing plugins
if not ok:
    try:
        import pytest
        plugs = [p.name for p in pytest.main.__self__.__class__.__mro__] if hasattr(pytest, 'main') else None
    except Exception:
        plugs = None
if not ok:
    # still print a marker so logs show result
    print('PYTEST_TIMEOUT_AVAILABLE=False')
    sys.exit(4)
print('PYTEST_TIMEOUT_AVAILABLE=True')
PY

# Run pytest with per-test timeout 5s to avoid hangs
python -m pytest -q -o log_cli=false --maxfail=1 --disable-warnings -k "test_" --timeout=5 tests || { echo 'pytest failed' >&2; exit 2; }
