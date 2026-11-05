#!/usr/bin/env bash
# Use an explicit PDF environment, or the system Python when it has both dependencies.
set -euo pipefail
vdot_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
vdot_python=${VDOT_PDF_PYTHON:-python3}
if ! "$vdot_python" -c 'import reportlab, pypdf' >/dev/null 2>&1; then
  printf 'Use a Python environment with ReportLab and pypdf and set VDOT_PDF_PYTHON; see docs/ARTIFACTS.md.\n' >&2
  exit 2
fi
exec "$vdot_python" "$vdot_root/scripts/render_reports.py" "$@"
