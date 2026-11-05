"""Exercise the actual RTL driver's shell lifetime using a blocked fake emu.

This checks driver bookkeeping, not hardware or Difftest functionality.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest


class RunnerTest(unittest.TestCase):
    def test_edit_during_emulation_does_not_break_completion(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='vdot-runner-test-') as folder:
            root = Path(folder)
            for subdir in ('scripts', 'bin', 'third_party/XiangShan/build',
                           'build/workloads', 'build/nemu/reference'):
                (root / subdir).mkdir(parents=True, exist_ok=True)
            runner = root / 'scripts/run_rtl.sh'
            shutil.copyfile(source / 'scripts/run_rtl.sh', runner)
            shutil.copyfile(source / 'scripts/check_run.py', root / 'scripts/check_run.py')
            (root / 'scripts/env.sh').write_text(
                'export VDOT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"\n'
                'export NOOP_HOME="$VDOT_ROOT/third_party/XiangShan"\n'
                'export PATH="$VDOT_ROOT/bin:$PATH"\n')
            (root / 'scripts/source_manifest.py').write_text(
                'from pathlib import Path\nimport sys\nPath(sys.argv[1]).write_text("{}\\n")\n')
            wrapper = root / 'bin/systemd-run'
            wrapper.write_text('#!/bin/bash\nwhile [[ "$1" != /usr/bin/time ]]; do shift; done\nexec "$@"\n')
            wrapper.chmod(0o755)
            emu = root / 'third_party/XiangShan/build/emu'
            emu.write_text('#!/usr/bin/env python3\n'
                           'from pathlib import Path\nimport os,time\n'
                           'p=Path(os.environ["VDOT_ROOT"])\n(p/"ready").touch()\n'
                           'while not (p/"release").exists(): time.sleep(0.01)\n'
                           'print("VADD_PASS\\nDifftest enabled.\\nHIT GOOD TRAP")\n')
            emu.chmod(0o755)
            for relative in ('build/workloads/vadd_test.bin', 'build/workloads/flash.bin',
                             'build/nemu/reference/riscv64-nemu-interpreter-so'):
                (root / relative).write_bytes(b'test stub\n')
            # Keep this fixture on its own fake artifacts even when the caller
            # selects a real simulator/reference for a surrounding regression.
            environment = dict(os.environ, VDOT_EMU_PATH=str(emu),
                               VDOT_REF_SO=str(root / 'build/nemu/reference/riscv64-nemu-interpreter-so'))
            process = subprocess.Popen(['/bin/bash', str(runner), 'vadd_test'],
                                       env=environment, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic() + 10
                while not (root / 'ready').exists():
                    if process.poll() is not None or time.monotonic() >= deadline:
                        self.fail('Driver did not reach blocked emu: ' + str(process.communicate(timeout=2)))
                    time.sleep(0.01)
                runner.write_text(runner.read_text().replace(
                    'case "$vdot_workload" in\n',
                    '# Workload list edited while emulator was running.\ncase "$vdot_workload" in\n', 1))
                (root / 'release').touch()
                stdout, stderr = process.communicate(timeout=10)
                self.assertEqual(process.returncode, 0, stdout + stderr)
                self.assertIn('PASS ', stdout)
                reports = list((root / 'reports').glob('rtl-vadd_test-*'))
                self.assertEqual(len(reports), 1)
                self.assertEqual((reports[0] / 'exit-status.txt').read_text(), '0\n')
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()
