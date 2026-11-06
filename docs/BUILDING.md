# 构建说明

环境安装、固定上游及非gitlink资源见[环境准备](BOOTSTRAP.md)。本项目使用昆明湖V2单核MinimalConfig，保留128位向量执行单元。

## 准备源码

在独立检出中获取固定XiangShan、NEMU和工具后，检查并应用补丁：

```sh
git -C third_party/XiangShan apply --check ../../patches/xiangshan.patch
git -C third_party/XiangShan apply ../../patches/xiangshan.patch
git -C third_party/NEMU apply --check ../../patches/nemu.patch
git -C third_party/NEMU apply ../../patches/nemu.patch
```

已应用补丁的目录跳过这一步。将改动文件提交到各自本地仓库，并记录实际提交号。模型的dirty标志来自真实构建树状态。

## 构建

以下配置用于已完成的点积累加整核构建。编译依赖Linux用户systemd会话；临时交换空间和磁盘需有余量。

```sh
source scripts/env.sh
export CCACHE_DISABLE=1
export VDOT_MILL_HEAP=512m
export VDOT_JAVA_HEAP=6G
export VDOT_BUILD_MEMORY_MAX=9500M
export VDOT_FIRTOOL_MEMORY_MAX=7000M
export VDOT_COMPILE_MEMORY_MAX=8500M
export VDOT_CPP_JOBS=3
export VDOT_NATIVE_FILE_HEAP=0
export VDOT_HEAP_BACKING_DIR=
export VDOT_USE_JEMALLOC=1
export VDOT_CPP_DECODER_O0=1
export VDOT_INLINE_MULT=1
export VDOT_EMU_TRACE=
bash scripts/build_workloads.sh
bash scripts/build_nemu.sh standalone
bash scripts/build_nemu.sh reference
bash scripts/build_emu.sh
```

`VDOT_EMU_TRACE=`生成无波形性能模型。需要采集FST时，在独立构建目录按构建脚本的波形选项重新生成模型，保留该次构建与运行记录。

固定工具包括Mill 0.12.3、Chisel 6.7.0、firtool 1.62.1、Verilator 5.022和RISC-V交叉工具链。仓库的兼容配置处理固定GCC选项、Verilator波形接口和低内存生成。`local.env`只在本机生效，不进入源码仓库。

## 输出和检查

| 输出 | 位置 |
|---|---|
| RTL仿真器 | third_party/XiangShan/build/emu |
| NEMU解释器 | build/nemu/standalone/riscv64-nemu-interpreter |
| NEMU动态参考库 | build/nemu/reference/riscv64-nemu-interpreter-so |
| 裸机程序及flash | build/workloads/ |
| 分阶段构建日志、退出码和摘要 | reports/vdot-build-*/ |

构建完成后运行：

```sh
python3 scripts/check_repository.py --replay-patches
python3 -m unittest discover -s tests -v
```

整核功能、差分和性能命令见[复现说明](累加融合复现.md)。各项测试分别保存自己的输入副本、命令、退出码和结果。
