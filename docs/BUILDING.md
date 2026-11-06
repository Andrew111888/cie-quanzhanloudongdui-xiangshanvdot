# 构建与运行记录

本文为固定版本的构建与运行入口。开发与干净检出证据分别保留；本轮完整构建身份、资源和验收状态见CLEAN_REPRODUCTION.md，不能只依据某个中间文件判断三阶段交付完成。

## 2026-11-06本轮宿主配置

新独立目录为/home/yh/cie/vdot-kmhv2-repro-20261106，构建源码4e5cfce。Chisel和firtool在此目录从源码生成，Verilator采用原生jemalloc、O1、inline-mult=1和trace-depth=10，生成DecodeUnit的宿主C++按兼容规则使用O0，其余快速对象使用O2。两级点积RTL没有因宿主选项改变。

scripts/firtool_file_heap.sh与本轮实际执行的reports/firtool-file-heap.sh字节一致，为固定firtool单独提供16GiB文件映射池。它要求先按BOOTSTRAP.md安装本地libvmmalloc；不修改系统库。以下显式配置可用于后续从头复现，各阶段的实际成功记录与本次恢复经过见CLEAN_REPRODUCTION.md：

```bash
VDOT_FIRTOOL="$PWD/scripts/firtool_file_heap.sh" \
VDOT_NATIVE_FILE_HEAP=0 VDOT_USE_JEMALLOC=1 \
VDOT_INLINE_MULT=1 VDOT_VERILATOR_OPT=1 VDOT_TRACE_DEPTH=10 \
VDOT_CPP_DECODER_O0=1 VDOT_CPP_JOBS=4 \
VDOT_COMPILE_MEMORY_MAX=8G bash scripts/build_emu.sh
```

本轮实际先在6400MiB模型阶段触及内存限制，保留退出137。文件堆尝试因磁盘写回过慢被人工停止；启用8GiB临时系统交换空间后，原生模型在MemoryMax=8G、MemorySwapMax=2G的独立用户服务中生成，再复用本目录自己的C++目标续编译。脚本默认构建scope的MemorySwapMax仍为0，上述从头入口没有伪记成此次实际连续运行的命令。临时交换空间帮助释放其他进程占用，不改变处理器周期；具体命令、资源与成功阶段分别记录在composite-build.json及其指向的原始目录。

后文保留通用入口、默认值和历史资源实验；本轮显式参数优先于对默认值的推断。

## 固定源码

| 工程 | 官方地址 | 基准提交 |
|---|---|---|
| XiangShan | https://github.com/OpenXiangShan/XiangShan | `7b16188f7f18a97be69c9b1a2dae8a446eec3b47` |
| NEMU | https://github.com/OpenXiangShan/NEMU | `d772a9d9e06f663d529bd1c6518480c1ee59ded2` |
| xs-env | https://github.com/OpenXiangShan/xs-env | `822e3581a2757d4a9848b065fd2a3057957b401e` |

香山子模块必须按其固定提交初始化，不能自行更新到各子模块最新分支。`source_manifest.py` 记录每个运行的实际 Git 提交、子模块身份和改动文件摘要。

在新的 `third_party/XiangShan`、`third_party/NEMU` 检出上述基准提交并初始化子模块后，分别执行 `git apply ../../patches/xiangshan.patch`、`git apply ../../patches/nemu.patch`。应用前确认目标工作区干净；当前开发目录中补丁已经应用，不要重复应用。

## 当前工具环境

实际宿主为Ubuntu 26.04.1 LTS、x86_64、Linux 7.0.0-38-generic，Intel Core i7-11700、16个逻辑线程；内存总量16056976KiB（约15.3GiB），交换空间4194300KiB。采集在独立目录reports/host-environment.json，不包含主机名、网络地址或联系信息；可用磁盘空间随运行变化，不能当作最低配置。

`scripts/env.sh` 只配置当前 Shell，默认复用本机 `/home/yh/chipyard/.conda-env` 的 RISC-V GCC、Java 和辅助程序，以及本项目 `tools/` 中的 Mill、依赖库。路径可通过本地 `local.env` 或 `VDOT_CHIPYARD_ENV` 覆盖。

已使用Mill 0.12.3、Scala 2.13.15、Chisel 6.7.0、RISC-V GCC 13.2.0、OpenJDK 20.0.2、Verilator 5.022、firtool 1.62.1及宿主GCC/G++ 15.2.0。scripts/toolchain_manifest.py记录实际可执行文件、版本与SHA256，本轮输出在独立目录reports/toolchain-identity.json。环境准备详见BOOTSTRAP.md；没有完整的新系统自动安装器或Conda传递依赖锁，仍需满足系统库、Make、Python、dtc、Bison、Flex等依赖。

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

