# 生成RTL

| 文件 | 用途 |
|---|---|
| VdotAccRetimedDatapath.sv | 当前两级点积/累加共享算术模块 |
| VIMacU.sv | 同次整核生成的向量乘法执行单元包装器 |
| provenance.json | 上述模块、补丁和实际构建的摘要 |
| baseline/ | 原两级平衡归约实现，仅用于结构、资源和历史波形对照 |

当前两个模块逐字节复制自已完成的整核构建。普通vdot选择累加输入0，累加变体选择旧目标低32位；两条指令共用此模块。源代码见[香山补丁](../patches/xiangshan.patch)和[完整修改文件](../experiments/acc/generated/README.md)。

VIMacU依赖固定平台的其他向量模块，整核生成与编译入口见[构建说明](../docs/BUILDING.md)。原始生成文件头及上游许可证保留。
