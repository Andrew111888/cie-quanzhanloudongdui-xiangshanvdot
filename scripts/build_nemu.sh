#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/env.sh"
vdot_mode=${1:-reference}
case "$vdot_mode" in
  standalone) vdot_binary=riscv64-nemu-interpreter ;;
  reference) vdot_binary=riscv64-nemu-interpreter-so ;;
  *) printf 'Usage: bash scripts/build_nemu.sh [standalone|reference]\n' >&2; exit 2 ;;
esac
vdot_output="$VDOT_ROOT/build/nemu/$vdot_mode"
mkdir -p "$vdot_output"
cd "$NEMU_HOME"
make riscv64-xs-kmhv2_defconfig
tools/kconfig/build/conf --defconfig="$VDOT_ROOT/configs/nemu-$vdot_mode.config" Kconfig
tools/kconfig/build/conf --syncconfig Kconfig
make -j"${VDOT_NEMU_JOBS:-1}"
cp "build/$vdot_binary" "$vdot_output/$vdot_binary"
cp .config "$vdot_output/config"
cp include/generated/autoconf.h "$vdot_output/autoconf.h"
cp include/config/auto.conf "$vdot_output/auto.conf"
printf 'Built %s\n' "$vdot_output/$vdot_binary"
