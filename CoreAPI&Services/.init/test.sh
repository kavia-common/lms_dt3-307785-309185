#!/usr/bin/env bash
set -euo pipefail

# Run async pytest smoke test for /health using venv pytest binary
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
cd "$WORKSPACE"

# Ensure tests directory exists
mkdir -p tests

# Create async pytest smoke test for /health (idempotent overwrite)
cat > tests/test_smoke.py <<'PY'
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url='http://test') as ac:
        r = await ac.get('/health')
        assert r.status_code == 200
        assert r.json().get('status') == 'ok'
PY

# Ensure venv pytest binary exists
if [ ! -x /opt/venv/bin/pytest ]; then
  echo "ERROR: /opt/venv/bin/pytest not found or not executable. Ensure /opt/venv exists and dependencies are installed." >&2
  exit 2
fi

# Run tests with 60s external timeout to avoid hangs; fail fast on first failure; save output to /tmp/tests.log
if command -v timeout >/dev/null 2>&1; then
  timeout 60s /opt/venv/bin/pytest -q --maxfail=1 tests 2>&1 | tee /tmp/tests.log
else
  /opt/venv/bin/pytest -q --maxfail=1 tests 2>&1 | tee /tmp/tests.log
fi

# Exit with pytest exit code preserved by tee+pipefail (set -o pipefail is enabled via set -euo pipefail)
