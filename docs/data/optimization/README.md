# 新增实验数据

全部数据来自实际RTL/NEMU差分；每次结果校验通过后才输出样本。before和after使用相同工作负载、参考库与flash，只有仿真器版本不同。before的270条冻结样本保留原来源，after的270条来自2026-11-06新独立构建。本轮完整功能验收使用另行新编译的NEMU，摘要与A/B固定参考库分别记录。

- [完整自动对照表](full-report.md)
- [来源与校验值](provenance.json)
- [after-memory-incremental.csv](after-memory-incremental.csv)
- [after-memory-summary.csv](after-memory-summary.csv)
- [after-memory.csv](after-memory.csv)
- [after-rvv-incremental.csv](after-rvv-incremental.csv)
- [after-rvv-summary.csv](after-rvv-summary.csv)
- [after-rvv.csv](after-rvv.csv)
- [before-memory-incremental.csv](before-memory-incremental.csv)
- [before-memory-summary.csv](before-memory-summary.csv)
- [before-memory.csv](before-memory.csv)
- [before-rvv-incremental.csv](before-rvv-incremental.csv)
- [before-rvv-summary.csv](before-rvv-summary.csv)
- [before-rvv.csv](before-rvv.csv)
- [unchanged-rvv-controls.csv](unchanged-rvv-controls.csv)

原始CSV按before/after与寄存器/含访存区分。summary.csv给出中位、最小、最大周期，incremental.csv给出相邻长度的循环增量周期。两个RVV控制序列共36组前后中位数完全一致。
