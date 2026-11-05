# 基线、含访存内核与旧目标依赖对照

本轮在已通过版本之外补充三类实验。原版基准、独立检出验收、报告和发布归档保留原始内容；本轮结果在新的报告目录产生。完成状态以实际RTL运行和新验收记录为准。

## 测量方案

`workloads/benchmark_rvv.c` 比较三条语义等价的路径：每轮重新清零目标的原序列、复用已清零目标及独立零种子的优化RVV序列、单条vdot。优化序列仍执行有符号扩宽乘法和32位扩宽归约，结果完整高96位必须为零。初始化移到计时外，包含完整初始化的旧版测量继续独立保留，不将两类边界混为一个数字。

分别使用ta/ma与tu/mu，以及独立目标和真实源目的重叠链。每个分支采用8次展开、32/128/512条计算，预热后重复5次，共180条周期样本。独立输入前8项是混合符号，点积为6；依赖链初值为低四字节各1、其余零，乘数均为1，结果稳定为4。依赖链从一开始就满足高96位零的条件，才允许RVV复用目标；不把此优化推广为任意初始旧目标都无需清零。

周期边界为序列化的cycle CSR，计时包含计算循环及最终完整结果存储，初始化在边界外。每次运行检查完整128位结果，测量值是程序片段周期，不是裸FU延迟。编译后的指令清单应与源代码一同保存。

`workloads/dot_memory.c` 对32/128/512块数据分别执行真实输入加载、点积及逐块完整结果存储。每块计算8项，两源各读取8字节、各源块地址跨度16字节，输出16字节；最大有效点积输入为4096项。数据含正负边界及固定种子随机值，每块与独立C黄金结果核对，高96位也逐项检查。三种计算路径、两种tail策略各预热一次并重复5次，共90条样本。地址、数据和输出布局相同，报告预热后的表现，不将其称为冷缓存或完整LLM测量。

## 微架构改变

原OPIVV模板默认读取第三源旧vd。vdot的既定语义覆盖完整目标，不累加旧值，因而将该指令译码项的src3标为SrcType.no。vs1、vs2和向量配置依赖保留，真实的vd=vs1/vs2依赖也保留。常规向量指令译码、算术通路、流水级数、异常和NEMU语义不变。

原实现的通用派发/发射逻辑可能在ta或vlmax条件成立时动态消除旧vd，但在本项目vl=8、VLEN128、SEW8的tu情况下仍可能保留。实验对照必须同时报告ta、tu、真依赖与独立操作，不能用一种配置的结果代表全部情况。

## 运行与证据

先保存原始emu、正常参考库、原补丁和源码绑定，然后构建新工作负载。在同一旧emu上取得before，之后从新Chisel源码重新生成RTL并构建after。两次运行使用完全相同的工作负载、flash、参考库和内存容量。新emu必须有独立构建身份；原始日志不修改，不把旧emu的运行当作新微架构结果。

```bash
bash scripts/build_workloads.sh benchmark_rvv dot_memory
VDOT_EMU_PATH=/absolute/path/to/preserved/emu \
  VDOT_REF_SO=/absolute/path/to/preserved/reference.so \
  VDOT_MAX_CYCLES=15000000 bash scripts/run_rtl.sh benchmark_rvv
VDOT_EMU_PATH=/absolute/path/to/preserved/emu \
  VDOT_REF_SO=/absolute/path/to/preserved/reference.so \
  VDOT_MAX_CYCLES=15000000 bash scripts/run_rtl.sh dot_memory
```

新emu另运行相同程序，并回归原有vadd、基础、随机、寄存器重叠、流水、故障差分与性能探针。`scripts/optimization_report.py`只接受真实差分完成日志，要求样本集合完整、各次输入摘要一致、内存结果校验值一致，并保留CSV。没有实测到提升就如实报告；周期变化不能推断面积、频率或能效。
