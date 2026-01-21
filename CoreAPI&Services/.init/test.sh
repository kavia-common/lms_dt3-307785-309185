#!/usr/bin/env bash
set -euo pipefail

# Paths from container context
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
VENV_DIR="/opt/venv"
PY_BIN="${VENV_DIR}/bin/python"
TEST_DIR="${WORKSPACE}/tests"
TEST_FILE="${TEST_DIR}/test_health.py"
LOG_DIR="${WORKSPACE}/logs"

mkdir -p "${TEST_DIR}" "${LOG_DIR}"

if [ ! -x "${PY_BIN}" ]; then
  echo "ERROR: venv python not found at ${PY_BIN}. Ensure step 'environment' and 'dependencies' have been run." >&2
  exit 2
fi

# Create minimal pytest test if it doesn't exist
if [ ! -f "${TEST_FILE}" ]; then
  cat > "${TEST_FILE}" <<'PY'
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_health():
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json().get('status') == 'ok'
PY
fi

cd "${WORKSPACE}"
# Run pytest via venv-resident python and capture output for diagnostics
# -q for concise output; -o log_cli=true to allow live logs if tests use logging
"${PY_BIN}" -m pytest "${TEST_DIR}" -q -o log_cli=true 2>&1 | tee "${LOG_DIR}/pytest.out"

exit ${PIPESTATUS[0]}
