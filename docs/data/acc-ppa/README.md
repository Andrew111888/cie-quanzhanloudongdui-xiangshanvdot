# 累加融合模块资源与时序数据

[汇总CSV](summary.csv)、[完整结果](results.json)、[黄金验证](verification.json)、[原始验证日志](verification.log)、[工具版本](toolchain.json)、[库推导](library-derivation.json)、[完整原始证据清单](evidence-manifest.json)。

同一轮对照原始点积、实际Chisel平衡树累加、CSA、前缀及重定时模块。每个设计仅映射一次，ABC目标1000 ps；各自同一网表分别用1/1.5/2.5 ns约束检查。实际生成模块在inputs目录，公共架构见[累加融合架构](../../累加融合架构.md)。

压缩重定时版面积5608.344、159个触发器；1.5 ns建立裕量+0.100698 ns，1 ns仍未通过。此为无布局布线的模块结果。10种独立原型/实际模块各检查8217拍完整128位黄金结果，均通过。

[整核实际模块的结果](full-core/results.json)、[汇总](full-core/summary.csv)、[完整证据清单](full-core/evidence-manifest.json)另行绑定firtool优化后的SV，面积5519.500、1.5 ns建立裕量+0.136429 ns；同样完成8217拍完整黄金检查。前述五对象表是单元测试生成形式的同轮结构对照，整核输出与其分别保存，不混用文件身份。

库及派生副本保留[许可证](OpenCellLibraryLicenseSi2.txt)。完整库、网表、约束、工具命令与原始日志在清单指定的本机目录；不包含工具二进制。
