# 两级与四级算术模块对照

本目录是独立算术实验，正式香山补丁、功能单元延迟与指令语义均保持原值。

| 文件 | 用途 |
|---|---|
| PpaTop2.sv | 将正式生成的VdotDatapath两个使能绑定到公共enable |
| VdotPipelined4.sv | 乘法、两两和、四项和、总和四级原型 |
| PpaTop4.sv | 与两级对象一致的外部综合接口 |
| PpaVerify.sv | 同时实例化两个对象供功能比较 |
| verify.cpp | 完整128位黄金比较、不同流水延迟与公共使能停顿检查 |

从工程根目录运行，下面工具和库参数替换为本机实际路径：

```sh
python3 scripts/evaluate_datapath_ppa.py \
  --yosys /path/to/yosys \
  --abc /path/to/yosys-abc \
  --sta /path/to/sta \
  --verilator /path/to/verilator \
  --liberty /path/to/NangateOpenCellLibrary_typical.lib
```

脚本要求库的时间单位、标称电压/温度及默认wire-load模型与固定Nangate45 typical版本相符。记录的版本、来源、摘要与结果见[数据索引](../../docs/data/ppa/README.md)，约束及解释见[资源与时序评估](../../docs/资源与时序评估.md)。

输出目录为reports/ppa-*/evidence，保存工具版本、原始命令与退出码、输入副本、库推导、映射网表、约束、综合/STA日志和SHA256SUMS。输入库及零互连派生副本应与[许可证](../../docs/data/ppa/OpenCellLibraryLicenseSi2.txt)一同分发。两对象均为单一公共使能的算术模型；四级原型没有实现整核有效位、ROB和冲刷接入。
