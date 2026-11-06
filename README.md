# 香山昆明湖 V2 vdot 指令项目

2026 CIE 赛题独立工程，队伍：全栈漏洞队。已完成自定义vdot.vv的Chisel/RTL和NEMU扩展；优化版于2026-11-06在新的独立检出中完成整核构建、三阶段内部验收与性能复测。

按赛题1.1至3.3的交付入口见[提交成果索引](docs/SUBMISSION.md)，三份阶段报告源稿分别为[第一阶段](docs/submission/stage1.md)、[第二阶段](docs/submission/stage2.md)、[第三阶段](docs/submission/stage3.md)。另提供[逐例正负数/边界程序](examples/vdot_basic.c)及[真实整核运行入口](scripts/run_basic_validation.sh)。三段官网录屏由参赛者自行完成，操作入口见[录屏指南](docs/RECORDING_GUIDE.md)；本轮不制作PPT，官网材料继续暂停替换。

本轮新增RVV序列对比、含访存内核及旧目标依赖消除，重新构建的全核功能回归和前后540条真实性能样本均已通过。512次TU独立点积的片段周期由3639降至625（改善5.822倍）；TA、真实依赖链和含访存内核未因这次调度修改降低中位周期。候选RVV序列在部分场景更慢，报告以两条实测RVV序列中较快者作为主要基线。详见[方法](docs/OPTIMIZATION.md)、[结果与限制](docs/OPTIMIZATION_RESULTS.md)及[原始数据](docs/data/optimization/README.md)。

赛题：[官方说明](https://rv.cie.org.cn/direction?id=8)。指令结果位宽等赛题未明确事项采用的暂定解释见 [contract.json](contract.json) 和 [待确认问题](docs/QUESTIONS.md)，尚未获得赛题方确认。

固定昆明湖V2单核MinimalConfig，复用现有向量译码、调度、读源、VIMac执行槽位、写回及ROB通路。新增8路有符号8×8乘法与17/18/19位加法树，两级流水；同时交付[生成RTL及来源](rtl/README.md)，不依赖编译器认识新助记符。

本轮正式结果来自[独立检出完整验收](docs/FINAL_RESULTS.md)，包括1000组固定种子输入、4000次合法随机vdot、1000次等价基线、1664条流水压力和v0/v31边界寄存器检查。真实错误参考库能触发v12_low的9/8差异，恢复正确库后通过。实际FST确认vdot输入至结果2周期，以及5组×8条独立指令逐周期握手。

本轮复测的60条基础RTL性能样本中，相对此处公开等价序列的程序片段中位数加速比为2.607–4.634；范围包含必要配置、循环及结果存储，没有测量所有软件组合的最优结果。测量边界、原始CSV与来源摘要见[阶段三报告](docs/results/stage3-clean.md)和[干净数据](docs/data/clean/provenance.json)。没有面积、频率、功耗或端到端LLM实测声明。

`vdot_vstart_probe` 是独立探测程序：它尝试在非零 `vstart` 下执行普通 `vmul`。固定版本NEMU原有实现对此报非法指令；该探测不属于vdot主回归的通过项，也不单独证明规范问题。vdot自身的非零vstart非法行为已由整核差分检查。

全核构建继续采用官方 `MinimalConfig`，通过 `DISABLE_PERF=1 DISABLE_ALWAYSDB=1` 减少仿真统计与数据库逻辑。此前的 `VdotSimConfig` 精简实验还遇到软 PTW 和缓存索引问题，不作为可用配置。

本轮新FST再次核实2周期算术延迟、错路冲刷与独立突发；直接比较独立生成的前后1868个SV模块，只有DecodeUnit改变。报告输出到output/pdf/20261106-optimized，三段录屏输出到output/video/20261106-optimized；生成状态和校验值见各manifest及本机output/delivery-20261106.json。本轮不制作PPT，官网和官方PR仍保留旧提交。

实现说明见 [设计文档](docs/DESIGN.md)，当前工具、构建命令和限制见 [构建与运行记录](docs/BUILDING.md)。

历史未修改原核构建与vadd证据保留在上一轮独立目录；本轮另建目录，从固定源码生成优化版RTL、C++及NEMU并完成完整验收，详见[干净复现记录](docs/CLEAN_REPRODUCTION.md)。复用固定外部工具和下载缓存，未做全新操作系统验证。实际构建提交与最终文档/工具提交在发布包source-binding.json中分别记录，并逐字节核对关键输入。代码与依赖来源见[NOTICE](NOTICE.md)。

从[环境准备](docs/BOOTSTRAP.md)获取固定源码和工具后，运行scripts/build_workloads.sh、scripts/build_nemu.sh、scripts/build_emu.sh，再用scripts/verify_reproduction.sh执行完整验收。具体参数、资源和恢复条件见[构建说明](docs/BUILDING.md)。报告、三段真实录屏和四类ZIP的生成入口见[材料工作流](docs/ARTIFACTS.md)。

官网四栏逐项来源见[要求核对](docs/REQUIREMENTS_AUDIT.md)，阶段材料见[交付清单](docs/DELIVERY_CHECKLIST.md)。[历史发布页](https://github.com/Andrew111888/cie-quanzhanloudongdui-xiangshanvdot/releases/latest)保留旧归档与旧提交回执，本轮本地新稿不据此视为已同步官网；技术验收通过不代表官方评审通过。

`patches/` 保存相对固定上游版本的源代码改动，`workloads/` 是裸机测试与基准程序，`tests/` 是独立语义参考模型。编译工具和上游仓库保存在本地 `tools/` 与 `third_party/`，默认不上传。

提交信息模板见[submission-info.template.txt](docs/submission-info.template.txt)。联系邮箱只保存在本地private/并进入官方公钥加密的信息；原始环境日志及FST保留在官网评审证明材料包，公开源码包含小型CSV与来源摘要。
