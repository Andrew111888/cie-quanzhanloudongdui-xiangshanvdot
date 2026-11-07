"""Run mixed standard vector MAC and custom dot control validation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emu', type=Path, required=True)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--flash', type=Path, required=True)
    parser.add_argument('--no-wave', action='store_true')
    parser.add_argument('--begin', type=int, default=0)
    parser.add_argument('--end', type=int, default=30000)
    args = parser.parse_args()
    assert 0 <= args.begin < args.end
    root = Path(__file__).resolve().parents[1]
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + str(os.getpid())
    out = root / 'reports' / ('control-wave-' + stamp)
    inputs = out / 'inputs'; inputs.mkdir(parents=True)
    for relative in ('examples/vdot_control.c', 'workloads/start.S',
                     'workloads/console.h', 'workloads/link.ld'):
        shutil.copyfile(root / relative, inputs / Path(relative).name)
    commands = []

    def run(command, **kwargs):
        commands.append([str(value) for value in command])
        (out / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
        return subprocess.run(commands[-1], cwd=root, **kwargs)

    elf = out / 'test.elf'; binary = out / 'test.bin'
    with (out / 'build.log').open('w') as log:
        run(['riscv64-unknown-elf-gcc', '-march=rv64gcv', '-mabi=lp64d',
             '-mcmodel=medany', '-O2', '-fno-tree-vectorize', '-ffreestanding',
             '-fno-builtin', '-nostdlib', '-nostartfiles', '-I' + str(inputs),
             '-Wl,--no-relax', '-Wl,-T,' + str(inputs / 'link.ld'),
             inputs / 'start.S', inputs / 'vdot_control.c', '-o', elf],
            check=True, stdout=log, stderr=log)
    run(['riscv64-unknown-elf-objcopy', '-O', 'binary', elf, binary], check=True)
    with (out / 'test.dis').open('w') as log:
        run(['riscv64-unknown-elf-objdump', '-d', elf], check=True, stdout=log)
    disassembly = (out / 'test.dis').read_text()
    pcs = {name: '0x' + pc for pc, name in re.findall(r'^([0-9a-f]+) <(control_[a-z_]+)>:', disassembly, re.M)}
    assert len(pcs) == 11, pcs
    emu = args.emu.resolve(strict=True); reference = args.reference.resolve(strict=True)
    flash = args.flash.resolve(strict=True)
    bound = {str(path): digest(path) for path in
             [emu, reference, flash, elf, binary, root / 'src/Vdot.scala',
              root / 'patches/xiangshan.patch', root / 'patches/nemu.patch',
              Path(__file__).resolve(), *sorted(inputs.iterdir())]}
    command = [emu, '-i', binary, '-F', flash, '--ram-size=128MB',
               '--diff=' + str(reference), '--no-squash', '-C', '1000000']
    if not args.no_wave:
        command += ['--dump-wave-full', '-b', str(args.begin), '-e', str(args.end),
                    '--wave-path=' + str(out / 'wave.fst')]
    print('CONTROL_WAVE_STARTED ' + str(out), flush=True)
    with (out / 'run.log').open('w') as log:
        result = run(command, stdout=log, stderr=log)
    (out / 'exit-status.txt').write_text(str(result.returncode) + '\n')
    text = re.sub(r'\x1b\[[0-9;]*m', '', (out / 'run.log').read_text())
    assert result.returncode == 0
    assert re.search(r'VDOT_CONTROL_PASS rounds=40 custom_committed=200 standard_mac_committed=80 odd=\d+ even=\d+ checksum=\d+', text)
    assert 'Difftest enabled.' in text and 'HIT GOOD TRAP' in text
    assert not re.search(r'ABORT|HIT BAD TRAP|different at pc|CRITICAL ERROR', text, re.I)
    manifest = json.loads((root / 'configs/source-manifest.json').read_text())
    version = re.search(r'Commit SHA is: ([0-9a-f]+), dirty: ([01])', text)
    assert version and manifest['tested']['XiangShan'].startswith(version[1]) and version[2] == '0'
    for name, expected in bound.items():
        assert digest(Path(name)) == expected, name
    record = {'status': 'passed', 'scope': 'rtl_nemu_difftest', 'raw_exit_status': 0,
              'core_commit': manifest['tested']['XiangShan'], 'core_dirty': 0,
              'difftest_enabled': True, 'instruction_pcs': pcs,
              'source_snapshot_unchanged': True,
              'internal_flush_timing_claimed': False,
              'backpressure_claimed': False,
              'input_sha256': bound, 'run_log_sha256': digest(out / 'run.log'),
              'wave_dump_enabled': not args.no_wave}
    if not args.no_wave:
        assert (out / 'wave.fst').stat().st_size > 0
        record.update(fst=str(out / 'wave.fst'), fst_sha256=digest(out / 'wave.fst'),
                      capture_begin=args.begin, capture_end=args.end)
    (out / 'results.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    print('CONTROL_WAVE_PASSED ' + str(out), flush=True)


if __name__ == '__main__':
    main()
