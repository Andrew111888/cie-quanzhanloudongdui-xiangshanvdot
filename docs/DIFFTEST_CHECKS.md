# 向量 Difftest 验收判据

本文件记录对当前工作区的静态审计，以及 emu 可用后应执行的正例、故障注入和恢复回归。编写时 `third_party/XiangShan/build/emu` 尚不存在，没有整核运行日志；本文中的RTL预期输出均为源码推导，不是动态通过证据。静态审计未修改checker；随后仅REF的真实ABI烟测结果单列在文末，不能与RTL验收混淆。

| 检查 | 当前状态 |
|---|---|
| 向量寄存器、向量 CSR 比较及日志路径 | 静态审计通过 |
| 隔离错误参考库 | 已生成并核对摘要，尚未证明能被 DUT 比较器检出 |
| 标准向量 vadd 整核执行及波形 | 动态待验证 |
| 正常 REF 的 vdot smoke | 动态待验证 |
| 错误 REF 被向量比较器检出 | 动态待验证 |
| 恢复后的 smoke 与 1000 组随机回归 | 动态待验证 |

## 证据身份

以下为审计时实际检出的 Git HEAD。XiangShan 和 NEMU 含本项目的 vdot 修改，HEAD 不能单独代表完整源码；每次真实运行还须保存源码清单、未提交修改摘要及二进制 SHA256。Difftest 的受版本控制文件在本次审计时无修改，只有本任务既有计划和进度文件未跟踪。

| 工程 | 固定 HEAD |
|---|---|
| 本项目 | `0b95cb925fe26244f67be6118df41f658b0e385f` |
| XiangShan | `7b16188f7f18a97be69c9b1a2dae8a446eec3b47` |
| Difftest | `3729300ae233816d332d057f170472ebe35147b0` |
| NEMU | `d772a9d9e06f663d529bd1c6518480c1ee59ded2` |
| xs-env | `822e3581a2757d4a9848b065fd2a3057957b401e` |

审计时关键文件/产物的 SHA256：

| 文件 | SHA256 |
|---|---|
| `third_party/XiangShan/difftest/src/test/csrc/difftest/refproxy.h` | `93121e4679ea0809cc451dd92b99a30f5a2939e87b93b41094731dcbec1bafe6` |
| `third_party/XiangShan/difftest/src/test/csrc/difftest/refproxy.cpp` | `85cf3d73f6b00f69ee5ac8ebfd7e46d5cd971c7575a1200f1b7470b019b3899e` |
| `third_party/XiangShan/difftest/src/test/csrc/difftest/difftest.cpp` | `0ddfa2e581a1b088a24ae38293632ce09f8def610d578e9b888bbc0210a3474e` |
| `third_party/XiangShan/build/generated-src/difftest-state.h` | `13b8408e3eed1ff57c9d812bf59ae5eddde1d2c5a534e1c4220b741a5cce3c1f` |
| `third_party/NEMU/src/isa/riscv64/instr/rvv/vcompute.h`，正常实现 | `3b04d0233b0d8832f1908b36b37e472bd061948c79853b2b505a677138603f06` |
| `workloads/vdot_test.c` | `e43d970191ed0d60eef30682127a16e2447233b3ea6ff988438c9295a14f8eb8` |
| `configs/nemu-reference.config`，与已保存的参考配置相同 | `250b457f844796b3767e689e21d4b8708159e4b634f7b835446b8e57d6cade4a` |
| `build/nemu/reference/riscv64-nemu-interpreter-so`，正常库 | `6f258e9dd5061bd0058f9404dfa97881042232f2ceb8658392f818741c0bad91` |
| `build/nemu/fault-reference/nemu-OnIFEj/riscv64-nemu-interpreter-so`，故意错误的库 | `4b776b8eb02efaaff03dcd5ee861fe4844484082c85d2717625ae3d1f38364c4` |
| `build/workloads/vdot_smoke.bin` | `a241f6247d623d082110e521a23e6f0f8c1c364c38764260d012b1d7b744e29e` |
| `build/workloads/vdot_smoke.dis` | `ea9ff3e470d7a9c30a1226b32f4fd8d666dce6abb3a6f47ca5504a9bd7874136` |
| `build/workloads/flash.bin` | `12b791f69e01db906377cac6d6b15c4cce7cd09c226515f181f7687186f786bd` |

