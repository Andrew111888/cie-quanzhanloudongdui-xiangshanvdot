#!/usr/bin/env bash
# Source this file; all changes are confined to the current shell.
VDOT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
export VDOT_ROOT
if [[ -f "$VDOT_ROOT/local.env" ]]; then source "$VDOT_ROOT/local.env"; fi
VDOT_CHIPYARD_ENV=${VDOT_CHIPYARD_ENV:-/home/yh/chipyard/.conda-env}
if [[ -d "$VDOT_CHIPYARD_ENV" ]]; then
  # Use host GCC/libc together; conda's compiler uses an older sysroot.
  export PATH="$VDOT_CHIPYARD_ENV/riscv-tools/bin:/usr/bin:$VDOT_CHIPYARD_ENV/bin:$PATH"
  export JAVA_HOME="$VDOT_CHIPYARD_ENV"
  export CPATH="$VDOT_CHIPYARD_ENV/include${CPATH:+:$CPATH}"
  export LIBRARY_PATH="$VDOT_CHIPYARD_ENV/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
  export BISON_PKGDATADIR="$VDOT_CHIPYARD_ENV/share/bison"
fi
export PATH="$VDOT_ROOT/tools:$PATH"
export CPATH="$VDOT_ROOT/tools/sysroot/usr/include:$VDOT_ROOT/tools/sysroot/usr/include/x86_64-linux-gnu${CPATH:+:$CPATH}"
export LIBRARY_PATH="$VDOT_ROOT/tools/lib:$VDOT_ROOT/tools/sysroot/usr/lib/x86_64-linux-gnu${LIBRARY_PATH:+:$LIBRARY_PATH}"
export COURSIER_REPOSITORIES=${COURSIER_REPOSITORIES:-https://repo.maven.apache.org/maven2}
export NEMU_HOME="$VDOT_ROOT/third_party/NEMU"
export NOOP_HOME="$VDOT_ROOT/third_party/XiangShan"
export AM_HOME="$VDOT_ROOT/third_party/xs-env/nexus-am"
export JAVA_OPTS=${JAVA_OPTS:--Xmx2g -Xss8m -XX:ActiveProcessorCount=2}
