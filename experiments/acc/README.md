# 两级融合累加算术实验

本目录对照原始8项点积与显式32位累加的算术实现。实验输入acc为32位，调用端选择零或旧目标低32位；输出低32位为模2^32结果，高96位清零。所有候选均使用独立enable1/enable2，算术延迟两级、连续接收间隔一拍。

| 文件 | 结构 |
|---|---|
| VdotAccPlain.sv | 第一级寄存8个16位乘积与acc，第二级19位平衡归约后串32位累加 |
| VdotAccCsa.sv | 相同第一级，第二级将9项压缩到2项，再作普通32位加法 |
| VdotAccCsaPrefix.sv | CSA结构，最终加法为XOR传播的32位并行前缀 |
| VdotAccCsaPrefixOr.sv | OR传播的前缀进位实验，最终和仍使用两操作数异或 |
| VdotAccRetimed.sv | 第一级完成组合乘法和首层3:2压缩、寄存6项；第二级继续压缩并作XOR前缀加法 |
| AccVerify.sv | 同时实例化原始模块、候选及可选的真实Chisel生成模块 |

## 功能验证

[C++黄金检查](../../verification/acc_arithmetic.cpp)独立逐字节解释有符号int8，以软件整数循环计算8项和，再用uint32_t完成模2^32累加。12项定向包含基础正负/极值、非零累加器和正负溢出；另有4096组固定种子随机输入。

每个模型连续检查4108组结果，再执行独立使能压力与排空，总计检查8217拍完整128位结果；覆盖1413拍第一级保持和848拍结果级保持。测试比较正常原始点积的acc=0语义，并逐项检查所有累加候选。该验证覆盖数据通路寄存更新，不替代整核有效位、ROB、冲刷或NEMU差分。

## 同约束综合与STA

[运行脚本](../../scripts/evaluate_acc_ppa.py)对每个对象只进行一次ABC映射，目标固定为1000ps；1.0、1.5、2.5ns三个STA时钟均使用该同一映射网表。库为固定Nangate45 typical、1.10V、25°C；输入/输出延迟100ps，时钟不确定度20ps，输入转换50ps，输出负载5fF，理想时钟和零互连模型。原始库、仅替换wire-load的派生库及许可证均随证据保存。

面积为Liberty area属性单位，不换算为物理µm²。所有数据仅描述隔离算术模块，不包含指令选择、发射、读写端口或全核物理实现，不能据此宣称芯片频率或功耗。

同轮单元生成形式的比较中，平衡树串累加、CSA、前缀和提前压缩版的面积分别为5431.188、5733.896、5830.188、5608.344；1.5 ns建立裕量分别为-0.561671、-0.220036、-0.055645、+0.100698 ns。[同轮数据](../../docs/data/acc-ppa/results.json)

整核实际生成的提前压缩模块另行验证：面积5519.500、159个触发器，1/1.5/2.5 ns建立裕量为-0.363571/+0.136429/+1.136429 ns。其输入SV及黄金验证见[整核实际模块数据](../../docs/data/acc-ppa/full-core/results.json)。

## 运行方式

从工程根目录运行，工具和库路径替换为本机实际路径：

```sh
python3 scripts/evaluate_acc_ppa.py \
  --yosys /path/to/yosys \
  --abc /path/to/yosys-abc \
  --sta /path/to/sta \
  --verilator /path/to/verilator \
  --liberty /path/to/NangateOpenCellLibrary_typical.lib
```

若已运行Chisel数据通路测试，可追加--chisel-plain、--chisel-csa、--chisel-prefix及--chisel-retimed，分别传入对应VdotAcc*Datapath.sv；脚本将其纳入同一黄金检查和同约束映射。--designs可选择需映射的对象，支持original、plain、csa、prefix、prefix_or、retimed及相应chisel_*名称。选择映射对象不会跳过黄金检查。

输出reports/acc-ppa-*/evidence包含输入副本、命令、工具摘要、库推导、原始编译/运行退出码、网表、综合/STA日志、结果JSON、汇总CSV与SHA256SUMS。早期旧OpenSTA无法解析拼接左值的失败记录单独保留；脚本已使用write_verilog -simple-lhs，只有无解析错误的完整轮次才写入passed回执。