生成文件、工作负载或库重新构建后，应以新的运行清单为准，不能沿用本表证明新产物。最终 emu 的 SHA256 仍待生成。

## 比较与失败传播路径

当前[生成头:181](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/build/generated-src/difftest-state.h:181)定义 `CONFIG_DIFFTEST_VECCSRSTATE`，七项为 `vstart/vxsat/vxrm/vcsr/vl/vtype/vlenb`；[生成头:249](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/build/generated-src/difftest-state.h:249)定义 `CONFIG_DIFFTEST_ARCHVECREGSTATE`，覆盖全部 32 个 128 位向量寄存器。

[refproxy.cpp:185](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/refproxy.cpp:185)使用 `memcmp` 比较完整 `vrf` 和 `vcsr`。普通 CSR waive 只处理最后的 `csr` 项，不能豁免前面的向量差异。[difftest.cpp:685](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/difftest.cpp:685)先从 REF 同步状态，再执行 `proxy->compare(dut)`；比较失败返回 checker 的 `STATE_DIFF=1`。这与全局 trap 枚举不是同一组状态码。

[difftest.cpp:155](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/difftest.cpp:155)收到 `STATE_DIFF` 后调用 `Difftest::display()`，随后落入 `STATE_ERROR` 分支，返回全局 `STATE_ABORT=2`。[difftest.cpp:769](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/difftest.cpp:769)显示提交历史、REF 寄存器及逐字段差异。不能把内部 `STATE_ABORT=2` 当作 shell 退出码。

## 精确日志与退出状态

向量低半部的字段名是 **`v12_low`**，不是 `v12`、`vrf[12]` 或 `v12_lo`，见[refproxy.h:63](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/refproxy.h:63)。[REPORT_DIFFERENCE:551](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/refproxy.h:551)的精确格式是：

```c
"%7s different at pc = 0x%010lx, right = 0x%016lx, wrong = 0x%016lx\n"
```

[refproxy.cpp:238](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/refproxy.cpp:238)明确传入 `right=REF`、`wrong=DUT`。因此错误参考库的预期差异行模板为以下内容；这不是实测日志：

```text
v12_low different at pc = 0x<诊断PC>, right = 0x0000000000000009, wrong = 0x0000000000000008
```

`different at pc` 的诊断 PC 取 `commit[0].pc`（若该项仍 valid），否则取 `trap.pc`，见[refproxy.cpp:234](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/refproxy.cpp:234)。它不是保证指向故障指令的独立 PC 字段，不应将该行的 PC 硬编码成 vdot 地址。注入位置应结合 `Commit Instr Trace` 的 PC、`inst 02a4060b`、目标寄存器和未跳过状态判断，格式见[diffstate.cpp:20](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/diffstate.cpp:20)与[diffstate.h:63](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/diffstate.h:63)。

下表适用于正常、非 `FUZZING/FUZZER_LIB` 的 emu，源码依据为[emu.cpp:651](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/emu/emu.cpp:651)、[emu.h:93](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/emu/emu.h:93)、[main.cpp:64](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/emu/main.cpp:64)。

| 结果 | 最终文本 | shell 退出码 | 验收含义 |
|---|---|---|---|
| 正常工作负载结束 | `HIT GOOD TRAP at pc = 0x...` | 0 | 还须有指定工作负载完成标记且无错误 |
| 工作负载返回失败 | `HIT BAD TRAP at pc = 0x...` | 1 | 不能单独证明向量比较器检测到了差异 |
| Difftest 差异或 checker 错误 | `ABORT at pc = 0x...` | 1 | 还须有精确向量字段差异，才能验收本故障注入 |
| 周期/指令预算耗尽 | `EXCEEDING CYCLE/INSTR LIMIT at pc = 0x...` | 0 | **不算通过**，不能只检查退出码 |
| 仿真顶层请求退出 | `EXIT at pc = 0x...` | 0 | 不能代替本工作负载的 GOOD TRAP 和完成标记 |

