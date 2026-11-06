#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/env.sh"
vdot_root=${VDOT_REPRO_ROOT:?Set the completed clean checkout}
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
printf '下面直接读取本轮真实FST分析结果，列出微操作的输入与输出握手：\n'
python3 - "$vdot_acceptance/wave-analysis/analysis.json" <<'PY'
import json,sys
from pathlib import Path
wave=json.loads(Path(sys.argv[1]).read_text())
source=wave['latency_source']
print('FST: '+source['fst'])
print('SHA256: '+source['fst_sha256'])
print('采样：后端上升沿前；edge为采集内序号，不是cycle CSR。\n')
print('operation/uop       P     input    output   cycles   result[127:0]')
for name in ('multiply','reduce','vdot'):
 for pair in wave['fu_pairs'][name]:
  print('%-15s %5d %8d %9d %8d   %s'%
        (name+'/'+str(pair['uop']),pair['pdest'],pair['input_edge'],
         pair['output_edge'],pair['cycles'],pair['result_hex']))
print('\n归约uop0是内部部分和；uop1才写完整v12=8。')
print('结果以实际ROB动态区间和物理目的关联，不按相邻波形拼接。')
PY
sleep 10
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
print('\n第一组独立突发的真实握手：')
print('input  output  commit  ROB      P   vd')
for op in pipeline['independent_bursts'][0]['operations']:
 print('%5d %7d %7d  (%d,%3d) %3d  v%d'%
       (op['input_edge'],op['output_edge'],op['commit_edge'],op['rob_flag'],
        op['rob_value'],op['pdest'],op['ldest']))
print('\n性能表属于含必要配置与循环的片段，不能称为FU延迟。')
print('没有综合、时序或功耗测量，不声称面积、频率或能效收益。')
PY
clear
printf '展示本轮真实FST的派生时序图，输入/输出按ROB和物理目的关联。\n'
python3 "$VDOT_ROOT/scripts/show_recording_image.py" "$vdot_acceptance/wave-analysis/latency-timeline.svg" --seconds 14
clear
printf '新增对照：真实加载/存储、两条RVV序列、TA/TU及真依赖。\n'
printf '现在从已经完成的RTL原始数据重新计算；不把旧日志称作实时仿真。\n'
vdot_optimization=${VDOT_OPTIMIZATION_DIR:?Set the completed optimization report}
vdot_video_report="$VDOT_ROOT/reports/video-optimization-$(date -u +%Y%m%dT%H%M%SZ)"
python3 - "$vdot_optimization/evidence.json" "$VDOT_ROOT/scripts/optimization_report.py" "$vdot_video_report" <<'PYDATA'
import json,subprocess,sys
r=json.load(open(sys.argv[1]));cmd=['python3',sys.argv[2]]
for phase in ['before','after']:
 for kind in ['RVV','MEMORY']:
  cmd.extend(['--'+phase+('-rvv' if kind=='RVV' else '-memory'),r['runs'][phase][kind]['directory']])
cmd.extend(['--output',sys.argv[3]]);subprocess.run(cmd,check=True)
PYDATA
clear
python3 "$VDOT_ROOT/scripts/show_optimization_summary.py" "$vdot_video_report"
sleep 14
printf '\n阶段三演示结束。三段录屏、报告与最终源码将一起校验并打包。\n'
sleep 8
