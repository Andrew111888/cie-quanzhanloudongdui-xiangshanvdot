"""Verify early decoder faults before custom-dot execution configuration faults."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emu', type=Path, required=True)
    parser.add_argument('--nemu', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--flash', type=Path, required=True)
    parser.add_argument('--old-nemu', type=Path)
    parser.add_argument('--old-reference', type=Path)
    parser.add_argument('--wait-build-receipt', type=Path)
    parser.add_argument('--wait-seconds', type=int, default=3600)
    parser.add_argument('--max-cycles', type=int, default=2000000)
    args = parser.parse_args()
    assert args.wait_seconds >= 0 and args.max_cycles > 0
    root = Path(__file__).resolve().parents[1]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    out = root / 'reports' / ('acc-precedence-' + stamp)
    inputs = out / 'inputs'
    inputs.mkdir(parents=True)
    for name in ['examples/acc_illegal_precedence.c', 'scripts/run_acc_precedence.py',
                 'workloads/start.S', 'workloads/console.h', 'workloads/link.ld']:
        shutil.copy2(root / name, inputs / Path(name).name)
    write_json(out / 'arguments.json', {k: str(v) if isinstance(v, Path) else v
                                      for k, v in vars(args).items()})
    elf, binary = out / 'test.elf', out / 'test.bin'
    build_cmd = ['riscv64-unknown-elf-gcc', '-march=rv64gcv', '-mabi=lp64d',
                 '-mcmodel=medany', '-O2', '-fno-tree-vectorize', '-ffreestanding',
                 '-fno-builtin', '-nostdlib', '-nostartfiles', '-I' + str(inputs),
                 '-Wl,--no-relax', '-Wl,-T,' + str(inputs / 'link.ld'),
                 str(inputs / 'start.S'), str(inputs / 'acc_illegal_precedence.c'),
                 '-o', str(elf)]
    write_json(out / 'build-command.json', build_cmd)
    with (out / 'build.log').open('w') as log:
        subprocess.run(build_cmd, check=True, stdout=log, stderr=log)
    subprocess.run(['riscv64-unknown-elf-objcopy', '-O', 'binary', elf, binary], check=True)
    with (out / 'test.dis').open('w') as log:
        subprocess.run(['riscv64-unknown-elf-objdump', '-d', elf], check=True, stdout=log)
    emu, flash = args.emu.resolve(strict=True), args.flash.resolve(strict=True)
    bound = {str(p.resolve()): digest(p) for p in [emu, flash, binary, elf, *sorted(inputs.iterdir())]}
    runs = []
    print('ACC_PRECEDENCE_STARTED ' + str(out), flush=True)

    def execute(label, executable, reference=None, old=False):
        executable = executable.resolve(strict=True)
        bound[str(executable)] = digest(executable)
        if reference is None:
            cmd = [str(executable), '--batch', '--flash-image=' + str(flash), str(binary)]
        else:
            reference = reference.resolve(strict=True)
            bound[str(reference)] = digest(reference)
            cmd = [str(executable), '-i', str(binary), '-F', str(flash), '--ram-size=128MB',
                   '--diff=' + str(reference), '--no-squash', '-C', str(args.max_cycles)]
        write_json(out / (label + '-command.json'), cmd)
        with (out / (label + '.log')).open('w') as log:
            result = subprocess.run(cmd, cwd=root, stdout=log, stderr=log)
        (out / (label + '-exit-status.txt')).write_text(str(result.returncode) + '\n')
        text = (out / (label + '.log')).read_text(errors='replace')
        entry = {'label': label, 'command': cmd, 'exit_status': result.returncode,
                 'log_sha256': digest(out / (label + '.log'))}
        runs.append(entry)
        write_json(out / 'progress.json', {'status': 'running', 'runs': runs})
        assert result.returncode == (1 if old else 0), (label, result.returncode)
        if reference is not None:
            assert 'Difftest enabled.' in text and 'dirty: 0' in text, label
            if old:
                mismatch = re.search(r'mtval different at pc[^\r\n]*', text)
                assert mismatch and 'ABORT' in text, label
                entry['detected_mismatch'] = mismatch.group(0)
        if reference is None or not old:
            rows = re.findall(r'^PRECEDENCE_CASE,(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)\s*$', text, re.M)
            # Successful cases remain silent to keep UART/formatting outside
            # this exception test's critical runtime. The final case counter
            # covers all 48 probes; only failures produce detailed rows.
            expected_ids = list(range(1, 10)) + [13] + list(range(25, 34)) + [37]
            assert [int(r[0]) for r in rows] == (expected_ids if old else []), label
            wrong = sum(int(r[5]) != 0 for r in rows)
            assert wrong == (20 if old else 0), (label, wrong)
            marker = ('ACC_PRECEDENCE_FAIL cases=48 failures=20' if old
                      else 'ACC_PRECEDENCE_PASS cases=48 failures=0')
            assert marker in text, label
            if not old:
                assert all(int(r[2]) == int(r[3]) for r in rows), label
                assert 'HIT GOOD TRAP' in text, label
                assert not re.search(r'ABORT|HIT BAD TRAP|different at pc|mismatch', text, re.I), label
            entry['case_count'] = 48
            entry['failed_case_count'] = wrong
        print('ACC_PRECEDENCE_RUN_PASS ' + label, flush=True)

    try:
        if args.old_nemu:
            execute('old-nemu', args.old_nemu, old=True)
        if args.old_reference:
            execute('old-reference-rtl', emu, args.old_reference, old=True)
        if args.wait_build_receipt:
            receipt = args.wait_build_receipt.resolve()
            deadline = time.monotonic() + args.wait_seconds
            while not receipt.exists():
                if time.monotonic() >= deadline:
                    raise TimeoutError('new NEMU build receipt not available: ' + str(receipt))
                time.sleep(1)
            build = json.loads(receipt.read_text())
            assert build.get('status') == 'passed', build
            shutil.copy2(receipt, out / 'reference-build-receipt.json')
            bound[str(receipt)] = digest(receipt)
        execute('corrected-nemu', args.nemu)
        execute('corrected-reference-rtl', emu, args.reference)
        for path, want in bound.items():
            assert digest(path) == want, path
        output = {'status': 'passed', 'scope': 'real_rtl_nemu_decode_fault_precedence',
                  'case_count': 48, 'operations': ['vdot', 'vdot.acc'],
                  'original_nemu_wrong_cases': 20 if args.old_nemu else None,
                  'original_reference_rtl_mismatch_observed': bool(args.old_reference),
                  'corrected_nemu_all_cases_passed': True,
                  'corrected_reference_rtl_all_cases_passed': True,
                  'destination_and_vstart_preserved': True,
                  'reported_core_dirty': 0, 'difftest_enabled': True,
                  'input_sha256': bound, 'runs': runs}
        write_json(out / 'results.json', output)
        print('ACC_PRECEDENCE_PASSED ' + str(out), flush=True)
    except Exception as error:
        write_json(out / 'results.json', {'status': 'failed', 'error': repr(error),
                                          'input_sha256': bound, 'runs': runs})
        raise


if __name__ == '__main__':
    main()
