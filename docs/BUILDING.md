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

## 香山全核构建

```bash
bash scripts/build_emu.sh
```

默认使用单核 `MinimalConfig`、4500 MiB 子 JVM 堆、5500 MiB 进程组内存上限、单任务 Make，并启用 FST 波形编译支持。通过官方 `DISABLE_PERF=1 DISABLE_ALWAYSDB=1` 关闭仿真统计和数据库生成，Difftest 继续启用。脚本为每次构建建立独立报告目录，保存命令、源码摘要、日志、内存和退出状态。它依赖当前 Linux 用户的 systemd 会话；内存不足会失败，脚本不会自动扩大上限。

`scripts/lowmem-bin/mill` 直接调用固定 Mill 0.12.3 的主入口，限制构建工具自身的 JVM 堆为 384 MiB；实际硬件生成子进程仍通过 Makefile 的 `JVM_XMX` 参数配置。仅设置普通 Mill 启动脚本的 `JAVA_OPTS` 不能保证该主进程继承同样上限。

本机普通 4500 MiB 堆仍在转换期间持续满载。已验证 JVM 的文件映射堆能够在 384 MiB 内存上限内校验 512 MiB 存活数据。本机当前尝试的完整命令为：

```bash
VDOT_JAVA_HEAP=8G \
  VDOT_HEAP_BACKING_DIR="$PWD/build/jvm-heap" \
  VDOT_BUILD_MEMORY_MAX=4800M bash scripts/build_emu.sh
```

该方式通过 `-XX:AllocateHeapAt` 在项目目录下创建临时堆映射，进程退出后 JVM 关闭临时文件。预留至少 9 GiB 磁盘空间；可能因页读写而降低构建速度。它只用于构建，不用于 RTL 性能计时。机制见 [OpenJDK 20 实现](https://github.com/openjdk/jdk20u/blob/master/src/hotspot/os/posix/os_posix.cpp) 与 [JVM 选项文档](https://docs.oracle.com/en/java/javase/11/tools/java.html)。完整全核生成是否通过仍以运行日志为准。

可用环境变量显式指定配置和资源：

```bash
VDOT_CONFIG=MinimalConfig VDOT_JAVA_HEAP=4500m \
  VDOT_BUILD_MEMORY_MAX=5500M bash scripts/build_emu.sh
```

此前的 `VdotSimConfig` 实验遇到软 PTW 缓冲空指针和缩小 L3 导致的索引越界，实验代码及临时 MemBlock 改动已撤回，失败日志与开发提交保留了经过。当前继续验证原有 `MinimalConfig` 配合官方统计开关。

完整仿真器生成后，还需核对其 `--help`，补全固定版本的 RTL 运行、短窗口波形、真实 Difftest 和性能命令。不要根据 NEMU 结果替代这些待完成步骤。
