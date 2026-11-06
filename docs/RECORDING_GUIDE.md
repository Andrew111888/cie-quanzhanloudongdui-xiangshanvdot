# 参赛者自行录屏入口

三段录屏由参赛者自行完成。本文提供可操作的命令和讲解点，不生成或上传视频。PPT按当前安排暂不制作。

## 使用已完成的本机仿真环境

```bash
cd /home/yh/cie/vdot-kmhv2
source scripts/env.sh
export VDOT_REPRO_ROOT=/home/yh/cie/vdot-kmhv2-repro-20261106
export VDOT_ACCEPTANCE_DIR="$VDOT_REPRO_ROOT/reports/acceptance-20261106T023150Z-228441"
```

正式验收与硬件构建源码为4e5cfce；当前作品另含补充逐例程序和文档。录像时区分现场重新执行、查看已完成的构建日志和查看原始波形三类动作，保持原始日志所记提交号。

## 第一阶段：操作过程

说明固定版本、单核保留向量的配置，打开提交包中的部署操作索引并解释实际内存故障及恢复；长时间构建可展示已有日志，不声称现场重新编译。

```bash
VDOT_WAVE_BEGIN=0 VDOT_WAVE_END=15000 \
  bash "$VDOT_REPRO_ROOT/scripts/run_rtl.sh" vadd_test
```

命令结束会打印实际RTL evidence目录；打开该目录run.log展示hello xiangshan、队名、IP、VADD_PASS和GOOD TRAP。IP来自工作负载构建时的本机地址。再展示正式验收FST和报告中的PC=0x80000118、ROB=(1,18)、P51关联，解释译码到提交31拍与ALU运算1拍的区别。

可用已有讲解脚本辅助：`bash scripts/demo_stage1.sh`。它会真实复跑vadd，并明确区分正式验收的派生时序图。

## 第二阶段：解题思路与基础测试

先展示contract.json、两级数据通路图与patches/xiangshan.patch：8路有符号乘法、16位乘积、17/18/19位归约、低32位结果和高96位清零，以及复用VIMac通路和共享资源的取舍。

```bash
bash scripts/run_basic_validation.sh \
  "$VDOT_REPRO_ROOT/third_party/XiangShan/build/emu" \
  "$VDOT_REPRO_ROOT/build/nemu/reference/riscv64-nemu-interpreter-so"
```

现场日志逐例展示positive=8、negative=-8、正边界131072、负边界-130048、最大值129032、零值0，并打印完整128位结果。解释负数只在低32位补码保存，高96位仍为零。展示完整随机/寄存器/流水回归时说明它们是已有完成记录。

## 第三阶段：波形、差分与性能

先展示NEMU补丁中的独立计算和完整写回。用已构建故障参考库运行真实正确→错误→恢复，展示错误比较能失败；故障退出1是预期反例，恢复必须成功。原始例子的首条vdot提交PC与差异诊断PC有区别。

```bash
VDOT_BAD_REF=$(sed -n 's/^FAULT_REFERENCE_BUILT //p' "$VDOT_ACCEPTANCE_DIR/fault-build.log")
bash "$VDOT_REPRO_ROOT/scripts/run_fault_check.sh" "$VDOT_BAD_REF"
```

打开三阶段性能分析文档和FST：vdot输入到输出2拍；此次基线首个乘法输入至最终归约16拍，包含配置/清零/调度。解释组合路径、程序片段、吞吐三个边界，不能混称。

展示两条RVV基线、三长度五重复的原始周期、540条前后样本和含访存结果。重点说明旧vd虚假依赖消除在独立TU场景有效，真实依赖链及含访存未因此普遍改善；没有面积、功耗或LLM收益实测。

## 录制完成后

自行检查每段能看清命令、输入输出、波形和解释；不要在视频中打开私人联系信息或提交明文。三个视频文件由参赛者交付后，再核对文件、最终源码绑定及官网上传次数，统一更新官网材料。
