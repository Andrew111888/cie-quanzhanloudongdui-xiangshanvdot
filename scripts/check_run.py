"""Reject misleading GOOD TRAP output following an upstream NEMU critical error."""
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
text = re.sub(r'\x1b\[[0-9;]*m', '', path.read_text(errors='replace'))
required = sys.argv[2] if len(sys.argv) > 2 else ''
bad = re.search(r'HIT (?:BAD TRAP|CRITICAL ERROR)|Assertion.*fail|ABORT|DIFFTEST.*FAIL|mismatch', text, re.I)
if bad or 'HIT GOOD TRAP' not in text or (required and required not in text):
    print(f'FAIL {path}: {bad.group(0) if bad else "missing completion marker"}', file=sys.stderr)
    sys.exit(1)
print(f'PASS {path}')
