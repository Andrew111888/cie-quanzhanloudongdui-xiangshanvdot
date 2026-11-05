# 干净源码检出的环境准备

核对日期：2026-11-05。本文件依据当前脚本、上游固定源码、本机工具及官方工件元数据整理，提供环境准备和源码复现步骤。独立目录的实际执行结果、构建身份和失败修复以CLEAN_REPRODUCTION.md为准。

同机使用既有工具的干净源码复现，与在全新操作系统重建全部工具环境是两项不同验证。已有目录、已有编译缓存或单独模块通过，都不能作为整套流程成功证据。当前独立目录为/home/yh/cie/vdot-kmhv2-repro-20261105，详细证据和中断恢复状态见CLEAN_REPRODUCTION.md。

## 1. 准备独立检出并固定作品版本

最终复现前先把全部源码、补丁和复现脚本提交到作品仓库，记录确定的交付 SHA。现有开发目录中的未提交文件不会进入新的 Git 克隆。下面示例从本机作品仓库创建独立检出；发布后也可将克隆源替换为公开作品仓库 URL。只在新目录执行，不能对当前正在开发的目录重复应用补丁。

```bash
: "${VDOT_RELEASE_SHA:?请先设置交付提交 SHA}"
VDOT_SOURCE_ROOT=/home/yh/cie/vdot-kmhv2
VDOT_REPRO_ROOT=/home/yh/cie/vdot-kmhv2-repro
test ! -e "$VDOT_REPRO_ROOT"
git clone --no-hardlinks "$VDOT_SOURCE_ROOT" "$VDOT_REPRO_ROOT"
git -C "$VDOT_REPRO_ROOT" checkout --detach "$VDOT_RELEASE_SHA"
cd "$VDOT_REPRO_ROOT"
```

该目录应没有 `build/`、`out/`、`third_party/` 和 `tools/` 的既有构建产物。可以复用已注明版本的外部工具和 Maven 下载缓存；这不能表述为无缓存构建。

## 2. 获取固定平台源码

