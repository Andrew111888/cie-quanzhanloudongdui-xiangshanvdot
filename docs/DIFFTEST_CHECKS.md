# 向量Difftest：静态接口与实际反例

更新时间：2026-11-05。本文件区分已运行证据和仍待完成的验收；未修改Difftest受版本控制的checker、跳过规则或同步策略。

## 当前结果与身份

| 检查 | 结果/本机证据 |
|---|---|
| 标准vadd整核与向量结果 | 通过；reports/rtl-vadd_test-20261105T013458Z-3573289/ |
| 正常REF的vdot smoke | 通过；reports/rtl-vdot_smoke-20261105T012647Z-3563691/ |
| 故意错误REF | 精确向量差异、ABORT、原始退出1；reports/rtl-vdot_smoke-20261105T013039Z-3569060/ |
| 恢复正常REF | 通过；reports/rtl-vdot_smoke-20261105T013044Z-3569524/ |
| 三段反例驱动与输入一致性 | 通过；reports/fault-check-20261105T013003Z-3568473/ |
| 1000组×5模式随机差分 | 修正驱动后完整通过，786591指令/593917周期、原始退出0、4项输入摘要不变；reports/rtl-vdot_test-20261105T021232Z-3593010/ |
| 64组/1664条流水压力 | RTL/NEMU与C黄金模型通过；reports/rtl-pipeline_test-20261105T020117Z-3585813/ |

| 产物 | SHA256 |
|---|---|
| emu | f94a71643146e20148512c41e74bf01654a9ee45b47d6942d01441b5759c77c6 |
| 正常参考库 | 83fd0337620e0883910b320887c1eb470b18812098259cd2fc498840de5a1e0a |
| 故障参考库 | da4891f6e308c1bac15c07b31025805120b071b5bfe23f489103a324f37fade4 |

上游XiangShan=7b16188f7f18a97be69c9b1a2dae8a446eec3b47、Difftest=3729300ae233816d332d057f170472ebe35147b0、NEMU=d772a9d9e06f663d529bd1c6518480c1ee59ded2。每次目录的source.json和artifacts.sha256记录其实际完整输入；HEAD不替代未提交修改的字节摘要。

## 独立执行与比较机制

生成配置启用CONFIG_DIFFTEST_ARCHVECREGSTATE与CONFIG_DIFFTEST_VECCSRSTATE。前者为32个128位向量寄存器，后者为vstart/vxsat/vxrm/vcsr/vl/vtype/vlenb。Difftest refproxy.cpp对完整vrf和vcsr使用memcmp；普通CSR waive不覆盖向量状态。

在未跳过的vdot提交上，参考NEMU独立推进到对应架构状态；Difftest取得参考状态后与DUT提交的架构状态比较。未使用从DUT复制结果、跳过vdot或关闭向量比较的方式取得通过。初始化日志“Difftest enabled.”只能证明初始化，真正的比较能力由以下故障注入证明。

NEMU导出的状态前缀总长1400字节，保持与Difftest一致。新增trapInfo.vdot_config_fault在架构导出前缀之外，不改变regcpy ABI。

| 字段 | 偏移/长度（字节） |
|---|---|
| gpr、fpr | 0/256、256/256 |
| 普通CSR块（含mode） | 512/144 |
| pc | 656/8 |
| HCSR | 664/136 |
| vr[32] | 800/512 |
| 7项向量CSR | 1312/56 |
| fcsr | 1368/8 |
| tselect、tdata1、tinfo | 1376/24 |

## 故障注入实际结果

build_fault_reference.sh复制独立NEMU源码，仅把结果低位异或1。故障库在build/nemu/fault-reference/nemu-ZRGKop/；live NEMU及正常库不改写。run_fault_check.sh以同一emu、smoke和flash依次运行正确→错误→正确参考库，并验证输入文件摘要未变。

负例日志实际出现：

```text
v12_low different at pc = 0x0080000164, right = 0x0000000000000009, wrong = 0x0000000000000008
```

right是故意错误的REF，wrong是DUT。诊断PC不保证是vdot自身PC，不能据此认定vdot位于0x80000164；同一日志提交历史的首条vdot为PC 0x800001cc、指令02a4060b、wen 1 dst 12，未标为skip或delayed。随后ABORT且原始emu退出1。恢复正常库后smoke退出0并产生完整完成标记和GOOD TRAP。

验收驱动同时要求向量字段、精确9/8数据、合法未跳过提交、ABORT及退出1；一般非零退出、BAD TRAP或store mismatch不足以替代该反例。反例不进入正确性或性能数据。

## 异常契约修正与保护检查

首次真实差分发现坏SEW时DUT mtval=0、原REF为指令位；单独修正后又发现非零vstart恰好相反。源码路径说明后期执行单元配置检查没有译码trap指令载荷，而非零vstart被译码阶段拒绝。契约v2据此分开定义；RISC-V允许非法指令xtval为0或指令编码，见[特权规范](https://docs.riscv.org/reference/isa/v20260120/priv/machine.html)。

NEMU仅在自定义后期配置错误时设置一次性非架构标志，raise_intr消费后立即清除；非零vstart和普通非法指令保持原路径。没有关闭CONFIG_TVAL_EX_II，没有豁免mtval比较。工作负载逐一检查7种形式的目标不改写、vstart保留和mtval，并紧接执行普通非法0x7b确认没有残留自定义标志。最终smoke及独立NEMU完整随机已通过。

## 重跑入口与判据

```bash
bash scripts/run_rtl.sh vadd_test
bash scripts/run_fault_check.sh \
  "$PWD/build/nemu/fault-reference/nemu-ZRGKop/riscv64-nemu-interpreter-so"
bash scripts/run_rtl.sh vdot_test
bash scripts/run_rtl.sh pipeline_test
```

一般正例须原始退出0、指定完成标记、GOOD TRAP、Difftest初始化并拒绝任何ABORT、关键错误、断言失败、寄存器/store差异、预算耗尽或顶层EXIT。预算耗尽可能返回0，不能仅验进程状态。新驱动结束还重验emu、REF、工作负载和flash全部SHA256。

完整随机驱动已通过；干净检出全流程及最终材料仍待完成，不能把三阶段交付全部标为通过。独立ABI烟测和静态memcmp核对只作为补充证据，不替代上面的真实RTL反例。
