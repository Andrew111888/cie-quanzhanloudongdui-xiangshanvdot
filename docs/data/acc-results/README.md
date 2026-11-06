# 累加融合整核实验数据

[实验报告](../../累加融合实验结果.md)、[复现入口](../../累加融合复现.md)。

validation保存22318次功能执行，包含1000组唯一随机输入；benchmark保存60条长点积及120条累加链样本，pipeline保存1664条流水测试，registers保存v0/v31别名，fault保存真实错误参考及恢复。每组均含输入快照、二进制、命令、原始日志与退出码。validation、benchmark、pipeline、registers、fault及precedence保留真实RTL/NEMU差分；corrected-reference-legal仅为修正库的NEMU独立回归，不能替代整核差分。

[长点积逐次样本](benchmark/long-samples.csv)、[链逐次样本](benchmark/chain-samples.csv)、[完整性能结果](benchmark/results.json)、[功能结果](validation/results.json)、[流水结果](pipeline/results.json)、[边界寄存器](registers/results.json)、[错误与恢复](fault/results.json)。

[异常优先级差分](precedence/results.json)、[修正库NEMU独立回归](corrected-reference-legal/results.json)。
