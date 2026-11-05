#!/usr/bin/env bash
# Prefer an explicit PDF environment, then the system, then the bundled runtime.
set -euo pipefail
vdot_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
vdot_python=${VDOT_PDF_PYTHON:-python3}
if ! "$vdot_python" -c 'import reportlab' >/dev/null 2>&1; then
  if [[ -n "${VDOT_PDF_PYTHON:-}" ]]; then
    printf 'VDOT_PDF_PYTHON must provide ReportLab.\n' >&2
    exit 2
  fi
  vdot_python="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
  if [[ ! -x "$vdot_python" ]] || ! "$vdot_python" -c 'import reportlab' >/dev/null 2>&1; then
    printf 'Use a Python environment with ReportLab and set VDOT_PDF_PYTHON; see docs/ARTIFACTS.md.\n' >&2
    exit 2
  fi
fi
exec "$vdot_python" "$vdot_root/scripts/render_reports.py" "$@"