向量差异行没有通用的 `DIFFTEST FAIL` 或 `mismatch` 单词，不能只搜索这两个词。`Info` 日志受 `sim_verbose` 控制，默认开启，见[common.h:73](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/common/common.h:73)与[common.cpp:167](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/common/common.cpp:167)。验收应保存 stdout、stderr，去除 ANSI 色码后匹配。

## 正例、反例与恢复回归

所有运行使用同一 emu、同一 smoke/flash、单核和 `--ram-size=128MB`；更换 REF 是故障注入运行的唯一运行参数差异。保留 `--diff` 的明确绝对路径，禁止 `--no-diff`，构建不能带 `NO_DIFF=1`。日志应出现固定源码的初始化文本 `The first instruction of core 0 has commited. Difftest enabled.`，见[instructions.cpp:30](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/checkers/instructions.cpp:30)。该文本仅证明初始化发生，不能单独证明向量比较。

当前运行入口为[run_rtl.sh:19](/home/yh/cie/vdot-kmhv2/scripts/run_rtl.sh:19)，默认带 `--no-squash` 和 `-C 5000000`，可用 `VDOT_MAX_CYCLES` 显式调整预算。它在独立报告目录保存命令、源码清单、产物摘要、原始退出码与合并日志，见[run_rtl.sh:27](/home/yh/cie/vdot-kmhv2/scripts/run_rtl.sh:27)。触及预算必须判为未完成并记录后续预算调整。

以下仅为 emu 可用后依次执行的入口；本次审计没有执行。`run_fault_check.sh` 自己依次运行正常 smoke、错误 REF smoke、正常 REF smoke；整套反例尚未运行，不能把脚本存在或错误库构建成功当作反例通过。

```bash
vdot_root=/home/yh/cie/vdot-kmhv2
vdot_bad="$vdot_root/build/nemu/fault-reference/nemu-OnIFEj/riscv64-nemu-interpreter-so"
test -x "$vdot_root/third_party/XiangShan/build/emu"
bash "$vdot_root/scripts/run_rtl.sh" vadd_test

# 标准向量正例验收后，再执行正常 smoke -> 错误 REF -> 正常 smoke。
bash "$vdot_root/scripts/run_fault_check.sh" "$vdot_bad"

# 上述检查全部通过后，用正常 REF 完成 1000 组随机回归。
bash "$vdot_root/scripts/run_rtl.sh" vdot_test
```

1. **正例。** `vadd` 要求退出码 0、`VADD_PASS`、`HIT GOOD TRAP`；smoke 要求退出码 0、`VDOT_PASS random_cases=0 directed_cases=6 modes=5 illegal_cases=7`、`HIT GOOD TRAP`。拒绝任何 `different at pc`、`Mismatch for store commits`、`ABORT`、`HIT BAD TRAP`、`HIT CRITICAL ERROR`、断言失败、预算耗尽或信号退出。不能把 NEMU 单独运行结果记作整核差分通过。

2. **准备错误参考库。** 使用 `bash scripts/build_fault_reference.sh` 的隔离复制流程。它将当前 NEMU 源码复制到 `build/fault-injection/nemu-XXXXXX`，仅在副本中把[NEMU vcompute.h:35](/home/yh/cie/vdot-kmhv2/third_party/NEMU/src/isa/riscv64/instr/rvv/vcompute.h:35)改为 `vreg_l(id_dest->reg, 0) = ((uint32_t)result) ^ UINT32_C(1);`，再按冻结参考配置构建，产物输出到 `build/nemu/fault-reference/nemu-XXXXXX/`。live NEMU 和正常库不变，无需改回 live 源码或重建正常库。复制过滤仅排除 NEMU 根层的构建输出，保留 softfloat 等依赖中合法的 `build` 子目录，见[build_fault_reference.sh:17](/home/yh/cie/vdot-kmhv2/scripts/build_fault_reference.sh:17)。高位清零、合法性检查、`vstart=0` 和 dirty 更新保持原样；禁止跳过 vdot 或将 DUT 结果同步给 REF。脚本保存 `fault.json`、冻结配置、生成头、库摘要，并核对 live 源文件摘要，见[build_fault_reference.sh:24](/home/yh/cie/vdot-kmhv2/scripts/build_fault_reference.sh:24)。当前错误库已生成，路径和摘要见上表；通用调用应取脚本打印的 `FAULT_REFERENCE_BUILT <绝对路径>`。该构建标记不代表整核故障注入通过。

