# 构建与运行记录

本文为开发中的复现入口。尚未完成干净检出复现，也尚未成功运行香山整核，不能据此标记三阶段完成。

## 固定源码

| 工程 | 官方地址 | 基准提交 |
|---|---|---|
| XiangShan | https://github.com/OpenXiangShan/XiangShan | `7b16188f7f18a97be69c9b1a2dae8a446eec3b47` |
| NEMU | https://github.com/OpenXiangShan/NEMU | `d772a9d9e06f663d529bd1c6518480c1ee59ded2` |
| xs-env | https://github.com/OpenXiangShan/xs-env | `822e3581a2757d4a9848b065fd2a3057957b401e` |

香山子模块必须按其固定提交初始化，不能自行更新到各子模块最新分支。`source_manifest.py` 记录每个运行的实际 Git 提交、子模块身份和改动文件摘要。

在新的 `third_party/XiangShan`、`third_party/NEMU` 检出上述基准提交并初始化子模块后，分别执行 `git apply ../../patches/xiangshan.patch`、`git apply ../../patches/nemu.patch`。应用前确认目标工作区干净；当前开发目录中补丁已经应用，不要重复应用。

## 当前工具环境

`scripts/env.sh` 只配置当前 Shell，默认复用本机 `/home/yh/chipyard/.conda-env` 的 RISC-V GCC、Java 和辅助程序，以及本项目 `tools/` 中的 Mill、依赖库。路径可通过本地 `local.env` 或 `VDOT_CHIPYARD_ENV` 覆盖。

已使用 Mill 0.12.3、Scala 2.13.15、Chisel 6.7.0、RISC-V GCC 13.2.0 和本机 Conda 环境中的 OpenJDK 20。干净机器仍需按固定版本的香山环境要求安装 Verilator、C/C++ 编译器、Make、Python、设备树编译器、Bison、Flex、压缩库等依赖。工具安装及版本自动检查脚本尚未完备。

本机的 `/usr/bin/java` 与 Conda Java 版本不同；使用脚本中的 `JAVA_HOME`，不要只依据 PATH 推断 Java 版本。

## 软件与数据通路功能测试

从项目根目录运行：

```bash
python3 -m unittest discover -s tests -v
source scripts/env.sh
mill -i -j 1 datapath.test
bash scripts/build_workloads.sh
bash scripts/build_nemu.sh standalone
build/nemu/standalone/riscv64-nemu-interpreter --batch \
  --flash-image=build/workloads/flash.bin build/workloads/vdot_test.bin \
  > reports/nemu-functional.log 2>&1
python3 scripts/check_run.py reports/nemu-functional.log VDOT_PASS
```

NEMU 的通过条件必须同时包含工作负载完成标记、`HIT GOOD TRAP`，并且没有异常错误标记。仅看到 `GOOD TRAP` 不足以排除上游关键错误的处理路径。`vdot_vstart_probe` 是独立行为探测，固定 NEMU 会报非法指令，不能将其当作必须成功的 vdot 主测试。

`vadd_test` 会按赛题要求输出当前团队标识和本机 IP。该原始日志应留在本机，公开前检查网络和个人信息。

## NEMU 差分库

```bash
bash scripts/build_nemu.sh reference
```

输出位于 `build/nemu/reference/riscv64-nemu-interpreter-so`。`configs/` 保存当前使用的完整独立运行、参考库两份配置。两种配置不同，必须分别构建，不能将普通可执行程序误用为参考动态库。

可以独立检查动态库ABI，确认其通过`init_v2/regcpy/memcpy/exec`实际执行vdot：

```bash
python3 scripts/check_reference_abi.py \
  build/nemu/reference/riscv64-nemu-interpreter-so --expected-result 8
bash scripts/build_fault_reference.sh
```

第二条命令将当前NEMU复制到隔离目录，仅对vdot结果最低位注入错误，打印错误库的独立路径；不会改动正常源码或参考库。用打印的路径再次运行ABI检查并传入`--expected-result 9`，再执行`scripts/run_fault_check.sh <错误库路径>`检验真正的RTL向量比较器。ABI检查只包含REF，故障库构建成功也不代表RTL故障注入已通过。完整判据见[DIFFTEST_CHECKS.md](DIFFTEST_CHECKS.md)。

## 香山全核构建

```bash
bash scripts/build_emu.sh
```

当前脚本按阶段执行：Chisel 仅生成 CHIRRTL 并写辅助文件，退出 Java 后独立运行 firtool，再生成 SRAM 模型、处理仿真断言和构建 Verilator 模型。默认单核 `MinimalConfig`，关闭仿真统计/数据库，Difftest 保持启用，带 FST 支持。

C++构建明确使用系统GCC/G++及`OPT_FAST=-O2 -fno-tree-slp-vectorize`。固定Difftest默认的`-fno-slp-vectorize`属于另一编译器的选项，会被当前GCC拒绝。固定Verilator5.022还需要`configs/verilator_5_022_trace.h`，使Difftest的通用trace指针名称对应实际FST/VCD具体类；头文件对版本精确检查，不改变比较器。通过`MAKEFILES=configs/verilator_5_022.mk`仅将它预包含到四个使用波形接口的用户对象，不能全局添加到模型对象，否则会干扰GCC的PCH加载。实际`VSimTop.o/emu.o/waveform.o/verilator.o`目标已编译通过；完整链接及波形仍需后续验证。

C++阶段默认两个编译任务，总内存仍受5500MiB上限约束。可用`VDOT_CPP_JOBS=1`降低并行度。JVM及firtool阶段仍各自串行执行，与C++编译分离。