C++构建明确使用系统GCC/G++及`OPT_FAST=-O2 -fno-tree-slp-vectorize`。固定Difftest默认的`-fno-slp-vectorize`属于另一编译器的选项，会被当前GCC拒绝。固定Verilator5.022还需要`configs/verilator_5_022_trace.h`，使Difftest的通用trace指针名称对应实际FST/VCD具体类；头文件对版本精确检查，不改变比较器。通过`MAKEFILES=configs/verilator_5_022.mk`仅将它预包含到四个使用波形接口的用户对象，不能全局添加到模型对象，否则会干扰GCC的PCH加载。实际完整链接与FST读写均已通过，兼容头未修改checker。

C++阶段默认两个编译任务，总内存仍受5500MiB上限约束。可用`VDOT_CPP_JOBS=1`降低并行度。JVM及firtool阶段仍各自串行执行，与C++编译分离。

默认Java堆8GiB、Chisel进程组上限4800MiB、firtool上限5500MiB、模型编译上限5500MiB。每阶段独立记录命令、日志、退出状态和资源，最后检查源码摘要未漂移；该方式依赖Linux用户systemd会话。必须同时核对BUILD_COMPLETE、退出0、二进制摘要和后续真实运行，不能把任务启动视为成功。

当前独立扩展核复现显式使用 `VDOT_COMPILE_MEMORY_MAX=7G bash scripts/build_emu.sh`；原核也在模型生成阶段把进程组限制在线调至7GiB并保存调整记录。两者实际资源参数见CLEAN_REPRODUCTION.md及各阶段命令/日志，不能仅依据脚本默认值推断实测峰值。

`scripts/lowmem-bin/mill`直接调用固定Mill 0.12.3主入口，并在新检出中先创建out锁目录。构建工具自身默认堆为2GiB，可用VDOT_MILL_HEAP显式覆盖；384MiB只在已有编译缓存时跑通过，干净检出编译315个Rocket Chip源码会Java heap OOM，2GiB同目标已实际通过。硬件生成子进程另由-Djvm-xmx参数配置，不能将子进程8GiB误当成Mill自身的上限。

本机普通 4500 MiB 堆在转换期间持续满载。已验证 JVM 的文件映射堆能够在 384 MiB 内存上限内校验 512 MiB 存活数据。脚本默认启用该方式，可显式指定：

```bash
VDOT_JAVA_HEAP=8G \
  VDOT_HEAP_BACKING_DIR="$PWD/build/jvm-heap" \
  VDOT_BUILD_MEMORY_MAX=4800M bash scripts/build_emu.sh
```