3. **反例最小验收集合。** 用同一 smoke 仅替换 `--diff` 后，必须同时满足：实际加载了记录摘要的错误库；提交历史包含合法且未跳过的 `02a4060b`；出现 `v12_low different at pc = ...` 且 **right 为 `0x0000000000000009`、wrong 为 `0x0000000000000008`**；最终 `ABORT`、shell 退出码 **1**；没有更早的无关异常、超时或 store checker 失败。`HIT BAD TRAP`、一般非零退出、单独的 store mismatch 或只看到 NEMU 输出错误均不足以通过本反例。可在去色后的日志上用 `v12_low different at pc = 0x[0-9a-fA-F]+, right = 0x0000000000000009, wrong = 0x0000000000000008` 精确匹配。若未满足，保留失败证据并定位原因，不能修改验收器来接受 BAD TRAP。

   提交文本的最小检查应先提取**第一条** `commit pc ... inst 02a4060b ...` 整行，再要求 `wen 1 dst 12`。可匹配 `(?m)^\[\d+\]\s+commit pc ([0-9a-fA-F]{16}) inst 02a4060b wen 1 dst 12 data [0-9a-fA-F]{16} idx ([0-9a-fA-F]{3})([^\r\n]*)$`，尾部不得有 `(S)` 或 `(W)`。`get_tag` 对 skip、delayed 采用字符按位或：仅 skip 是 `S`，二者同时为真是 `W`，见[diffstate.h:77](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/diffstate.h:77)。本 vdot 预期也无 delayed，严格验收可要求尾部只有空白和可选的 ` <--`。不要跳过第一条异常/skip 记录，再寻找后面的合法记录。还应检查负例 RTL 报告目录中的 `exit-status.txt` 为 1，区分原始 emu 状态与包装脚本状态。

4. **为什么首例是 DUT 8 / REF 9。** [vdot_test.c:106](/home/yh/cie/vdot-kmhv2/workloads/vdot_test.c:106)的首个输入对为 `{1,1}`，循环从 `n=0`、`mode=0` 开始，低八个有符号字节的积之和为 8；[vdot_test.c:29](/home/yh/cie/vdot-kmhv2/workloads/vdot_test.c:29)写 v12 的编码为 `0x02a4060b`。smoke 是同一源码以 `RANDOM_CASES=0` 编译，见[build_workloads.sh:21](/home/yh/cie/vdot-kmhv2/scripts/build_workloads.sh:21)，未开启标准 vstart 探测。当前绑定反汇编中首个 mode-0 vdot 位于 `0x800001cc`，见[vdot_smoke.dis:165](/home/yh/cie/vdot-kmhv2/build/workloads/vdot_smoke.dis:165)。重新编译可能改变地址，必须重新核对。

5. **恢复回归。** 错误库反例通过后，用已恢复正常实现的库再跑同一 smoke，再跑 `vdot_test.bin`。后者必须打印 `VDOT_PASS random_cases=1000 directed_cases=6 modes=5 illegal_cases=7`，同时满足正例的退出码与无错误条件。记录 emu、两种 REF、工作负载、flash 和当前源码摘要；错误库不参与任何正常结果或性能记录。全部动态检查完成前，本文件状态保持“待验证”，不能提交比赛结果。

