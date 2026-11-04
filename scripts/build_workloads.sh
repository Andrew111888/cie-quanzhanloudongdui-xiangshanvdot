#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/env.sh"
mkdir -p "$VDOT_ROOT/build/workloads"
python3 - <<'PY'
import json, os, pathlib, socket, subprocess
try:
    ip = subprocess.check_output(['hostname', '-I'], text=True).split()[0]
except (OSError, subprocess.CalledProcessError, IndexError):
    ip = 'IP-unavailable'
identity = os.environ.get('VDOT_IDENTITY', os.environ.get('USER', 'participant'))
target = pathlib.Path(os.environ['VDOT_ROOT']) / 'build/workloads/identity.h'
target.write_text('#define VDOT_IDENTITY ' + json.dumps(identity) + '\n#define VDOT_IP ' + json.dumps(ip) + '\n')
PY
riscv64-unknown-elf-gcc -march=rv64gc -mabi=lp64d -nostdlib -nostartfiles \
  -Wl,-Ttext=0x10000000 "$VDOT_ROOT/workloads/flash.S" -o "$VDOT_ROOT/build/workloads/flash.elf"
riscv64-unknown-elf-objcopy -O binary "$VDOT_ROOT/build/workloads/flash.elf" "$VDOT_ROOT/build/workloads/flash.bin"
for workload in vdot_test vdot_smoke vdot_vstart_probe vadd_test benchmark; do
source_name=$workload
extra=()
if [[ "$workload" == vdot_smoke ]]; then source_name=vdot_test; extra=(-DRANDOM_CASES=0); fi
if [[ "$workload" == vdot_vstart_probe ]]; then source_name=vdot_test; extra=(-DRANDOM_CASES=0 -DVDOT_PROBE_STANDARD_VSTART); fi
riscv64-unknown-elf-gcc -march=rv64gcv -mabi=lp64d -mcmodel=medany \
  -O2 -fno-tree-vectorize -ffreestanding -fno-builtin -nostdlib -nostartfiles \
  -I"$VDOT_ROOT/build/workloads" \
  -Wl,--no-relax -Wl,-T,"$VDOT_ROOT/workloads/link.ld" \
  "${extra[@]}" "$VDOT_ROOT/workloads/start.S" "$VDOT_ROOT/workloads/$source_name.c" \
  -o "$VDOT_ROOT/build/workloads/$workload.elf"
riscv64-unknown-elf-objcopy -O binary "$VDOT_ROOT/build/workloads/$workload.elf" "$VDOT_ROOT/build/workloads/$workload.bin"
riscv64-unknown-elf-objdump -d "$VDOT_ROOT/build/workloads/$workload.elf" > "$VDOT_ROOT/build/workloads/$workload.dis"
done
