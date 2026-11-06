#!/usr/bin/env bash
set -euo pipefail
vdot_task_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
vdot_firtool_binary="$HOME/.cache/llvm-firtool/1.62.1/bin/firtool"
if [[ $# == 1 && "$1" == --version ]]; then
  exec "$vdot_firtool_binary" --version
fi
vdot_allocator="$vdot_task_root/tools/sysroot/usr/lib/x86_64-linux-gnu/libvmmalloc.so.1"
vdot_pool_directory="$vdot_task_root/build/firtool-file-heap"
test -f "$vdot_allocator"
mkdir -p "$vdot_pool_directory"
exec env LD_PRELOAD="$vdot_allocator" VMMALLOC_POOL_DIR="$vdot_pool_directory" \
  VMMALLOC_POOL_SIZE=17179869184 "$vdot_firtool_binary" "$@"