该方式通过 `-XX:AllocateHeapAt` 在项目目录下创建临时堆映射，进程退出后 JVM 关闭临时文件。可能因页读写而降低构建速度。它只用于构建，不用于 RTL 性能计时。机制见 [OpenJDK 20 实现](https://github.com/openjdk/jdk20u/blob/master/src/hotspot/os/posix/os_posix.cpp) 与 [JVM 选项文档](https://docs.oracle.com/en/java/javase/11/tools/java.html)。

早期开发恢复路线的独立firtool 1.62.1实测5分46秒、最大RSS5359524KiB，见reports/firtool-standalone-time.txt。随后带FST的Verilator在常规分配器下超过5200MiB；改用原生文件映射分配库后完成模型生成及C++链接。本轮完整干净构建已成功，各阶段的新测量见CLEAN_REPRODUCTION.md；不能混用两轮的资源结果。

`scripts/lowmem-bin/verilator` 仅对模型生成的Verilator 5.022原生进程使用 `libvmmalloc`，默认临时池32GiB，退出后释放，仿真器运行不加载该库。小规模测试在384MiB限制下校验512MiB数据通过；整核生成成功证据为 `reports/model-resume-20261104T155853Z-3297719/`，该次make随后因C++选项不兼容失败，经修复后在 `reports/model-resume-20261104T170533Z-3349034/` 完成链接。工具库来自Debian官方 `libvmmalloc1=1.8-2`，本地安装入口为 `bash scripts/install_memory_helper.sh`，带固定SHA256校验，不修改系统目录。机制见 [官方手册](https://pmem.io/vmem/manpages/linux/master/libvmmalloc/libvmmalloc.7.html) 和 [Debian包信息](https://packages.debian.org/bullseye/libvmmalloc1)。

分阶段默认需要约33GiB临时堆空间，另给RTL、C++和对象文件保留充足空间。默认追踪12层层级、生成器优化等级O1，均只作用于宿主模型构建；实际FST已提取到后端译码、重命名、执行、写回与提交接口。`VDOT_VERILATOR_BIN`可覆盖本机原生Verilator路径，`VDOT_NATIVE_FILE_HEAP=0`可在有足够内存时禁用原生文件映射库。不要把构建时间计入处理器性能测量。

wrapper在所有`-O`选项之后显式追加`--inline-mult 2000`。Verilator5.022的`-O3`会设置最大内联，随后`-O1`不会撤销该设置；小例已实测33个与1个内联实例的差异。本轮原核和扩展核的干净构建均已使用显式内联参数成功生成模型，但未在同条件下与旧参数做完整A/B资源实验，不声称具体内存收益。`VDOT_INLINE_MULT`可显式覆盖；早期开发模型仍保留历史参数。详见[固定版本低内存选项核对](LOWMEM_OPTIONS.md)。

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

若Chisel已成功而firtool被停止，可从原构建报告恢复：

```bash
bash scripts/build_emu.sh --resume-fir /absolute/path/to/prior-build-report
```

恢复前会核对原Chisel退出0、平台与资源仓库身份、项目输入、单核配置及完整FIR的SHA256；仅允许恢复入口自身的脚本修订，不允许其它输入漂移。新报告以chisel-reuse.json引用已完成阶段，不伪造一次新的Chisel运行。篡改FIR摘要的反例已被实际拒绝；恢复仍须完成firtool、原生编译、最终源码复核和真实运行才能验收。

它会启动独立用户systemd服务，终端或聊天连接断开后仍可继续运行，并在打印的报告目录保存服务名、构建输入摘要、命令、日志、退出状态和时间。用 `systemctl --user status <报告中的服务名>` 查看实际状态；`BUILD_STARTED`只表示已启动，必须出现 `MODEL_BUILD_COMPLETE`、退出码0和可执行的`build/emu`才算成功。此恢复入口依赖现有生成文件，不能替代干净检出复现。

在同一构建之后继续本地验证，可运行`bash scripts/validate_rtl_when_ready.sh <构建报告目录> <错误库路径>`。它等待指定构建的成功记录与校验值，按序执行功能、差分、故障注入恢复、性能和初始波形运行，首个失败立即退出；实际波形分析和完整复现不由该队列自动判定通过。两个后台服务均不执行推送、上传或比赛提交。

scripts/run_rtl.sh的参数、短窗口FST、真实Difftest及性能命令已有实际运行证据。独立检出的完整构建和回归单独保留，结果见CLEAN_REPRODUCTION.md；不以开发目录的可运行二进制替代最终复现。

## 本轮性能模型的内存与编译恢复方案

本轮新增实验在文件映射堆写回过多、普通堆5200MiB保护上限失败后，采用jemalloc单arena、Verilator O1、inline-mult=1、关闭波形及6GiB进程组上限完成模型生成。该次生成耗时91.92秒，最大RSS为6019712KiB；它是在测得约6.8GiB可用内存时完成的实测，不作为任意机器的最低配置承诺。本次没有启用新增交换文件。本机可选分配库为libjemalloc2 5.3.0-4，脚本在启用该选项时检查实际库文件。

GCC15对生成的DecodeUnit表达式优化时间很长。可显式开启VDOT_CPP_DECODER_O0=1，仅将该模块的宿主C++快速对象改为O0并使用普通头文件，其他快速对象仍为O2。规则位于configs/gcc_decode_compat.mk，与实际生成新仿真器时使用的兼容规则逐字节相同。它不修改RTL或客体周期计数；新模型完整功能差分、流水压力和故障注入已通过，新增性能结果另见OPTIMIZATION.md。

已有同配置RTL和生成模型时，本地可按下列实测参数恢复。此入口沿用现有生成文件，不能替代干净构建；修改波形/内联等生成参数后，需要重新生成匹配的模型，不能只凭旧可执行文件存在判断成功。

```bash
VDOT_NATIVE_FILE_HEAP=0 VDOT_USE_JEMALLOC=1 \
VDOT_INLINE_MULT=1 VDOT_COMPILE_MEMORY_MAX=6G \
VDOT_EMU_TRACE= VDOT_CPP_DECODER_O0=1 VDOT_CPP_JOBS=2 \
bash scripts/resume_model_build.sh
```

该入口已实际重放，退出0、MODEL_BUILD_COMPLETE及仿真器SHA256一致均核对通过。此次重放复用了已有生成模型与对象，不另算一次从空目录生成。父进程会将这些参数显式传给持久用户服务；jemalloc仅在构建进程内加载。VDOT_EMU_TRACE为空的性能构建不产生新的FST证据，原调试构建的波形继续绑定原版本。

完整构建入口build_emu.sh也识别上述环境参数，但其Chisel和firtool阶段的内存与磁盘需求仍须分别满足。不要把本次原生模型生成的峰值套用到整套工具链，也不要将宿主编译时间当作vdot硬件性能。
