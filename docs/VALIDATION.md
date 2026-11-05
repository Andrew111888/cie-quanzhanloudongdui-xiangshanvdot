# 阶段二：功能与流水线验证

本文保留2026-11-05开发期的模型、命令和结果。正式交付使用[干净检出阶段二结果](results/stage2-clean.md)，不将下列历史运行改写为新的验收身份。

## 参考模型与基本输入

独立Python模型按字节解包并作有符号乘法求和；裸机C模型独立读取输入数组，以int32_t累加；NEMU独立执行指令；DUT为真实香山RTL。四者不共享计算结果。

| 前8项输入A/B | 普通模式结果（有符号） | 低32位补码 | 用途 |
|---|---:|---|---|
| 1 / 1 | 8 | 0x00000008 | 正数 |
| -1 / 1 | -8 | 0xfffffff8 | 负数、符号扩展 |
| -128 / -128 | 131072 | 0x00020000 | 正边界、避免16位累加溢出 |
| -128 / 127 | -130048 | 0xfffe0400 | 负边界 |
| 127 / 127 | 129032 | 0x0001f808 | 正上界输入 |
| 0 / -128 | 0 | 0x00000000 | 零乘积 |

全部检查高96位为零。源寄存器完整128位初始化，计算仅取低64位；目标旧值置全1，防止误将未写位当作正确清零。每组输入的5种模式为独立目标、vd=vs1、vd=vs2、两源相同，以及已有向量指令的等价基线；前4种执行vdot。两源相同模式的黄金值使用A·A，不能套用表内A·B。

定向整核证据：`reports/rtl-vdot_smoke-20261105T012647Z-3563691/`，完整完成标记、Difftest启用、GOOD TRAP，原始退出0。检查结果在C程序中逐个断言，任一低位或高位不符都会非零返回并BAD TRAP；不能只根据首个正数8判断全部通过。

## 非法形式及异常保持

7种形式分别是SEW16、LMUL2、VL7、VL0、vstart1、LMUL1/2、vm0。每次预置整个目标128位，要求cause=2、目标不变、vstart不被清零，并检查契约v2的mtval：vstart1为指令位，其余后期配置检查为0。

随后执行普通非法0x7b，要求mtval仍为0x7b，检验NEMU自定义异常元数据未泄漏到下一条指令。异常处理程序仅在预期非法标志置位时接收cause=2并推进mepc；意外异常直接失败。未单列覆盖所有特权、VS关闭或vill组合。

## 数据通路与随机回归

独立Chisel/Verilator测试覆盖6组定向、1000组固定种子随机输入和独立阶段使能压力，原始日志 `reports/datapath-current.log`。这证明局部算术与阶段数据保持，不能代替整核。

裸机完整回归使用种子20261104生成1000组随机128位输入，各运行5模式，即4000次合法随机vdot与1000次等价基线，另加6组定向和异常检查。首次DUT日志完整通过且模拟器原始退出0，但驱动收尾受文件中途编辑影响退出2；没有补造缺失的exit-status.txt。修复后在 `reports/rtl-vdot_test-20261105T021232Z-3593010/` 完整通过，786591指令、593917周期、GOOD TRAP、Difftest无差异、原始退出0；结束后emu、REF、工作负载、flash四项SHA256均复核为OK。

## 连续发射、依赖与控制压力

`workloads/pipeline_test.c` 使用种子20261105，64组突发，每组包括：8个不同源及不同目的寄存器的独立vdot；vadd产生源后接vdot；16次vd=vs1真依赖链；依赖整数除法结果的分支在v26/v27中选择一个目的，同时检查未选目的保留完整哨兵。每条被选择结果都与C模型比较完整128位。

实测 `PIPELINE_PASS bursts=64 vdot_instructions=1664 taken=28 not_taken=36`，Difftest无差异、GOOD TRAP、原始退出0。证据目录 `reports/rtl-pipeline_test-20261105T020117Z-3585813/`；共290027条指令、181649周期。

上述结果覆盖架构可见的连续、不同标签、源/目的依赖和两个分支路径。另以同一emu、REF、工作负载和flash采集周期14000至27000的诊断窗口，实际观察到3条已经完成写回、随后被较老分支冲刷而未提交的vdot。

诊断目录 `reports/rtl-pipeline_test-20261105T023307Z-3609286/`，FST SHA256为 `3ab7c70e4738d69be3827fd7743b7e685955548f774b07a0a6de635789a01ce6`。该次故意在28000周期停止，正常验收器正确拒绝预算耗尽；它不是完整功能PASS，完整压力PASS仍以上一段64组运行证明。分析程序核对两份证据的4项输入摘要一致。

第一例的实际事件如下。边沿为这份FST窗口内部编号，在后端上升沿前采样；不得与其他窗口的编号直接相加。

| 事件 | 边沿 | 身份与结果 |
|---|---:|---|
| 分支重命名 | 3337 | PC=0x8000031e，ROB=(1,36) |
| 错路vdot重命名 | 3339 | PC=0x80000322，ROB=(1,37)，逻辑v27，P=121 |
| 错路vdot输入 | 3345 | 同ROB/P，Vimac，op=256 |
| 错路结果、写回与物理寄存器写入 | 3347 | 同ROB/P，完整128位0xeb4；此时允许进行投机物理写入 |
| 较老分支redirect | 3383 | ROB=(1,36)，冲刷错路 |
| 正路vdot重命名 | 3393 | PC=0x80000376，ROB=(1,38)，逻辑v26，复用P=121 |
| 正路vdot输入/结果 | 3399/3401 | 同ROB=(1,38)，P=121，结果0xeb4 |
| 分支及正路vdot提交 | 3447 | PC/ROB分别匹配分支与v26写入；错路v27没有提交 |

原ROB槽37随后可被别的指令重新分配，因此“错路未提交”按原PC、ROB及重命名到槽复用的动态区间判断；不声称整个窗口从未出现数字37提交。两条vdot还复用了同一P=121，不能仅用P匹配。完整C测试验证被选择目标正确、另一目标保留哨兵；真实Difftest继续比较全部向量状态。

同一诊断窗口观察到vdot译码入口合计621个valid且非ready的**接口周期**，重命名入口76个，说明确实施加了前端反压；六入口之和不是独立指令数或程序耗时。未观察到Vimac输入/输出端反压，也未观察到redirect恰在vdot两级算术内部的情形，不能声称这两种具体时序已覆盖。独立阶段使能压力只证明数据保持。

```bash
python3 scripts/analyze_pipeline_wave.py \
  --events reports/wave-analysis-pipeline-window/events-stalls \
  --full-run reports/rtl-pipeline_test-20261105T020117Z-3585813 \
  --output reports/wave-analysis-pipeline-window/verified
```

输出JSON/CSV保存3个实际例子及精确握手数据。若没有完整观察到的分支、错路输出、物理写入、redirect、正路重命名与提交，分析程序失败，不能以缺失事件推断冲刷成功。

## 运行与证据

```bash
python3 -m unittest discover -s tests -v
source scripts/env.sh
mill -i -j 1 datapath.test
bash scripts/build_workloads.sh
bash scripts/run_rtl.sh vdot_smoke
bash scripts/run_rtl.sh vdot_test
bash scripts/run_rtl.sh pipeline_test
```

每次RTL目录保存命令、源码摘要、emu/REF/工作负载/flash校验值、实际日志、时间和原始退出码。新驱动在完成后重验输入摘要，拒绝周期预算耗尽、ABORT、关键错误及向量差异。最终提交须以干净复现后的证据集合为准。
