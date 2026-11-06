# 长点积实验数据

[45条正式样本](samples.csv)、[中位数与范围](summary.csv)、[较快RVV基线选择](comparisons.csv)、[完整回执](results.json)、[原始日志](run.log)、[退出码](exit-status.txt)、[汇编审计](assembly-audit.json)、[运行命令](commands.json)。

三条内核、K=32/128/512、每组预热后五次重复，均通过真实RTL/NEMU差分并以GOOD TRAP结束。K32和K512各六类极值在三条实现上通过，共36次定向内核检查。正式模型dirty: 0，关闭波形导出。

[实验程序](../../../examples/long_dot_kernel.c)、[运行脚本](../../../scripts/run_long_dot_kernel.py)、[分析正文](../../长点积内核分析.md)。输入快照、二进制及反汇编保留在inputs与workload。旧探索版本未完成的日志保留在本地reports，不记为通过。
