#!/usr/bin/env bash
set -euo pipefail
# build no-op sanity check: ensure app/main.py exists
WORKSPACE="/home/kavia/workspace/code-generation/lms_dt3-307785-309185/CoreAPI&Services"
cd "${WORKSPACE}"
if [ ! -f "${WORKSPACE}/app/main.py" ]; then
  echo "error: app/main.py not found in workspace: ${WORKSPACE}/app/main.py" >&2
  exit 3
fi
# success
exit 0
