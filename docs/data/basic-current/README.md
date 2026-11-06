# 当前实现的六项基础测试

使用当前共享点积/累加模型及修正后的NEMU参考库，执行vdot_basic.c。六项完整128位结果均通过RTL/NEMU差分，运行报告dirty: 0、GOOD TRAP、退出0。

[逐例结果](cases.json)、[原始日志](run.log)、[命令](command.txt)、[输入摘要](artifacts.sha256)。该运行复用已完成构建的模型，源码、模型与测试输入分别记录。