默认 Java 堆8GiB、Chisel进程组上限4800MiB、firtool上限5500MiB、模型编译上限5500MiB。每阶段独立记录命令、日志、退出状态和资源，最后检查源码摘要未漂移；该方式依赖 Linux 用户 systemd 会话。整套脚本仍需完整成功运行和干净环境复现后才能标记可复现。

`scripts/lowmem-bin/mill` 直接调用固定 Mill 0.12.3 的主入口，限制构建工具自身的 JVM 堆为 384 MiB；实际硬件生成子进程仍通过 Makefile 的 `JVM_XMX` 参数配置。仅设置普通 Mill 启动脚本的 `JAVA_OPTS` 不能保证该主进程继承同样上限。

本机普通 4500 MiB 堆在转换期间持续满载。已验证 JVM 的文件映射堆能够在 384 MiB 内存上限内校验 512 MiB 存活数据。脚本默认启用该方式，可显式指定：

```bash
VDOT_JAVA_HEAP=8G \
  VDOT_HEAP_BACKING_DIR="$PWD/build/jvm-heap" \
  VDOT_BUILD_MEMORY_MAX=4800M bash scripts/build_emu.sh
```

该方式通过 `-XX:AllocateHeapAt` 在项目目录下创建临时堆映射，进程退出后 JVM 关闭临时文件。可能因页读写而降低构建速度。它只用于构建，不用于 RTL 性能计时。机制见 [OpenJDK 20 实现](https://github.com/openjdk/jdk20u/blob/master/src/hotspot/os/posix/os_posix.cpp) 与 [JVM 选项文档](https://docs.oracle.com/en/java/javase/11/tools/java.html)。

独立 firtool 1.62.1 已成功生成 SystemVerilog：5分46秒、最大RSS 5359524KiB，见 `reports/firtool-standalone-time.txt`。随后带 FST 的 Verilator 模型生成仍超过5200MiB，当前测试原生文件映射分配库。

`scripts/lowmem-bin/verilator` 仅对模型生成的 Verilator 5.022 原生进程使用 `libvmmalloc`，默认临时池32GiB，退出后释放，仿真器运行不加载该库。小规模测试在384MiB限制下校验512MiB数据通过。工具库来自 Debian 官方 `libvmmalloc1=1.8-2`，本地安装入口为 `bash scripts/install_memory_helper.sh`，带固定SHA256校验，不修改系统目录。机制见 [官方手册](https://pmem.io/vmem/manpages/linux/master/libvmmalloc/libvmmalloc.7.html) 和 [Debian包信息](https://packages.debian.org/bullseye/libvmmalloc1)。整核模型是否生成成功仍待运行证据。

分阶段默认需要约33GiB临时堆空间，另给RTL、C++和对象文件保留充足空间。默认追踪12层层级、生成器优化等级O1，均只作用于宿主模型构建，实际波形层级仍需验证。`VDOT_VERILATOR_BIN` 可覆盖本机原生 Verilator 路径，`VDOT_NATIVE_FILE_HEAP=0` 可在有足够内存时禁用原生文件映射库。不要把构建时间计入处理器性能测量。

wrapper在所有`-O`选项之后显式追加`--inline-mult 2000`。Verilator5.022的`-O3`会设置最大内联，随后`-O1`不会撤销该设置；小例已实测33个与1个内联实例的差异，整核改善尚待重新生成模型验证。`VDOT_INLINE_MULT`可显式覆盖；当前开发中已经生成的整核C++保留原参数，不为该宿主优化重新丢弃有效模型。详见[固定版本低内存选项核对](LOWMEM_OPTIONS.md)。

可用环境变量显式指定配置和资源：

```bash
VDOT_CONFIG=MinimalConfig VDOT_JAVA_HEAP=4500m \
  VDOT_BUILD_MEMORY_MAX=5500M bash scripts/build_emu.sh
```

此前的 `VdotSimConfig` 实验遇到软 PTW 缓冲空指针和缩小 L3 导致的索引越界，实验代码及临时 MemBlock 改动已撤回，失败日志与开发提交保留了经过。当前继续验证原有 `MinimalConfig` 配合官方统计开关。

已有SystemVerilog、SRAM模型和Difftest辅助文件时，可用以下开发恢复入口，只重启原生模型构建：

```bash
bash scripts/resume_model_build.sh
```

它会启动独立用户systemd服务，终端或聊天连接断开后仍可继续运行，并在打印的报告目录保存服务名、构建输入摘要、命令、日志、退出状态和时间。用 `systemctl --user status <报告中的服务名>` 查看实际状态；`BUILD_STARTED`只表示已启动，必须出现 `MODEL_BUILD_COMPLETE`、退出码0和可执行的`build/emu`才算成功。此恢复入口依赖现有生成文件，不能替代干净检出复现。

在同一构建之后继续本地验证，可运行`bash scripts/validate_rtl_when_ready.sh <构建报告目录> <错误库路径>`。它等待指定构建的成功记录与校验值，按序执行功能、差分、故障注入恢复、性能和初始波形运行，首个失败立即退出；实际波形分析和完整复现不由该队列自动判定通过。两个后台服务均不执行推送、上传或比赛提交。

完整仿真器生成后，还需核对其 `--help`，实际验证 `scripts/run_rtl.sh` 的运行参数、短窗口波形、真实Difftest和性能命令。不要根据NEMU结果替代这些待完成步骤。
