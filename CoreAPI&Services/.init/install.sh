#!/usr/bin/env bash
set -euo pipefail
# dependencies: create workspace venv and install python packages (safe under set -e)
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
cd "$WORKSPACE"
PY=python3
# verify python version >= 3.9
read MAJOR MINOR < <($PY - <<'PY'
import sys
print(sys.version_info.major, sys.version_info.minor)
PY
)
if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 9 ]; }; then
  echo "python3 >= 3.9 required, found ${MAJOR}.${MINOR}" >&2
  exit 2
fi
VENV="$WORKSPACE/.venv"
if [ ! -d "$VENV" ]; then
  $PY -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade --quiet pip setuptools
# determine missing packages without aborting under set -e
MFILE=$(mktemp)
python - <<'PY' > "$MFILE" 2>/dev/null || true
import importlib
mapping = [
  ("fastapi","fastapi"),
  ("uvicorn[standard]","uvicorn"),
  ("sqlmodel","sqlmodel"),
  ("pytest","pytest"),
  ("httpx","httpx"),
]
missing = []
for spec, mod in mapping:
    try:
        importlib.import_module(mod)
    except Exception:
        missing.append(spec)
print('\n'.join(missing))
PY
MISSING=$(tr -d '\r' < "$MFILE" || true)
rm -f "$MFILE" || true
if [ -n "${MISSING}" ]; then
  # install missing packages quietly (single pip call)
  python -m pip install --quiet ${MISSING}
fi
# write frozen dev requirements (filter pkg-resources noise)
python -m pip freeze | sed -e '/pkg-resources==0.0.0/d' > dev-requirements.txt
# quick import validation
python - <<'PY'
import sys
try:
    import fastapi, uvicorn, sqlmodel, pytest, httpx
except Exception as e:
    print('dependency import failed:', e, file=sys.stderr)
    sys.exit(2)
print('ok')
PY
exit 0
