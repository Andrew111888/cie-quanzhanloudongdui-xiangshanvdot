# 访存瓶颈对照数据

[40条正式样本](samples.csv)、[中位数与范围](summary.csv)、[完整结果](results.json)、[循环指令审计](loop-audit.json)、[加载波形统计](wave-summary.json)。

正式计时使用干净提交模型，128块、每组预热一次后重复5次，关闭波形导出。加载波形另用16块、每组预热及执行一次，关联512条已提交向量加载。

[实验程序](../../../examples/dot_memory_diagnostic.c)、[运行入口](../../../scripts/run_memory_diagnostic.py)、[波形提取](../../../scripts/extract_memory_wave.py)、[分析正文](../../访存瓶颈分析.md)。原有540条对照保持不变。
