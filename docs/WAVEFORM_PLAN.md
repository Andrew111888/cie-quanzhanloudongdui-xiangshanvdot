# vadd.vv 波形分析准备

此文件记录静态定位，尚未取得真实执行波形；周期、ROB编号和实际执行通路均未验证。

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
