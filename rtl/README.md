本文保留原三阶段基线的生成RTL。当前main的共享数据通路和包装器见[当前实际生成RTL](../experiments/acc/generated/README.md)，版本对应见[评审入口](../docs/评审入口.md)。

# 本次完整构建生成的RTL模块

这两个SystemVerilog文件直接复制自独立检出的完整扩展核构建，未手工修改。provenance.json记录构建源码、上游版本、FIR与补丁摘要，以及每个模块的SHA256。实际验收结果由docs/FINAL_RESULTS.md（完整验收通过后生成）和发布包source-binding.json关联，模块文件存在本身不代表测试通过。

VdotDatapath.sv是新增的两级8路有符号点积算术模块。VIMacU.sv是实际接入的向量乘法包装器，依赖固定平台中其它生成模块，不能仅凭这两个文件独立仿真整核。权威修改源为patches/xiangshan.patch及其中的Chisel源码；完整平台RTL使用scripts/build_emu.sh重新生成。

源码和依赖许可见根目录LICENSE与NOTICE.md；保留生成器原始文件头。生成文件用于检查实际结构，不替代时序、综合、面积或功耗报告。

本轮provenance.json已更新为2026-11-06新独立构建的真实来源，构建源码4e5cfce，完成报告为reports/completed-build-20261106。两个导出模块与该次完整构建逐字节一致，也与优化前算术模块一致。直接比较独立生成的前后1868个SV模块，只有DecodeUnit改变；完整回归和540条性能对照见docs/OPTIMIZATION_RESULTS.md。旧导出来源由原发布归档与Git历史保留。
