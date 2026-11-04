#!/usr/bin/env python3
"""Save the current tracked and new upstream edits without staging them."""
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
patches = root / 'patches'
patches.mkdir(exist_ok=True)
projects = {
    'xiangshan': (root / 'third_party/XiangShan', [
        'src/main/scala/xiangshan/backend/fu/vector/Vdot.scala',
        'src/test/scala/top/VdotSimConfig.scala',
    ]),
    'nemu': (root / 'third_party/NEMU', []),
}
for name, (project, new_files) in projects.items():
    diff = subprocess.check_output(['git', 'diff', '--binary', '--no-ext-diff'], cwd=project)
    for filename in new_files:
        result = subprocess.run(['git', 'diff', '--binary', '--no-index', '--', '/dev/null', filename],
                                cwd=project, stdout=subprocess.PIPE, check=False)
        if result.returncode != 1:
            raise SystemExit(f'expected new file diff for {filename}, got {result.returncode}')
        diff += result.stdout
    target = patches / f'{name}.patch'
    target.write_bytes(diff)
    subprocess.run(['git', 'apply', '--reverse', '--check', str(target)], cwd=project, check=True)
    print(f'{target.relative_to(root)}: {len(diff)} bytes; reverse check passed')