当前[check_run.py:9](/home/yh/cie/vdot-kmhv2/scripts/check_run.py:9)已拒绝 `different at pc`、包含 store mismatch 的一般 `mismatch`、`EXCEEDING CYCLE/INSTR` 与 `EXIT at pc`，并要求 GOOD TRAP 和指定完成标记。进程退出码由[run_rtl.sh:40](/home/yh/cie/vdot-kmhv2/scripts/run_rtl.sh:40)单独保存并检查。`check_run.py` 不验收反例；反例入口为[run_fault_check.sh:19](/home/yh/cie/vdot-kmhv2/scripts/run_fault_check.sh:19)，它尚未执行。验收还须核对运行身份、预期覆盖量和上述提交记录，不能只依据一个 PASS 字样。

## 仅 REF 的 ABI 烟测准备

此检查只验证参考库 ABI、指令解码和 vdot 运算，不包含 DUT、Difftest 比较器或 RTL；即使通过，也不能填充上述整核动态状态。本次审计只核对调用约定，没有执行该烟测。

当前 NEMU 向外复制的是 `riscv64_CPU_state` 从 `gpr` 到 `difftest_state_end` 之前的前缀，见[isa-def.h:96](/home/yh/cie/vdot-kmhv2/third_party/NEMU/src/isa/riscv64/include/isa-def.h:96)与[NEMU regcpy:251](/home/yh/cie/vdot-kmhv2/third_party/NEMU/src/isa/riscv64/difftest/ref.c:251)。对应 Difftest 结构名是 **`ref_state_t`**，见[refproxy.h:200](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/refproxy.h:200)，不是缺少 `pc` 插入位置的 `DiffTestRegState`。复制长度为 **1400 字节，即 175 个 uint64_t**，不包含 `difftest_state_end` 本身。

| 字段 | 字节偏移 / 长度 |
|---|---|
| `gpr[32]`、`fpr[32]` | 0 / 256、256 / 256 |
| `mode`、`mstatus` | 512 / 8、520 / 8 |
| 普通 CSR 块，包括 `mode` 但不包括 `pc` | 512 / 144 |
| `pc` | 656 / 8 |
| HCSR 块，从 `v` 到 `vsscratch`，共 17 项 | 664 / 136 |
| `vr[32]`，每个寄存器低/高两个 uint64_t | 800 / 512 |
| `vstart,vxsat,vxrm,vcsr,vl,vtype,vlenb` | 分别为 1312、1320、1328、1336、1344、1352、1360，各 8 字节 |
| `fcsr` | 1368 / 8 |
| `tselect,tdata1,tinfo` | 1376、1384、1392，各 8 字节 |

最小可用顺序如下，建议正确库与错误库分别在独立进程中加载一次，避免两个库中的同名全局符号互相影响。若显式复刻 Difftest 加载模式，可参考[refproxy.cpp:130](/home/yh/cie/vdot-kmhv2/third_party/XiangShan/difftest/src/test/csrc/difftest/refproxy.cpp:130)的 `RTLD_DEEPBIND`。

