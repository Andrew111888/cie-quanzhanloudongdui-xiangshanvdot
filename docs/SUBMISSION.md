# 赛题提交内容索引

全栈漏洞队 · 西安电子科技大学

| 编号 | 内容 | 文档或代码 |
|---|---|---|
| 1.1 | 环境验证：问候、队名及IP输出 | [一阶段执行记录](submission/stage1.md)、[向量加法程序](../workloads/vadd_test.c) |
| 1.2 | 环境部署和操作日志 | [环境准备](BOOTSTRAP.md)、[构建说明](BUILDING.md)、[原始部署记录索引](CLEAN_REPRODUCTION.md) |
| 1.3 | 向量加法的执行过程 | [一阶段过程文档](submission/stage1.md) |
| 2.1 | 指令语义、微架构和数据通路 | [设计说明](DESIGN.md)、[二阶段设计与测试](submission/stage2.md) |
| 2.2 | Chisel/RTL实现 | [香山补丁](../patches/xiangshan.patch)、[完整修改文件](../experiments/acc/generated/README.md)、[生成RTL](../rtl/README.md) |
| 2.3.1 | 正数点积测试 | [六项基础测试程序](../examples/vdot_basic.c)、[二阶段测试](submission/stage2.md)、[实际运行](data/basic-current/README.md) |
| 2.3.2 | 含负数的点积测试 | [六项基础测试程序](../examples/vdot_basic.c)、[二阶段测试](submission/stage2.md)、[实际运行](data/basic-current/README.md) |
| 2.3.3 | 最大值、最小值、零等边界 | [六项基础测试程序](../examples/vdot_basic.c)、[整核随机回归](data/acc-results/validation/results.json) |
| 3.1.1 | NEMU指令扩展 | [NEMU补丁](../patches/nemu.patch)、[三阶段协同仿真](submission/stage3.md) |
| 3.1.2 | RTL/NEMU协同仿真 | [功能回归](data/acc-results/validation/results.json)、[故障检出与恢复](data/acc-results/fault/results.json)、[异常优先级](data/acc-results/precedence/results.json) |
| 3.2 | 现有RVV指令组成的等价基线 | [基准程序](../examples/acc_benchmark.c)、[测量方法](累加融合性能方法.md) |
| 3.3 | 延迟和性能分析 | [三阶段性能分析](submission/stage3.md)、[完整实验报告](累加融合实验结果.md)、[逐次数据](data/acc-results/README.md) |

## 文件说明

`patches/`保存相对固定上游的完整改动。`rtl/`保存当前生成模块，`rtl/baseline/`保存原平衡树实现供资源对照。各次实验的原始记录保留自身的源码摘要；旧FST的分析对象为原点积模型。

## 录屏

[三阶段录屏指南](RECORDING_GUIDE.md)列出环境操作、设计讲解、波形与性能分析的命令和讲解顺序。
