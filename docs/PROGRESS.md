# 开发进度（2026-11-04）

阶段一、二、三尚未全部通过；按用户要求，未向比赛提交作品，GitHub 作品仓库仍为空。已有本地开发提交，最终验收证据仍需绑定最终源码。

## 当前有效结果

- Python 参考模型测试：3 项通过。
- 独立 Chisel/Verilator 数据通路：6 组定向、1000 组随机输入全部入流水并比较；另有1006周期独立阶段使能压力，`reports/datapath-current.log` 显示通过。
- NEMU 独立运行：`reports/nemu-functional-current.log` 显示6组定向、1000组随机输入，5种计算/基线模式和7种非法形式通过。不能替代整核差分。
- NEMU 参考库已通过 `build_nemu.sh reference` 重建并保存在 `build/nemu/reference/`。配置、autoconf.h 和 auto.conf 的内存大小均为128MB；库 SHA256 为 `6f258e9dd5061bd0058f9404dfa97881042232f2ceb8658392f818741c0bad91`。
- Difftest 静态审计：ARCHVECREGSTATE 与 VECCSRSTATE 开关及 memcmp 启用；双方状态大小1400字节，布局匹配。实际比较仍需整核正例和故障注入验证。

## 当前阻断及下一步

全核构建尚未生成可运行 emu。普通4–4.5GB Java堆不足，精简缓存/软PTW实验另有兼容性问题，实验代码已撤回。正式实现只保留 vdot 修改。

文件映射堆的小规模验证通过：384MiB进程组内存上限下校验512MiB存活数据，见 `reports/heap-probe.log`。8GB文件映射堆生成了 `third_party/XiangShan/build/rtl/SimTop.fir`（930730759字节），随后原联合生成进程组在4800MiB限制处被OOM终止，见 `reports/vdot-build-20261104T145544Z-3252404/`。

独立 firtool 1.62.1 已成功编译该FIR文件，耗时5分46秒、最大RSS 5359524KiB（scope上限从4800MiB调到5500MiB），日志 `reports/firtool-standalone.log`。已生成 SystemVerilog、SRAM模型并完成与 Makefile 等价的仿真断言后处理。

Verilator 带FST生成模型在5200MiB内存限制下失败，普通分配器和jemalloc均被OOM终止；限制追踪深度12层及生成优化O1后普通分配仍超过上限。原生文件映射堆探测在384MiB限制下校验512MiB数据通过。16GiB文件映射池的首次尝试因I/O缓慢被主动停止，不能计为通过。

当前会话88656、scope `vdot-emu-fileheap-opt1.scope` 使用32GiB文件映射池、5500MiB进程组上限、追踪深度12、生成优化O1生成Verilator模型，日志 `reports/emu-fileheap-opt1.log`，参数 `reports/emu-fileheap-opt1-parameters.txt`，源码摘要 `reports/emu-fileheap-opt1-source.json`。不要与旧尝试的成功/失败混淆，当前仍未得到 emu。

`scripts/build_emu.sh` 已改为独立 CHIRRTL → firtool → 模型构建的流程，避免Java与原生编译器同时占内存；`--target chirrtl` 已由固定生成器help确认，脚本尚未全程跑通。最终复现还需验证辅助产物及完整构建流程。

下一步顺序：可运行 emu → vadd与vdot_smoke整核 → 短窗口波形 → vdot_test完整差分 → 临时错误NEMU库证明向量mismatch → 恢复并回归 → RTL性能测量。计划中的步骤不得标为完成。

运行入口 `bash scripts/run_rtl.sh vadd_test|vdot_smoke|vdot_test|benchmark` 默认启用真实差分、128MB仿真内存，保存命令与二进制校验值；波形准备见 `docs/WAVEFORM_PLAN.md`。性能基线已消除结果寄存器搬移，依赖/无显式结果依赖分别与vdot使用相同v8/v12和存储位置；新 `reports/nemu-benchmark-current.log` 仅证明功能通过，不是RTL性能。

## 仓库与提交准备

工作目录 `/home/yh/cie/vdot-kmhv2`；作品仓库为 `Andrew111888/cie2026-quanzhan-loudong-dui-xiangshan-vdot`，Fork为 `Andrew111888/XiangShanLab`。官网本赛题已报名成功，当前团队有两人。没有创建参赛PR。联系信息仍为模板，真实信息不放入公开仓库。

官方11月8日是赛道页列出的报名截止日期，作品接收的确切截止时刻仍待核实；项目内部目标仍为11月8日18:00。指令的结果位宽、支持域和编码等解释尚未得到赛题方确认。