1. `dlopen` 库并解析符号，然后 `difftest_set_ramsize(size_t(128*1024*1024))`。
2. `difftest_init_v2(unsigned(1400))`。它内部调用 `difftest_init()` 并检查长度，不要重复再调 init，见[NEMU ref.c:447](/home/yh/cie/vdot-kmhv2/third_party/NEMU/src/cpu/difftest/ref.c:447)。初始化已分配内存、初始化 ISA、设备与 CSR 镜像，见[init.c:259](/home/yh/cie/vdot-kmhv2/third_party/NEMU/src/isa/riscv64/init.c:259)。
3. `difftest_regcpy(buffer, false)` 先取初始化后的 1400 字节，再修改指定字段。当前关闭 LightQS，真实 NEMU 导出签名是 `void difftest_regcpy(void*, bool)`，见[NEMU ref.c:146](/home/yh/cie/vdot-kmhv2/third_party/NEMU/src/cpu/difftest/ref.c:146)。不要将所有 CSR 从零构造，否则会丢失初始化的 HCSR/trigger 状态。
4. 保留其它初始字段，设置 `mode=3`（M 模式）、`v=0`、`pc=0x80000000`、`mstatus=(mstatus & ~0x600) | 0x600`（VS=Dirty）、`vstart=vxsat=vxrm=vcsr=0`、`vl=8`、`vtype=0`、`vlenb=16`。设置 `vr[8]._64[0]=vr[10]._64[0]=0x0101010101010101`，把 v12 两半预置为非零哨兵。VS 位掩码见[encoding.h:22](/home/yh/cie/vdot-kmhv2/third_party/NEMU/src/isa/riscv64/local-include/encoding.h:22)，合法性门禁见[vcompute_impl.c:358](/home/yh/cie/vdot-kmhv2/third_party/NEMU/src/isa/riscv64/instr/rvv/vcompute_impl.c:358)。然后 `difftest_regcpy(buffer, true)` 写入状态；该路径也调用 CSR writeback 和 MMU 状态刷新。
5. `difftest_memcpy(uint64_t(0x80000000), instruction_bytes, size_t(4), true)`，其中小端指令字节为 `0b 06 a4 02`（`0x02a4060b`）。普通 memcpy 不会因初始化用 large-copy 跳过零内容，见[NEMU ref.c:113](/home/yh/cie/vdot-kmhv2/third_party/NEMU/src/cpu/difftest/ref.c:113)。再 `difftest_exec(uint64_t(1))`，最后 `difftest_regcpy(buffer, false)` 取回结果，见[NEMU ref.c:208](/home/yh/cie/vdot-kmhv2/third_party/NEMU/src/cpu/difftest/ref.c:208)。方向 `false=TO_DUT/读取 REF`、`true=TO_REF/写入 REF`，见[difftest.h:23](/home/yh/cie/vdot-kmhv2/third_party/NEMU/lib-include/difftest.h:23)。FFI 应显式声明这些参数宽度与 void 返回类型。
6. 正常库预期 `pc=0x80000004`、`vr[12]._64[0]=8`、`vr[12]._64[1]=0`；错误库低半部为 9，高半部仍为 0。低半部严格等于 8/9 也同时证明位 63:32 清零，合计检查高 96 位为零。另核对 `vstart=0`、`vl=8`、`vtype=0`；仅没有崩溃不足以通过。

单核配置关闭 `MULTICORE_DIFF`，无需 `difftest_set_mhartid`；该符号仅在多核配置导出，见[NEMU ref.c:482](/home/yh/cie/vdot-kmhv2/third_party/NEMU/src/cpu/difftest/ref.c:482)。本检查将 PC 直接设为 RAM 地址，不从复位 flash 取指，因此无需 `difftest_load_flash`；不需要额外手工初始化设备、CSR 或调用 `difftest_csrcpy`。这些省略只适用于上述单指令 RAM 烟测，不能用于缩减整核启动流程。

## 本轮仅REF的实际ABI结果

主代理已实现并运行`scripts/check_reference_abi.py`，每个库使用独立Python进程，通过真实导出接口初始化128MB RAM、写入一条`0x02a4060b`并执行。初始v12两半均为非零哨兵，v8/v10高64位设置为不同数据，因而也检查了通道选择和目标清零。两次进程均退出0：

| 库 | 实际v12低64位 | 实际v12高64位 | 其余检查 | 本机日志 |
|---|---:|---:|---|---|
| 正常库，SHA256 `6f258e9dd5061bd0058f9404dfa97881042232f2ceb8658392f818741c0bad91` | 8 | 0 | PC=0x80000004，vstart=0 | `reports/reference-abi-good.log` |
| 故障库，SHA256 `4b776b8eb02efaaff03dcd5ee861fe4844484082c85d2717625ae3d1f38364c4` | 9 | 0 | PC=0x80000004，vstart=0 | `reports/reference-abi-fault.log` |

这确认了两种库的ABI可调用及单比特故障真实生效，没有执行DUT、状态比较器或RTL流水线。上面的正常RTL、错误REF检出、恢复随机回归仍为待验证。