| 工程 | 官方仓库 | 固定基准 SHA |
|---|---|---|
| XiangShan | [OpenXiangShan/XiangShan](https://github.com/OpenXiangShan/XiangShan) | `7b16188f7f18a97be69c9b1a2dae8a446eec3b47` |
| NEMU | [OpenXiangShan/NEMU](https://github.com/OpenXiangShan/NEMU) | `d772a9d9e06f663d529bd1c6518480c1ee59ded2` |
| xs-env | [OpenXiangShan/xs-env](https://github.com/OpenXiangShan/xs-env) | `822e3581a2757d4a9848b065fd2a3057957b401e` |

以下函数仅适用于目标路径尚不存在的新工程：

```bash
pin_repo() {
  local vdot_url=$1 vdot_sha=$2 vdot_dest=$3
  git init "$vdot_dest"
  git -C "$vdot_dest" remote add origin "$vdot_url"
  git -C "$vdot_dest" fetch --depth=1 origin "$vdot_sha"
  git -C "$vdot_dest" checkout --detach "$vdot_sha"
  test "$(git -C "$vdot_dest" rev-parse HEAD)" = "$vdot_sha"
}
mkdir -p third_party
pin_repo https://github.com/OpenXiangShan/XiangShan.git \
  7b16188f7f18a97be69c9b1a2dae8a446eec3b47 third_party/XiangShan
pin_repo https://github.com/OpenXiangShan/NEMU.git \
  d772a9d9e06f663d529bd1c6518480c1ee59ded2 third_party/NEMU
pin_repo https://github.com/OpenXiangShan/xs-env.git \
  822e3581a2757d4a9848b065fd2a3057957b401e third_party/xs-env
git -C third_party/XiangShan submodule update --init
git -C third_party/XiangShan/rocket-chip submodule update --init cde hardfloat
git -C third_party/XiangShan/openLLC submodule update --init openNCB
git -C third_party/XiangShan apply --check ../../patches/xiangshan.patch
git -C third_party/XiangShan apply ../../patches/xiangshan.patch
git -C third_party/NEMU apply --check ../../patches/nemu.patch
git -C third_party/NEMU apply ../../patches/nemu.patch
```

当前已使用的香山子模块身份如下。表中的嵌套三项是实际初始化项；其他未参与构建的嵌套测试仓库仍未初始化。上层 Git 提交的 gitlink 是获取依据，不能用各仓库最新分支替换。[来源：固定 XiangShan .gitmodules](https://github.com/OpenXiangShan/XiangShan/blob/7b16188f7f18a97be69c9b1a2dae8a446eec3b47/.gitmodules)

| XiangShan 内路径 | SHA |
|---|---|
| `ChiselAIA` | `13fddf2f435f69c96cdb4e6771730c61c67fbc45` |
| `ChiselIOPMP` | `09def1a7efa4707a74b7f31fe0a1c254b0940b78` |
| `coupledL2` | `55d8e69c690690dbc786e9ca2f3839a95555df95` |
| `difftest` | `3729300ae233816d332d057f170472ebe35147b0` |
| `fudian` | `e1bd4695ca7beb36a5ce7357e9527ad9e95b9ec1` |
| `huancun` | `65ef077373ecf398b4cecdea06b65ef9b8d79044` |
| `openLLC` | `9e6f78209b2f215fb9f6a8f0de250995ff3ab63d` |
| `openLLC/openNCB` | `5073e2c2efe19d71d11003df00425492067c4934` |
| `ready-to-run` | `cb8dd71834ba83cf5705ba8daa8a1d05dd64877a` |
| `rocket-chip` | `46f1efefa1ff431bffe3262e4830bc50316842f4` |
| `rocket-chip/cde` | `52768c97a27b254c0cc0ac9401feb55b29e18c28` |
| `rocket-chip/hardfloat` | `d93aa570806013dea479a92ba9bb33d1f2d4f69f` |
| `utility` | `2f0743f1f3ee1889049841926fa382cd0b32d8e2` |
| `yunsuan` | `955921186e34bb8915806582a238181a6dc3435c` |

`xs-env` 自身默认 gitlink 指向另一组主线平台版本，不是上述昆明湖 V2 组合。因此本路线不运行其自动更新平台脚本，也不在该目录内再构建另一个 XiangShan。当前工作负载是本项目的裸机程序，不依赖 AM 构建；`env.sh` 虽导出 `AM_HOME=third_party/xs-env/nexus-am`，该目录当前未初始化，也不能声称 AM 已部署验证。[来源：固定 xs-env README](https://github.com/OpenXiangShan/xs-env/blob/822e3581a2757d4a9848b065fd2a3057957b401e/README.md)

## 3. 预置 NEMU 的非 gitlink 资源

这些目录不是 NEMU `.gitmodules` 中的子模块。固定 NEMU 的 Makefile 在目录或标志文件缺失时自动克隆默认分支；仅固定 NEMU HEAD 不能固定它们。应在第一次调用 `make` 之前预置。

| NEMU 内完整路径 | 官方 URL | 实际 SHA | 当前两份配置中的作用 |
|---|---|---|---|
| `resource/softfloat/repo` | `https://github.com/ucb-bar/berkeley-softfloat-3` | `07ebd29db0cfb55723a79fbbffe99103ef38e305` | `CONFIG_FPU_SOFT=y`，实际编译；RV64 使用 `RISCV` specialization，参考库增加 `-fPIC` |
| `resource/gcpt_restore` | `https://github.com/OpenXiangShan/LibCheckpointAlpha.git` | `5169da768d18f4682a489eaabe7c071df6d6ef88` | `CONFIG_LIBCHECKPOINT_ALPHA_RESTORER=y`，serializer 实际包含该目录的 `src/restore_rom_addr.h`；vdot 裸机测试不要求另行构建 gcpt.bin |
| `resource/nanopb` | `https://github.com/nanopb/nanopb.git` | `625837ed2eedacc887ee6b747576b85a1f4b82b4` | make 解析时获取；当前关闭 `CONFIG_LIBCHECKPOINT_RESTORER`，未启用其序列化实现 |
| `resource/LibCheckpoint` | `https://github.com/OpenXiangShan/LibCheckpoint.git` | `1d8905cc2803c242ef257569128c2e68bf4272aa` | make 解析时获取；当前关闭 `CONFIG_LIBCHECKPOINT_RESTORER` |
| `resource/LibCheckpoint/resource/nanopb` | `https://github.com/nanopb/nanopb` | `671672b4d7994a9b07a307ae654885c7202ae886` | LibCheckpoint 自己的 gitlink；与上一项直接资源中的 nanopb 不是同一版本 |

来源：[softfloat.mk](https://github.com/OpenXiangShan/NEMU/blob/d772a9d9e06f663d529bd1c6518480c1ee59ded2/scripts/softfloat.mk)、[nanopb.mk](https://github.com/OpenXiangShan/NEMU/blob/d772a9d9e06f663d529bd1c6518480c1ee59ded2/scripts/nanopb.mk)、[Libcheckpoint.mk](https://github.com/OpenXiangShan/NEMU/blob/d772a9d9e06f663d529bd1c6518480c1ee59ded2/scripts/Libcheckpoint.mk)、[LibcheckpointAlpha.mk](https://github.com/OpenXiangShan/NEMU/blob/d772a9d9e06f663d529bd1c6518480c1ee59ded2/scripts/LibcheckpointAlpha.mk)。本轮核对上述仓库均为独立 Git 仓库，且没有未提交修改。

```bash
pin_repo https://github.com/ucb-bar/berkeley-softfloat-3 \
  07ebd29db0cfb55723a79fbbffe99103ef38e305 third_party/NEMU/resource/softfloat/repo
pin_repo https://github.com/OpenXiangShan/LibCheckpointAlpha.git \
  5169da768d18f4682a489eaabe7c071df6d6ef88 third_party/NEMU/resource/gcpt_restore
pin_repo https://github.com/nanopb/nanopb.git \
  625837ed2eedacc887ee6b747576b85a1f4b82b4 third_party/NEMU/resource/nanopb
pin_repo https://github.com/OpenXiangShan/LibCheckpoint.git \
  1d8905cc2803c242ef257569128c2e68bf4272aa third_party/NEMU/resource/LibCheckpoint
git -C third_party/NEMU/resource/LibCheckpoint submodule update --init
```

当前不需要 SimPoint 仓库。最终证据必须同时记录三个上游 HEAD、实际子模块和上述非 gitlink 资源；不能只依赖顶层 `git submodule status`。`source_manifest.py`现已采用schema v2，覆盖xs-env及4个额外资源仓库，同时记录LibCheckpoint的嵌套gitlink、根契约和构建文件；每次运行仍应检查实际清单。

## 4. 使用同版 Java、Verilator 和 RISC-V 工具链

同机干净源码复现可显式复用既有 Conda 环境；新环境必须同时具备下面目录结构和版本，不能只把路径改成空目录。

```bash
export VDOT_CHIPYARD_ENV=/home/yh/chipyard/.conda-env
export VDOT_VERILATOR_BIN="$VDOT_CHIPYARD_ENV/bin/verilator_bin"
source scripts/env.sh
"$JAVA_HOME/bin/java" -version
"$VDOT_VERILATOR_BIN" --version
riscv64-unknown-elf-gcc --version
```

| 工具 | 当前已核对身份 | 重要限制 |
|---|---|---|
| Java | OpenJDK `20.0.2-internal`，Conda `openjdk=20.0.2=haa376d0_2` | `env.sh` 指定 `JAVA_HOME`，但 PATH 中 `/usr/bin` 在 Conda bin 之前；直接运行 `java` 可能得到系统其他版本。低内存 Mill helper 使用 `JAVA_HOME/bin/java` |
| Verilator | `5.022`，Conda `verilator=5.022=h7cd9344_1` | 当前兼容头精确要求 `VERILATOR_VERSION_INTEGER=5022000`，不能直接换新版。wrapper 默认硬编码本机路径，迁移必须设置 `VDOT_VERILATOR_BIN` |
| RISC-V GCC | `riscv64-unknown-elf-gcc 13.2.0`，版本标识 `gc891d8dc23e` | 来自 Conda `riscv-tools=1.0.6=0_h1234567_g56c29e0`，位于 `riscv-tools/bin`；不是宿主 GCC |
| 宿主 C/C++ | `/usr/bin/gcc`、`/usr/bin/g++`，当前 15.2.0 | 构建明确不用 Conda 旧 sysroot 的编译器；可用 `VDOT_HOST_CC/VDOT_HOST_CXX` 覆盖，`AR=/usr/bin/ar` 仍固定 |
| 辅助工具 | Conda Bison 3.8.2、Flex 2.6.4、dtc 1.7.2；系统 Make 4.4.1、Python 3.14.3 | 还需 Git、curl、unzip、pkg-config、`/usr/bin/time`、dpkg-deb、Linux 用户 systemd 会话 |

对应 Conda 工件来源是 [conda-forge OpenJDK](https://conda.anaconda.org/conda-forge/linux-64/openjdk-20.0.2-haa376d0_2.conda)、[conda-forge Verilator](https://conda.anaconda.org/conda-forge/linux-64/verilator-5.022-h7cd9344_1.conda)、[ucb-bar RISC-V tools](https://conda.anaconda.org/ucb-bar/linux-64/riscv-tools-1.0.6-0_h1234567_g56c29e0.conda)。本机 conda-meta 记录的包 SHA256 分别为：

```text
0a88fdee61322f37bae674222488fc1153f1211312028c624db3f08bfda30617  openjdk-20.0.2-haa376d0_2.conda
e20a4c7da43a36652f6ed8d47a04f32c54c96c47c006b39793fd6b0abc2d9126  verilator-5.022-h7cd9344_1.conda
322019cf5aea325ab7ee094abb4d285d99e71d413fb52bdffa5c6870fdf5f2d4  riscv-tools-1.0.6-0_h1234567_g56c29e0.conda
```

这些是当前环境元数据中的精确包身份，不是独立环境重建测试结果；尚未交付完整 Conda 传递依赖锁文件。不要把下载并解压这三个包表述为已经得到可运行的完整环境，也不要直接复制带原安装前缀的 Conda 目录到其他路径。新系统的依赖求解、系统运行库及前缀迁移仍需另行验证。

## 5. 获取 Mill 0.12.3 与 firtool 1.62.1

Mill 的官方 Maven 工件已核对存在，本机 `tools/mill` 为 65,455,399 字节，与官方 `.sha1` 的 `9e2bd55d01428d0e14e93327bcb94e7d6cd0fdc0` 一致；下面 SHA256 是本机对该匹配工件计算的固定值，不冒充上游发布的 SHA256。[来源：官方 Maven 工件目录](https://repo.maven.apache.org/maven2/com/lihaoyi/mill-dist/0.12.3/)、[官方 SHA1](https://repo.maven.apache.org/maven2/com/lihaoyi/mill-dist/0.12.3/mill-dist-0.12.3.jar.sha1)

```bash
mkdir -p tools
curl --fail --location \
  https://repo.maven.apache.org/maven2/com/lihaoyi/mill-dist/0.12.3/mill-dist-0.12.3.jar \
  -o tools/mill
printf '%s  %s\n' 336346091edc69b248c306ca51aaccb73d888d8bf525ce45e02df89db449b41d tools/mill \
  | sha256sum --check
chmod +x tools/mill
```

项目根和上游 `.mill-version` 均为 `0.12.3`；低内存 helper 直接使用该工件中的 `mill.runner.MillMain`。Scala 2.13.15、Chisel 6.7.0、chiseltest 6.0.0 及其他 JVM 依赖由固定 `build.sc` 解析，不需要额外安装全局 Scala。当前使用 `COURSIER_REPOSITORIES=https://repo.maven.apache.org/maven2`；首次构建仍需访问 Maven，或提供事先校验的完整下载缓存。[来源：固定 XiangShan build.sc](https://github.com/OpenXiangShan/XiangShan/blob/7b16188f7f18a97be69c9b1a2dae8a446eec3b47/build.sc)

firtool 也可从已核对的官方 Maven 平台 JAR 获取。其 SHA1 `87ecc67b79ba9e51714a798f2007a23af563462e` 与本机缓存一致，JAR 内的 `firtool` 与当前缓存可执行文件逐字节相同。[来源：firtool 工件目录](https://repo.maven.apache.org/maven2/org/chipsalliance/llvm-firtool/1.62.1/)、[官方 SHA1](https://repo.maven.apache.org/maven2/org/chipsalliance/llvm-firtool/1.62.1/llvm-firtool-1.62.1-linux-x64.jar.sha1)

```bash
mkdir -p tools/packages tools/firtool-1.62.1/bin
curl --fail --location \
  https://repo.maven.apache.org/maven2/org/chipsalliance/llvm-firtool/1.62.1/llvm-firtool-1.62.1-linux-x64.jar \
  -o tools/packages/llvm-firtool-1.62.1-linux-x64.jar
printf '%s  %s\n' 63acdcb58ed12d4c1aa0ecdedc6e2425a252e94eefb75df9253c118d7d222039 \
  tools/packages/llvm-firtool-1.62.1-linux-x64.jar | sha256sum --check
unzip -p tools/packages/llvm-firtool-1.62.1-linux-x64.jar \
  org.chipsalliance/llvm-firtool/linux-x64/bin/firtool > tools/firtool-1.62.1/bin/firtool
chmod +x tools/firtool-1.62.1/bin/firtool
printf '%s  %s\n' 7f52d2a3782d09736895f66e7eb0e5cc4b3b1b18aa1ad0d04fca4cd6e42cd2ee \
  tools/firtool-1.62.1/bin/firtool | sha256sum --check
export VDOT_FIRTOOL="$PWD/tools/firtool-1.62.1/bin/firtool"
"$VDOT_FIRTOOL" --version
```

也可显式指向已验证的 `$HOME/.cache/llvm-firtool/1.62.1/bin/firtool`；`build_emu.sh` 默认只检查该路径已存在，并不负责自动安装 firtool。

## 6. 准备宿主头文件、链接库和内存 helper

当前系统为 x86_64 Linux；已使用系统 zlib 开发包、readline 8.3、SDL2 2.32.10、zstd 1.5.7 等运行库。NEMU standalone 的 `ldd` 实际包含 readline 和 SDL2。本地 `tools/sysroot` 的开发包不等于已经安装其全部运行时依赖；新操作系统必须另行满足这些运行库，不能只检查头文件存在。

同机复现可以从原工程复制已下载的三个开发包，并按下表验证后解压；也可从主来源下载相同包。SDL2 和 zstd 的本机 APT 元数据 `Filename/SHA256` 与本地包一致；Debian 主 pool 中这两个旧版本已经返回 404，不使用那个地址作为成功下载依据。

| 包 | 可定位的主来源 | 本地固定 SHA256 |
|---|---|---|
| `libreadline-dev_8.3-4_amd64.deb` | [Debian](https://deb.debian.org/debian/pool/main/r/readline/libreadline-dev_8.3-4_amd64.deb) | `c50cba7fef41f571eacf1147de0c9ca7303e7429f6299c208b1838e993931329` |
| `libsdl2-dev_2.32.10+dfsg-6_amd64.deb` | [Ubuntu archive](https://archive.ubuntu.com/ubuntu/pool/universe/libs/libsdl2/libsdl2-dev_2.32.10+dfsg-6_amd64.deb) | `b8e94803098e9299afc031fb898d0908387d88308eb62ea239918f455c69e985` |
| `libzstd-dev_1.5.7+dfsg-3_amd64.deb` | [Ubuntu archive](https://archive.ubuntu.com/ubuntu/pool/main/libz/libzstd/libzstd-dev_1.5.7+dfsg-3_amd64.deb) | `6d81369284ba3fd094f635fe6b9f8dfc71baaca36c1f758fe62244839e25ecf0` |

下面同机复制步骤不复制任何旧目标文件或模拟器，只复制已经下载的依赖包；从网络下载时也应逐项执行相同的 SHA256 校验。

```bash
mkdir -p tools/packages tools/sysroot tools/lib
cp "$VDOT_SOURCE_ROOT/tools/packages/libreadline-dev_8.3-4_amd64.deb" tools/packages/
cp "$VDOT_SOURCE_ROOT/tools/packages/libsdl2-dev_2.32.10+dfsg-6_amd64.deb" tools/packages/
cp "$VDOT_SOURCE_ROOT/tools/packages/libzstd-dev_1.5.7+dfsg-3_amd64.deb" tools/packages/
sha256sum --check <<'HASHES'
c50cba7fef41f571eacf1147de0c9ca7303e7429f6299c208b1838e993931329  tools/packages/libreadline-dev_8.3-4_amd64.deb
b8e94803098e9299afc031fb898d0908387d88308eb62ea239918f455c69e985  tools/packages/libsdl2-dev_2.32.10+dfsg-6_amd64.deb
6d81369284ba3fd094f635fe6b9f8dfc71baaca36c1f758fe62244839e25ecf0  tools/packages/libzstd-dev_1.5.7+dfsg-3_amd64.deb
HASHES
for vdot_package in tools/packages/*.deb; do
  dpkg-deb -x "$vdot_package" tools/sysroot
done
test -f /usr/lib/x86_64-linux-gnu/libSDL2-2.0.so.0
ln -s /usr/lib/x86_64-linux-gnu/libSDL2-2.0.so.0 tools/lib/libSDL2.so
bash scripts/install_memory_helper.sh
source scripts/env.sh
```

内存 helper 下载官方 `libvmmalloc1_1.8-2_amd64.deb`，脚本校验 SHA256 `f14d3979e7cd3920707a5206020af620a160bfdd4058c6ad41fb4371e081e883` 后只解压到 `tools/sysroot`，不会安装系统包。该路径仅支持 x86_64；当前 wrapper 的默认原生文件映射池为 32GiB，还需要足够磁盘空间。`VDOT_NATIVE_FILE_HEAP=0` 可禁用该分配库，但低内存机器是否还能完成构建需重新验证。[来源：Debian vmem 包入口](https://deb.debian.org/debian/pool/main/v/vmem/libvmmalloc1_1.8-2_amd64.deb)、[libvmmalloc 手册](https://github.com/pmem/vmem/blob/1.8/doc/libvmmalloc/libvmmalloc.7.md)

## 7. 执行复现并保留验收证据

工具及依赖就绪后，从新的项目根目录执行，不能复用当前开发目录的生成 RTL、C++ 或 NEMU 二进制：

```bash
source scripts/env.sh
python3 scripts/check_patches.py
python3 -m unittest discover -s tests -v
mill -i -j 1 datapath.test
bash scripts/build_workloads.sh
bash scripts/build_nemu.sh standalone
bash scripts/build_nemu.sh reference
bash scripts/build_emu.sh
```

`build_emu.sh` 分离 CHIRRTL、firtool、模型生成及 C++ 编译，默认保留向量的单核 `MinimalConfig`、FST、两个 C++ 任务；资源上限依赖可用的用户 systemd 会话。它显式使用本项目 `configs/verilator_5_022.mk` 和版本专用 trace 兼容头，因此不会只凭装上另一版本 Verilator 就自然兼容。`scripts/lowmem-bin/verilator` 在全部 `-O` 之后显式设置 `--inline-mult 2000`。其详细资源设置及宿主 GCC 选项见 `docs/BUILDING.md`。

源码与工具身份记录应在本次真实测试前生成，并在结束后复核。至少包含作品交付 SHA、三个上游及全部已用资源、补丁和配置校验值、Java/Verilator/GCC/Mill/firtool 版本及关键工件 SHA256。只有实际 `build/emu` 生成并成功运行后，才能继续按 `docs/BUILDING.md` 和 `scripts/run_rtl.sh` 复现向量加法、vdot、真实差分、故障注入恢复及性能结果。

本轮没有复制原工程的生成RTL、C++或模拟器。原核firtool阶段被停止后，已按源身份和FIR摘要校验恢复，并完成原核全量构建和真实vadd；随后应用补丁，从空的硬件生成目录重建扩展核。各阶段最终结果见CLEAN_REPRODUCTION.md。`resume_model_build.sh`依赖既有生成输入，不能单独替代本节全流程；原始干净检出到恢复完成的证据必须一并保留。
