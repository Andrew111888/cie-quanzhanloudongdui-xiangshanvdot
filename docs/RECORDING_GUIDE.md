# 三阶段录屏指南

## 准备

在本机工程根目录设置已构建的模型和参考库：

```sh
cd /home/yh/cie/vdot-kmhv2
source scripts/env.sh
export VDOT_MODEL_ROOT="$PWD/build/acc-core-20261106"
export VDOT_CURRENT_EMU="$VDOT_MODEL_ROOT/third_party/XiangShan/build/emu"
export VDOT_CURRENT_REF="$PWD/build/acc-nemu-precedence/reference/riscv64-nemu-interpreter-so"
export VDOT_FLASH="$VDOT_MODEL_ROOT/build/workloads/flash.bin"
```

## 第一阶段：环境与向量加法

展示固定版本、构建日志、问候、队名及IP输出，再按第一阶段文档中的PC、ROB和物理目的关联解释波形。

已有带波形的原点积模型可用于vadd操作录制：

```sh
export VDOT_TRACE_ROOT="$PWD/build/clean-commit-validation-20261106"
VDOT_EMU_PATH="$VDOT_TRACE_ROOT/third_party/XiangShan/build/emu" VDOT_REF_SO="$VDOT_TRACE_ROOT/build/nemu/reference/riscv64-nemu-interpreter-so" VDOT_WAVE_BEGIN=0 VDOT_WAVE_END=15000   bash "$VDOT_TRACE_ROOT/scripts/run_rtl.sh" vadd_test
```

打开命令输出目录中的run.log和wave.fst。完整部署记录及vadd分析见[第一阶段](submission/stage1.md)。当前共享路径的性能模型关闭了波形；上述FST对应带波形模型。

## 第二阶段：设计与基础测试

展示[语义](DESIGN.md)、[数据通路图](figures/acc-retimed-datapath.svg)、Chisel补丁和当前rtl/目录。

依次解释8路乘法、提前一级压缩、前缀加法、两级使能及高96位清零。普通点积选择累加输入0，累加版读取旧vd低32位；译码分别消除假依赖和保留真实依赖。

```sh
bash scripts/run_basic_validation.sh "$VDOT_CURRENT_EMU" "$VDOT_CURRENT_REF"
```

日志逐例显示正数8、负数-8、正边界131072、负边界-130048、最大值129032和零值0，核对完整128位。测试结束检查VDOT_BASIC_PASS、GOOD TRAP和退出码。

## 第三阶段：差分与性能

展示NEMU的独立计算及目标写回，再打开[错误参考记录](data/acc-results/fault/results.json)及同目录日志。正确值0x12345680，错误参考0x12345681，三轮退出码0/1/0。交叉异常的修正前后对照见[48例记录](data/acc-results/precedence/results.json)。

性能部分使用[完整报告](累加融合实验结果.md)和[逐次CSV](data/acc-results/README.md)，说明计时边界、预热、五次重复及较快RVV基线。

- 单链融合更慢，4/8条独立链在512轮时的周期比为1.428/2.255。
- 含访存长点积K=32有收益，K=128/512仍由RVV16更快。
- 算术模块的1.5 ns裕量、1 ns失败和面积单位按实际约束解释。

讲解当前共享路径时使用当前源码和数据。原平衡树FST可用于说明原点积流水，模型身份见该次记录。
