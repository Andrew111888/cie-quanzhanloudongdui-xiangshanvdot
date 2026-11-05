# 开发证据索引

核对日期：2026-11-05。下列为真实开发运行，尚未作为最终干净复现提交包发布。所有目录相对本机工程根/home/yh/cie/vdot-kmhv2；大体积FST及原始部署输出保留本机，最终按UPLOAD_MANIFEST.md选择并打包。

## 当前有效证据

| 阶段/检查 | 报告目录或文件 | 已核对结果 |
|---|---|---|
| 可运行扩展核 | reports/model-resume-20261104T170533Z-3349034/ | 完成链接、emu摘要及真实运行 |
| vadd环境与波形 | reports/rtl-vadd_test-20261105T013458Z-3573289/ | VADD_PASS、GOOD TRAP、退出0、真实FST |
| vdot基础定向 | reports/rtl-vdot_smoke-20261105T012647Z-3563691/ | 6输入×5模式、7非法形式和普通非法保护，通过 |
| 向量故障注入与恢复 | reports/fault-check-20261105T013003Z-3568473/ | 正确/故障/恢复，精确v12_low的REF9/DUT8及ABORT退出1 |
| 完整随机差分 | reports/rtl-vdot_test-20261105T021232Z-3593010/ | 1000组、4000次合法随机vdot与1000次基线，退出0、输入摘要复核 |
| 完整流水压力 | reports/rtl-pipeline_test-20261105T020117Z-3585813/ | 64组、1664条vdot、两分支路径，退出0 |
| RTL性能 | reports/rtl-benchmark-20261105T013446Z-3572189/ | 60样本、BENCH_PASS、GOOD TRAP、退出0 |
| 算术延迟FST | reports/rtl-latency_probe-20261105T013554Z-3573999/ | vdot两周期，等价基线16周期路径及完整结果 |
| 补充控制FST | reports/rtl-pipeline_test-20261105T023307Z-3609286/ | 3个已写回错路冲刷、5组一条/周期独立突发及前端反压；诊断预算停止，不是功能PASS |
| 波形结构化分析 | reports/wave-analysis-current/、reports/wave-analysis-pipeline-window/verified/ | JSON/CSV按PC、ROB动态区间和P核对 |
| 原始补丁重放 | reports/patch-replay.json | 4个香山文件、5个NEMU文件逐字节匹配 |
| 长运行脚本回归 | reports/runner-original-red.log、tests/test_runner.py | 旧版复现错位语法错误，修复版通过 |
| 冷编译恢复门禁 | reports/resume-guard-negative.log | 错误FIR摘要被拒绝，未进入firtool |

正常emu和REF的SHA256、差分负例身份、所有完成判据见DIFFTEST_CHECKS.md。每次RTL目录至少包含command.txt、source.json、artifacts.sha256、run.log、time.txt和exit-status.txt；新驱动另有artifacts-after.txt。

## 可随源码分发的小型数据

data/development-20261105-manifest.json记录CSV自身与来源日志/FST的SHA256：

- benchmark-development-20261105.csv：全部60条周期样本。
- wave-events-development-20261105.csv：vadd、乘法、归约及vdot的身份与握手事件。
- flush-events-development-20261105.csv：3个实际错路冲刷例子的事件。
- burst-throughput-development-20261105.csv：5组独立突发中40条指令的输入、输出、提交和结果。

这些副本用于复核报告计算，保留来源绑定，不把CSV或示意图冒充原始连续波形。原始FST的选中信号和采样方式由extract_wave_events.py生成的metadata.json/signals.json记录。

## 不能记为最终通过的项目

首次随机运行的DUT本身正确，但驱动收尾退出2，其目录reports/rtl-vdot_test-20261105T013446Z-3572191/保留原样。后来的完整重跑才是有效验收；没有补造缺失退出文件。旧参考库及更早失败构建也只作为诊断历史。

独立干净检出位于/home/yh/cie/vdot-kmhv2-repro-20261105。未修改原核已完成全量构建和真实vadd；扩展核复现及正式交付的最新状态见CLEAN_REPRODUCTION.md和PROGRESS.md，不能以这里的开发日志替代最终验收。
