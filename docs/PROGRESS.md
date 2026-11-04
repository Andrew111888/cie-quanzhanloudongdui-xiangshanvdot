# 开发进度

阶段一、二、三尚未全部通过；按用户要求，未向比赛提交作品，GitHub 作品仓库仍为空。已有本地开发提交，最终验收证据仍需绑定最终源码。

## 当前有效结果

- Python 参考模型测试：3 项通过。
- 独立 Chisel/Verilator 数据通路：6 组定向、1000 组随机输入全部入流水并比较；另有1006周期独立阶段使能压力，`reports/datapath-current.log` 显示通过。
- NEMU 独立运行：`reports/nemu-functional-current.log` 显示6组定向、1000组随机输入，5种计算/基线模式和7种非法形式通过。不能替代整核差分。
- NEMU 参考库已通过 `build_nemu.sh reference` 重建并保存在 `build/nemu/reference/`。配置、autoconf.h 和 auto.conf 的内存大小均为128MB；库 SHA256 为 `6f258e9dd5061bd0058f9404dfa97881042232f2ceb8658392f818741c0bad91`。
- Difftest 静态审计：ARCHVECREGSTATE 与 VECCSRSTATE 开关及 memcmp 启用；双方状态大小1400字节，布局匹配。实际比较仍需整核正例和故障注入验证。
- 本轮通过修正后的完整Kconfig同步流程重建NEMU独立运行程序，`reports/software-validation-current/` 中的vadd、vdot、benchmark及latency_probe四项均通过，并保存源码清单和二进制摘要。
- 新增`latency_probe`，为基线乘法/归约和vdot设置明确PC符号，两条路径的完整128位结果一致；目前只有NEMU功能结果，实际周期待整核波形。
- 错误参考库在独立NEMU副本中生成，正常源码和正常库未改变；现存错误库为`build/nemu/fault-reference/nemu-OnIFEj/riscv64-nemu-interpreter-so`，SHA256为`4b776b8eb02efaaff03dcd5ee861fe4844484082c85d2717625ae3d1f38364c4`。
- 已通过真实Difftest ABI在独立进程中分别加载正确/错误参考库，执行一条vdot，观察到低64位8/9、高64位0、vstart=0、PC推进4字节；见`reports/reference-abi-good.log`、`reports/reference-abi-fault.log`。这不含RTL，不能记为协同仿真或向量比较器故障注入通过。
- 原始基准源码补丁可在临时干净目录重放，得到的4个香山文件、3个NEMU文件与当前实现逐字节一致；见`reports/patch-replay.json`。不能替代完整干净构建。

## 当前阻断及下一步

### 2026-11-05 凌晨：模型已生成，正在修复C++构建兼容性

`vdot-model-20261104T155853Z-3297719.service`在48分32秒后完成Verilator模型生成并进入C++编译，随后因默认`-fno-slp-vectorize`不被GCC识别而退出2。此前“没有C++模型”的状态已被后续事实更新。该次最大RSS为4694396KiB，资源日志`reports/model-resume-20261104T155853Z-3297719/time.txt`；不能把整个make退出2误判为模型生成失败或OOM。

已将构建固定为系统GCC/G++，使用`-O2 -fno-tree-slp-vectorize`。后续编译成功产出42个对象文件，又在`emu.o`遇到Difftest较新的`VerilatedTraceBaseC`类型与Verilator5.022不兼容。最小失败目标见`reports/trace-api-red.log`；项目内新增版本限定的类型别名头`configs/verilator_5_022_trace.h`，预包含后同一`emu.o`目标实际编译通过，见`reports/trace-api-fixed.log`。没有修改Difftest源码、比较器或跳过逻辑。

随后在`VSimTop.o`暴露全局预包含对GCC预编译头的干扰，见`reports/model-resume-20261104T165430Z-3341330/build.log`。全局纯宏/`-imacros`候选在小例与真实目标中仍未通过，未作为最终方案。最终采用`configs/verilator_5_022.mk`：仅对emu.o/main.o/verilator.o/waveform.o添加兼容头，模型对象保持原PCH规则；实际`VSimTop.o`、`emu.o`、`waveform.o`、`verilator.o`四个目标均编译通过，见`reports/trace-pch-targeted.log`。失败候选及旧PCH保存在本机开发产物中。

当前继续复用已生成模型的C++构建服务为`vdot-model-20261104T170533Z-3349034.service`，报告`reports/model-resume-20261104T170533Z-3349034/`。按单任务实测峰值约1.5GB将C++编译改为两任务，总进程组上限仍为5500MiB；最新完整构建检查已超过百个对象文件，暂无新错误。新验证队列为`vdot-validate-20261104T170620Z-3351242.service`，报告`reports/rtl-queue-20261104T170620Z-3351242/`。旧队列随对应构建失败停止，不能记为测试通过。最终emu仍需链接及实际运行验证。

另发现旧wrapper的`-O3 -O1`参数在5.022中仍保留最大内联。小层级RTL实测中，该参数组合内联33个实例；显式追加`--inline-mult 2000`后为1个，两个生成命令均退出0。wrapper已明确设置该值，避免以后重构建继续遗留最大内联；**当前复用的整核模型是在修正前生成的，不能把小例收益写成整核实测收益**。分配器禁purge小探测未显示收益，未应用到真实模型。主来源研究见`docs/LOWMEM_OPTIONS.md`。

