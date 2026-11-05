#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/env.sh"
vdot_root=${VDOT_REPRO_ROOT:-/home/yh/cie/vdot-kmhv2-repro-20261105}
vdot_acceptance=${VDOT_ACCEPTANCE_DIR:?Set the completed clean acceptance report}
python3 - "$vdot_acceptance/acceptance.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1]))['status']=='passed'
PY
printf '\n阶段三：真实差分反例、恢复与性能分析\n'
printf '队伍：全栈漏洞队。NEMU独立执行vdot，不跳过、不复制DUT结果。\n'
printf '\n$ sed -n ... NEMU/instr/rvv/vcompute.h\n'
sed -n '23,47p' "$vdot_root/third_party/NEMU/src/isa/riscv64/instr/rvv/vcompute.h"
printf '\n比较全部32个128位向量寄存器及7项向量CSR，导出ABI=1400字节。\n'
sleep 6
clear
printf '现在实时运行：正确REF -> 低位故障REF -> 正确REF。\n'
printf '故障库仅改变结果最低位，独立副本生成，不改正常源码。\n'
vdot_bad=$(sed -n 's/^FAULT_REFERENCE_BUILT //p' "$vdot_acceptance/fault-build.log")
printf '\n$ bash scripts/run_fault_check.sh <已校验的隔离故障库>\n'
bash "$vdot_root/scripts/run_fault_check.sh" "$vdot_bad" > "$vdot_acceptance/video-stage3-fault.log" 2>&1
cat "$vdot_acceptance/video-stage3-fault.log"
python3 - "$vdot_acceptance/video-stage3-fault.log" <<'PY'
import re,sys
from pathlib import Path
driver=Path(sys.argv[1]).read_text()
directories=[Path(s.removeprefix('RTL evidence: ')) for s in driver.splitlines() if s.startswith('RTL evidence: ')]
# The outer driver may summarize child directories instead of printing them.
if len(directories)!=3:
 folders=[Path(s.removeprefix('Fault-check evidence: ')) for s in driver.splitlines() if s.startswith('Fault-check evidence: ')]
 if len(folders)==1:
  folder=folders[0];directories=[]
  for name in ('positive-before.log','negative.log','positive-restored.log'):
   p=folder/name
   if p.exists():
    directories.extend(Path(s.removeprefix('RTL evidence: ')) for s in p.read_text().splitlines() if s.startswith('RTL evidence: '))
if len(directories)!=3: raise SystemExit('Cannot identify all three real fault-check runs; inspect outer log')
for n,p in enumerate(directories):
 text=re.sub(r'\x1b\[[0-9;]*m','',(p/'run.log').read_text())
 print('\n'+('正确','故障','恢复')[n]+'：'+str(p))
 for line in text.splitlines():
  if any(k in line for k in ('v12_low different','VDOT_PASS','HIT GOOD TRAP','ABORT at')):print(line)
 print('原始退出码：'+(p/'exit-status.txt').read_text().strip())
PY
sleep 6
clear
printf '基线：vwmul有符号扩宽乘法 -> SEW切换/目标清零 -> vwredsum到32位。\n'
printf '以下从已完成RTL原始日志重新计算，不使用NEMU时间或指令数。\n'
vdot_bench=$(sed -n 's/^RTL evidence: //p' "$vdot_acceptance/benchmark.log")
python3 "$vdot_root/scripts/performance_report.py" "$vdot_bench/run.log" --engine rtl \
  --output "$vdot_acceptance/video-performance.md"
cat "$vdot_acceptance/video-performance.md"
sleep 7
clear
python3 - "$vdot_acceptance" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);wave=json.loads((p/'wave-analysis/analysis.json').read_text())
pipeline=json.loads((p/'pipeline-analysis/pipeline-analysis.json').read_text())
print('真实FST：vdot输入至结果 %s 周期。'%wave['vdot_input_to_result_cycles'])
print('此次基线首个乘法至最终归约 %s 周期，含配置/清零/调度。'%wave['baseline_input_to_final_result_cycles'])
print('基线归约包含2个微操作：首个是部分和，第二个才是v12的最终结果。')
print('独立突发组数：',len(pipeline['independent_bursts']))
print('每组8条，实测接收/输出间隔1周期，逐个核对结果、ROB、物理目的及提交。')
print('已完成写回后被分支冲刷、未提交的错路vdot：',len(pipeline['cases']))
print('\n性能表属于含必要配置与循环的片段，不能称为FU延迟。')
print('没有综合、时序或功耗测量，不声称面积、频率或能效收益。')
PY
printf '\n阶段三演示结束。三段录屏、报告与最终源码将一起校验并打包。\n'
sleep 8
