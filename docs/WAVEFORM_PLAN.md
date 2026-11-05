# 波形信号定位与重跑准备

本文件保留信号定位和重跑方法。现已取得真实执行波形；实际周期、ROB关联、输入/输出与提交证据见 `STAGE1_WAVEFORM.md`，基线与vdot真实路径见 `PERFORMANCE.md`。以下候选路径仅用于重新定位，不能替代实际结果。

当前 `build/workloads/vadd_test.dis` 中，`vadd_target_pc=0x80000118`，指令字 `0x02850657`，即 `vadd.vv v12,v8,v10`，配置 `VL=16, SEW=8, LMUL=1, tu,mu`。预期128位结果为 `34302c2824201c1814100c080400fcf8`。每次重编工作负载后应重新核对该PC。

生成RTL中后端公共层级为 `SimTop.cpu.l_soc.core_with_l2.core.backend`（FST中可能带`TOP.`前缀，待实际确认）。

| 阶段 | 公共层级下的候选实例与信号 | 关联方式 |
|---|---|---|
| 解码 | `inner_ctrlBlock.decode`，`io_in_k_{valid,ready}`、`io_in_k_bits_{pc,instr}`，k=0..5 | 目标PC、编码和输入握手 |
| 重命名 | `inner_ctrlBlock.rename`，`io_out_k_{valid,ready}`、`io_out_k_bits_{pc,instr,ldest,pdest,robIdx_flag,robIdx_value}` | 目标PC输出握手时记录R={flag,value}、P=pdest，ldest=12 |
| 发射 | `inner_vfScheduler`，`io_toDataPathAfterDelay_{0_0,1_0}_{valid,ready}`，对应`bits_common_{robIdx_flag,robIdx_value,pdest,fuType,fuOpType}` | 两条候选VIALU通路按同一R匹配握手 |
| 执行 | `inner_vfExuBlock.exus`或`exus_2`，父级`io_in_*`，子模块`VialuFix.io_out_valid`、`io_out_bits_ctrl_*`、`io_out_bits_res_data` | 以父级入口R及FU输出R串联；不得把后一级ctrlPipe与当拍入口valid直接配对 |
| 写回 | `inner_wbDataPath.io_toCtrlBlock_writeback_{13,15}_valid`及`bits_{robIdx_flag,robIdx_value,pdest,vecWen,data_0}` | 0_0→13，1_0→15；再按P核对`io_toVfPreg_j_{wen,addr,data,vecWen}` |
| 提交 | `inner_ctrlBlock.rob`，`io_commits_isCommit`、`io_commits_commitValid_i`、`io_commits_robIdx_i_{flag,value}`、`io_commits_info_i_debug_pc`，i=0..7 | 同一R、目标PC、ldest=12；Difftest提交探针额外延迟3拍，不能代替即时ROB提交 |

定位依据为固定版本生成的 `DecodeStage.sv`、`Rename.sv`、`Scheduler_2.sv`、`ExuBlock_2.sv`、`VIAluFix.sv`、`WbDataPath.sv` 与 `Rob.sv`，及 `src/main/scala/xiangshan/backend/rob/Rob.scala` 的探针注册。正式报告应替换为真实波形信号、取值和周期。

固定Difftest实现中，`--dump-wave`与`--dump-wave-full`都使用99层trace；full额外记录下降沿，并在-b0时包含复位段。建议短窗口运行：

```bash
VDOT_WAVE_BEGIN=BEGIN VDOT_WAVE_END=END bash scripts/run_rtl.sh vadd_test
```

BEGIN/END须用实际提交日志或首次波形确定的整数周期替换。波形时间戳不能直接当CPU周期，尤其在包含复位段时。需要验证目标指令是否重放或被冲刷、实际VIALU通路、结果写回值及最终提交；静态源代码定位不能代替这些证据。

## 基线与vdot延迟定位

`workloads/latency_probe.c` 提供一次等价基线和一次vdot，结果均为低32位8、高96位0。NEMU与RTL功能均已通过，真实FST确认vdot2周期，基线首乘法至最终归约16周期（含配置和调度）。当前反汇编定位如下，重编译后必须重新核对：

| 符号 | PC | 用途 |
|---|---|---|
| baseline_latency_begin | 0x800000ba | vwmul入口指令 |
| baseline_latency_reduce | 0x800000ca | vwredsum入口指令 |
| baseline_latency_end | 0x800000d2 | 基线结果存储；此前已恢复SEW=8 |
| vdot_latency_begin | 0x800000e2 | vdot指令 |
| vdot_latency_end | 0x800000e6 | vdot结果存储 |

使用 `bash scripts/run_rtl.sh latency_probe`，需要波形时设置有效的VDOT_WAVE_BEGIN/END。按PC找到对应ROB标识，分别记录各算术指令的功能单元输入握手和结果有效周期。基线首个乘法握手至末次归约结果有效的区间包含中间配置与清零指令造成的等待，应标为该等价组合的计算路径延迟；vdot的输入握手至结果有效才是其功能单元执行延迟。另行报告两段指令的提交/结果存储边界和benchmark程序片段周期，不能混用这些指标。单次短程序没有吞吐测量意义，吞吐仍使用多次独立操作批次并说明循环和配置开销。
