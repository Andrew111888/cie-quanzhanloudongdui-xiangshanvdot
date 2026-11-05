# 开发进度

验收日期：2026-11-05。三阶段内部技术验收与独立检出复现均已通过，三段真实录屏完成。本文件记录技术归档状态；GitHub与官网的外部提交回执在作品发布页另行记录，不能将内部验收等同于官方评审通过。本机工程与/home/yh/eda独立。

正式结果入口为FINAL_RESULTS.md、results/stage1-clean.md、results/stage2-clean.md、results/stage3-clean.md及data/clean/provenance.json。实际构建源码为3424efe852a1b4e2b26fa3efc25b233d94aec9a4；最终文档/工具提交由发布包source-binding.json给出。

## 开发期真实结果

| 项目 | 当前状态与实际证据 |
|---|---|
| 全核仿真器 | 已成功生成并运行；reports/model-resume-20261104T170533Z-3349034/，emu SHA256 f94a71643146e20148512c41e74bf01654a9ee45b47d6942d01441b5759c77c6 |
| 标准向量加法 | RTL/NEMU差分通过并完成真实FST分析；reports/rtl-vadd_test-20261105T013458Z-3573289/，见 STAGE1_WAVEFORM.md |
| vdot定向整核 | 6组定向×5模式、7种非法形式及普通非法指令保护检查通过；reports/rtl-vdot_smoke-20261105T012647Z-3563691/，4084指令/12791周期 |
| 向量比较器反例 | 正确/错误/恢复三次真实整核完成；reports/fault-check-20261105T013003Z-3568473/，错误REF产生v12_low的9/8差异并ABORT退出1，恢复后通过 |
| 流水线压力 | 64组突发、1664条vdot、28/36种分支结果，RTL/NEMU及C黄金结果一致；reports/rtl-pipeline_test-20261105T020117Z-3585813/，290027指令/181649周期，退出0 |
| 完整随机差分 | 1000组×5模式通过，含4000次合法随机vdot、1000次等价基线及定向/异常；reports/rtl-vdot_test-20261105T021232Z-3593010/，786591指令/593917周期，原始退出0，输入4项SHA256复核通过 |
| 反压与冲刷波形 | 实测3条错路vdot已物理写回但被较老分支冲刷、未提交；vdot译码621、重命名76个反压接口周期。详见VALIDATION.md的完整边界 |
| 性能片段 | 60样本完整通过；reports/rtl-benchmark-20261105T013446Z-3572189/，各配置中位数加速比2.607–4.634，详见 PERFORMANCE.md |
| 实际算术路径 | latency_probe波形确认vdot输入至结果2周期；此次等价基线含配置/清零/归约调度为16周期，不等同于普遍8倍加速 |
| 独立突发吞吐 | 5组×8条独立vdot均每周期接收一条、两周期后每周期输出一条；逐个核对算术结果、标签和提交，见PERFORMANCE.md |
| 独立算术/模型 | Chisel/Verilator的6定向+1000随机、阶段使能压力通过；Python语义与脚本生命周期回归4项通过 |
| 补丁可重放 | 4个香山文件、5个NEMU文件在原始Git blob上重放后与当前源码一致；reports/patch-replay.json |

正常NEMU参考库SHA256：83fd0337620e0883910b320887c1eb470b18812098259cd2fc498840de5a1e0a。旧日志中的6f258e…是异常xtval对齐前的历史库，不能用于证明当前实现。

## 干净验收与归档材料

1. **干净检出全流程通过。** 原核构建和vadd通过后，从空硬件生成目录重建扩展核；完整验收reports/acceptance-20261105T063406Z-3723760/已结束，status=passed、source_unchanged=true。新emu SHA256为dd1f0323f96d567e26e9ba25336db5f9cbcc3a9ebb55821665110fc993e30e31；正常REF为baa2f11e3190d4dd3e7d6107c46ca6795c9b574978a070fdd7bdfafaf8372225。7项整核功能/性能运行、故障注入恢复、实际FST分析均完成，详见CLEAN_REPRODUCTION.md。
2. **真实录屏与报告来源齐备。** output/video-stage1-reviewed-20261105/、video-stage2-reviewed-20261105/、video-stage3-reviewed-20261105/分别为62.7、101.7、122.7秒，命令退出0、输入摘要和画面已复核。三份正式PDF、四类ZIP与校验清单由ARTIFACTS.md的入口统一生成；归档绑定清单给出最终源码和全部文件摘要，不将开发审阅稿当作正式材料。
3. **明确保留的覆盖边界。** 观察到的是完成FU输出后、等待ROB提交期间被冲刷的vdot；未观察到功能单元输出端反压或redirect恰在两级算术内部的情形，不将这些具体时序计为覆盖。标准完整压力运行通过，28000周期的补充诊断采集故意截断，不作为功能PASS。

首次随机运行因中途编辑脚本而缺少收尾记录，原始失败保留在reports/rtl-vdot_test-20261105T013446Z-3572191/。修复后的重跑已完整通过，见上表；没有补造第一次缺失的exit-status.txt。

## 已解决的真实错误

- 宿主GCC不接受-fno-slp-vectorize：固定GCC并改用-fno-tree-slp-vectorize。
- Verilator5.022缺少新版Difftest引用的trace基类：版本限定兼容头仅用于4个Difftest包装对象；避免全局预包含破坏模型PCH。checker、跳过及同步逻辑未修改。
- 自定义配置异常的mtval：执行单元后期配置非法报告0；非零vstart在译码阶段报告指令位。NEMU使用单次非架构标记区分，普通非法0x7b仍报告0x7b。详见契约v2与DIFFTEST_CHECKS.md。
- 长运行脚本被中途编辑导致收尾语法错误：完整函数解析后执行；并在结束时重验全部输入文件摘要。保留第一次原始失败记录。
- 冷检出启动Mill缺少out锁目录、编译315个依赖源码时384MiB堆不足：启动器主动创建目录，默认2GiB；原失败目标和后续主核源码编译均已通过。

早期开发C++模型在显式--inline-mult 2000修正前生成。本轮原核与扩展核的干净构建均已使用修正参数成功；资源结果见CLEAN_REPRODUCTION.md，未做同条件完整A/B，不声称具体内存收益。不能把小例内联减少写成整核实测收益，详见LOWMEM_OPTIONS.md。开发期48分32秒、最大RSS4694396KiB的生成记录及早先失败均保留为历史。

## 提交边界

三阶段全部通过及干净复现完成后才提交。内部目标2026-11-08 18:00；官网个人中心本赛题预赛实际截止已核实为2026-11-08 23:59:59。材料字段、每类单压缩包500M及每天5次限制见UPLOAD_MANIFEST.md。

低8项/低32位等未明确语义仍为暂定解释。2026-11-05 13:19已在官方Issue #126发送最小支持域、布局、版本与编码问题，链接见QUESTIONS.md；尚无维护者答复。技术测试通过不代表官方已认可该解释。没有综合/时序/功耗证据，不声称面积、频率或能效提升。
