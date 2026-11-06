# 边界RTL故障变异数据

[结果](results.json)、[汇总CSV](summary.csv)、[原始命令](evidence/commands.json)、[工具版本](evidence/tools.json)。

正常与恢复的两次运行各验证6项定向输入、1000组固定种子随机输入及1006拍独立流水使能压力。三类变异都在RTL副本中注入，模型成功编译后由完整128位结果断言以退出42检测。正常和恢复退出0。各变异差分、RTL副本、运行与构建日志及资源计量保存在evidence目录，直接输入快照保存在inputs目录。

[验证正文](../../边界故障变异验证.md)、[复现脚本](../../../scripts/run_boundary_mutations.py)、[软件黄金模型及流水记分板](../../../verification/boundary_mutations.cpp)。本目录不包含构建临时对象或可执行文件。