以下保留早先构建经过，用于排查历史；以本小节及最新运行报告判定当前状态。

全核构建尚未生成可运行 emu。普通4–4.5GB Java堆不足，精简缓存/软PTW实验另有兼容性问题，实验代码已撤回。正式实现只保留 vdot 修改。

文件映射堆的小规模验证通过：384MiB进程组内存上限下校验512MiB存活数据，见 `reports/heap-probe.log`。8GB文件映射堆生成了 `third_party/XiangShan/build/rtl/SimTop.fir`（930730759字节），随后原联合生成进程组在4800MiB限制处被OOM终止，见 `reports/vdot-build-20261104T145544Z-3252404/`。

独立 firtool 1.62.1 已成功编译该FIR文件，耗时5分46秒、最大RSS 5359524KiB（scope上限从4800MiB调到5500MiB），日志 `reports/firtool-standalone.log`。已生成 SystemVerilog、SRAM模型并完成与 Makefile 等价的仿真断言后处理。

Verilator 带FST生成模型在5200MiB内存限制下失败，普通分配器和jemalloc均被OOM终止；限制追踪深度12层及生成优化O1后普通分配仍超过上限。原生文件映射堆探测在384MiB限制下校验512MiB数据通过。16GiB文件映射池的首次尝试因I/O缓慢被主动停止，不能计为通过。

会话88656对应的`vdot-emu-fileheap-opt1.scope`已在8分48秒后结束，未留下模型或完整time退出记录，不能标为成功，也没有证据将它归因为一次新的OOM。其日志为`reports/emu-fileheap-opt1.log`。

当前使用独立用户服务`vdot-model-20261104T155853Z-3297719.service`恢复相同模型生成参数：32GiB文件映射池、5500MiB上限、追踪深度12、生成优化O1。报告目录为`reports/model-resume-20261104T155853Z-3297719/`，含生成输入摘要、命令和日志。服务不依赖聊天终端连接。最近检查仍在生成模型，尚无emu；构建成功需要退出码0、MODEL_BUILD_COMPLETE及二进制校验值三项证据。

已排队独立验证服务`vdot-validate-20261104T161804Z-3317880.service`，报告目录`reports/rtl-queue-20261104T161804Z-3317880/`。它等待上述特定构建成功并校验产物后，依次运行vadd、vdot smoke、正确/错误/恢复参考库检查、随机差分、latency_probe、benchmark及初始vadd波形。任何失败立即停止并保留当前步骤；排队不是通过。即使自动运行全部成功，实际波形分析、核心延迟解释、干净复现和提交材料仍须完成。首个排队服务在开发时主动停止并替换，不作为验收结果。

`scripts/build_emu.sh` 已改为独立 CHIRRTL → firtool → 模型构建的流程，避免Java与原生编译器同时占内存；`--target chirrtl` 已由固定生成器help确认，脚本尚未全程跑通。最终复现还需验证辅助产物及完整构建流程。

下一步顺序：可运行 emu → vadd与vdot_smoke整核 → 短窗口波形 → vdot_test完整差分 → 临时错误NEMU库证明向量mismatch → 恢复并回归 → RTL性能测量。计划中的步骤不得标为完成。

运行入口 `bash scripts/run_rtl.sh vadd_test|vdot_smoke|vdot_test|benchmark` 默认启用真实差分、128MB仿真内存，保存命令与二进制校验值；波形准备见 `docs/WAVEFORM_PLAN.md`。性能基线已消除结果寄存器搬移，依赖/无显式结果依赖分别与vdot使用相同v8/v12和存储位置；新 `reports/nemu-benchmark-current.log` 仅证明功能通过，不是RTL性能。

## 仓库与提交准备

已通过浏览器逐一展开赛题详情、参赛项目提交内容、建议领域、评审规则，并核对官方GitHub指南、脚本和官网PDF；见`docs/REQUIREMENTS_AUDIT.md`。官网附件与用户PDF的二进制SHA不同，但7页完整提取文本一致。三组文档、三段不同用途录屏、代码链接与双入口提交的缺口见`docs/DELIVERY_CHECKLIST.md`。评分为完整性60、可行性20、探索性10、创新性10；设计中已增加实际流水/数据通路取舍和SEW/VLEN扩展边界说明，未声称实现额外精度或面积/能效收益。

工作目录 `/home/yh/cie/vdot-kmhv2`；作品仓库为 `Andrew111888/cie2026-quanzhan-loudong-dui-xiangshan-vdot`，Fork为 `Andrew111888/XiangShanLab`。官网本赛题已报名成功，当前团队有两人。没有创建参赛PR。联系信息仍为模板，真实信息不放入公开仓库。

官方11月8日是赛道页列出的报名截止日期，作品接收的确切截止时刻仍待核实；项目内部目标仍为11月8日18:00。指令的结果位宽、支持域和编码等解释尚未得到赛题方确认。
