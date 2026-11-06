# 验证状态

| 检查 | 已完成内容 | 记录 |
|---|---|---|
| 整核构建 | 两级共享点积/累加路径，干净源码构建 | [生成RTL来源](../rtl/provenance.json) |
| 普通点积与累加 | 1000组唯一随机、6组定向、6种关系、TA/TU | [功能回归](data/acc-results/validation/results.json) |
| 流水 | 1664条累加、独立目的、生产者、别名和分支 | [流水记录](data/acc-results/pipeline/results.json) |
| 寄存器边界 | v0/v31及源目标重叠 | [寄存器记录](data/acc-results/registers/results.json) |
| 交叉异常 | 48例，修正前20例mtval错误，修正后通过 | [异常记录](data/acc-results/precedence/results.json) |
| 差分有效性 | 正确、错误、恢复参考库退出0/1/0 | [故障检查](data/acc-results/fault/results.json) |
| 性能 | 60条长点积、120条累加链样本 | [逐次数据](data/acc-results/README.md) |
| 资源与时序 | 实际生成模块黄金验证及同约束映射/STA | [模块记录](data/acc-ppa/full-core/results.json) |

当前源码和数据一致性可用`python3 scripts/check_repository.py`复核。环境与向量加法的原始部署、FST分析见[第一阶段](submission/stage1.md)。
