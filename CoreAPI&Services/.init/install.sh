#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
cd "$WORKSPACE"
# Source profile for immediate env usage (no-op if not loaded)
source /etc/profile.d/coreapi_services_env.sh >/dev/null 2>&1 || true
# Ensure venv exists and activate
if [ ! -d "$WORKSPACE/.venv" ]; then
  python3 -m venv "$WORKSPACE/.venv"
fi
# Activate venv
# shellcheck disable=SC1090
source "$WORKSPACE/.venv/bin/activate"

# Upgrade pip with captured logs
PIP_UPGRADE_LOG="$WORKSPACE/pip-upgrade.log"
python -m pip install --disable-pip-version-check --upgrade pip >"$PIP_UPGRADE_LOG" 2>&1 || { cat "$PIP_UPGRADE_LOG" >&2; echo 'pip upgrade failed' >&2; exit 2; }

# Install requirements with captured logs
PIP_LOG="$WORKSPACE/pip-install.log"
if [ -f requirements.txt ]; then
  python -m pip install -r requirements.txt >"$PIP_LOG" 2>&1 || { cat "$PIP_LOG" >&2; echo "pip install failed" >&2; exit 3; }
else
  echo "requirements.txt not found in $WORKSPACE" >&2
  exit 5
fi

# Verify imports (include pytest-timeout -> pytest_timeout module name)
python - <<'PY'
import importlib,sys
required = ('fastapi','uvicorn','pytest','requests','pytest_timeout')
for mod in required:
    try:
        importlib.import_module(mod)
    except Exception as e:
        sys.stderr.write(f'import failed for {mod}: {e}\n')
        sys.exit(4)
print('IMPORTS_OK')
PY

# Idempotently append env exports to venv activate (use robust grep)
ACTIVATE="$WORKSPACE/.venv/bin/activate"
if [ -f "$ACTIVATE" ]; then
  if ! grep -q "^# COREAPI_SERVICES_ENV - persisted by env-001$" "$ACTIVATE" 2>/dev/null; then
    cat >> "$ACTIVATE" <<'ACT'
# COREAPI_SERVICES_ENV - persisted by env-001
export PYTHONUNBUFFERED=1
export FASTAPI_ENV=development
export DATABASE_URL=sqlite:///./dev.db
ACT
  fi
else
  echo "Activate script missing: $ACTIVATE" >&2
  exit 6
fi

# Record versions to versions.txt (overwrite to reflect current state)
VERSIONS="$WORKSPACE/versions.txt"
: > "$VERSIONS"
python - <<'PV'
import sys
try:
    import pkg_resources
    v = pkg_resources.get_distribution('pip').version
    print('pip:', v)
except Exception:
    print('pip: unknown')
try:
    import uvicorn
    print('uvicorn:', getattr(uvicorn, '__version__', 'unknown'))
except Exception:
    print('uvicorn: unknown')
PV
python -m pip freeze >> "$VERSIONS" 2>/dev/null || true

# Success
echo "dependencies: OK"
