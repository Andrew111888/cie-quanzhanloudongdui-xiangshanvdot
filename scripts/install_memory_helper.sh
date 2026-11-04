#!/usr/bin/env bash
set -euo pipefail
VDOT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
vdot_package="$VDOT_ROOT/tools/packages/libvmmalloc1_1.8-2_amd64.deb"
vdot_sha=f14d3979e7cd3920707a5206020af620a160bfdd4058c6ad41fb4371e081e883
test "$(uname -m)" == x86_64 || { printf 'This pinned package is for x86_64 only.\n' >&2; exit 2; }
mkdir -p "$VDOT_ROOT/tools/packages" "$VDOT_ROOT/tools/sysroot"
if [[ ! -f "$vdot_package" ]]; then
  curl --fail --location --max-time 60 \
    https://deb.debian.org/debian/pool/main/v/vmem/libvmmalloc1_1.8-2_amd64.deb \
    -o "$vdot_package"
fi
printf '%s  %s\n' "$vdot_sha" "$vdot_package" | sha256sum --check
dpkg-deb -x "$vdot_package" "$VDOT_ROOT/tools/sysroot"
printf 'Memory helper extracted under %s/tools/sysroot\n' "$VDOT_ROOT"
