#!/usr/bin/env bash
# A live vadd run on the new clean final core, followed by its real FST.
set -euo pipefail
source "$(dirname -- "$0")/env.sh"
vdot_repro=${VDOT_REPRO_ROOT:?Set the clean checkout root}
vdot_acceptance=${VDOT_ACCEPTANCE_DIR:?Set the completed clean acceptance}
python3 - "$vdot_acceptance/acceptance.json" <<'PY'
import json,sys
s=json.load(open(sys.argv[1]));assert s['status']=='passed' and s['source_unchanged']
PY
vdot_demo="$VDOT_ROOT/reports/demo-stage1-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$vdot_demo"
printf '\n阶段一：开发环境、实际向量加法和波形关联\n'
printf '队伍：全栈漏洞队；参赛单位：西安电子科技大学。\n'
printf '本段在本轮新独立检出的最终扩展核上实时运行vadd。\n'
printf '\n$ git -C <本轮检出> rev-parse HEAD\n'
git -C "$vdot_repro" rev-parse HEAD
printf '\n$ git -C <XiangShan> rev-parse HEAD\n'
git -C "$vdot_repro/third_party/XiangShan" rev-parse HEAD
printf '\n全量构建已经完成：CHIRRTL -> firtool -> Verilator/C++。\n'
printf '这里核对已完成构建，长时间编译不在本段重新执行。\n'
python3 - "$VDOT_ROOT/rtl/baseline/provenance.json" "$vdot_repro" <<'PY'
from pathlib import Path
import json,subprocess,sys
r=json.load(open(sys.argv[1]));root=Path(sys.argv[2]);b=root/r['build_report']
assert (b/'compile-exit-status.txt').read_text().strip()=='0'
print('实际构建源码：',r['tested_project_head'])
print('FIR摘要：',r['fir_sha256'])
subprocess.run(['sha256sum','--check',str(b/'emu.sha256')],cwd=root/'third_party/XiangShan',check=True)
print('完整部署脚本、原始失败与恢复日志随操作日志包保留。')
PY
sleep 5
clear
printf '实时执行向量加法，并在0-15000周期窗口采集FST。\n'
printf '$ VDOT_WAVE_BEGIN=0 VDOT_WAVE_END=15000 bash scripts/run_rtl.sh vadd_test\n\n'
vdot_status=0
VDOT_WAVE_BEGIN=0 VDOT_WAVE_END=15000 bash "$vdot_repro/scripts/run_rtl.sh" vadd_test > "$vdot_demo/driver.log" 2>&1 || vdot_status=$?
printf '%s\n' "$vdot_status" > "$vdot_demo/exit-status.txt"
cat "$vdot_demo/driver.log"
[[ "$vdot_status" == 0 ]] || exit "$vdot_status"
vdot_run=$(sed -n 's/^RTL evidence: //p' "$vdot_demo/driver.log")
printf '%s\n' "$vdot_run" > "$vdot_demo/rtl-evidence.txt"
python3 - "$vdot_run/run.log" <<'PY'
from pathlib import Path
import re,sys
text=re.sub(r'\x1b\[[0-9;]*m','',Path(sys.argv[1]).read_text(errors='replace'))
for line in text.splitlines():
 if any(x in line for x in ('hello xiangshan','VADD_PASS','Difftest enabled','HIT GOOD TRAP','instrCnt')):print(line)
assert 'hello xiangshan, I am ' in text
PY
sleep 5
printf '\n从刚采集的真实FST提取握手；不回放先前测试。\n'
python3 "$VDOT_ROOT/scripts/extract_wave_events.py" "$vdot_run/wave.fst" --output "$vdot_demo/events"
clear
python3 - "$vdot_demo/events/events.json" "$vdot_repro/build/workloads/vadd_test.dis" <<'PY'
from pathlib import Path
import json,re,sys
matches=re.findall(r'^\s*([0-9a-f]+):\s+02850657\s',Path(sys.argv[2]).read_text(),re.M)
assert len(matches)==1;pc=int(matches[0],16);a=json.load(open(sys.argv[1]))
commits=[e for e in a if e['kind']=='commit' and e.get('pc')==pc];assert len(commits)==1
c=commits[0];tag=(c['rob_flag'],c['rob_value'])
ren=[e for e in a if e['kind']=='rename' and e.get('pc')==pc and (e.get('rob_flag'),e.get('rob_value'))==tag and e['edge']<=c['edge']]
r=max(ren,key=lambda e:e['edge']);dest=r['pdest']
print('同一动态指令的实际关联：PC=%#x ROB=%s P=%s'%(pc,tag,dest))
print('stage            edge       identity')
for kind in ('rename','issue','fu_in','fu_out','writeback','commit'):
 es=[e for e in a if e['kind']==kind and r['edge']<=e['edge']<=c['edge'] and (e.get('rob_flag'),e.get('rob_value'))==tag and e.get('pdest')==dest]
 assert len(es)==1,(kind,len(es));e=es[0]
 print('%-15s %6d      ROB=%s P=%s'%(kind,e['edge'],tag,dest))
 if 'data' in e:
  assert e['data']==int('34302c2824201c1814100c080400fcf8',16)
  print('  result=%032x'%e['data'])
print('\n按PC、ROB动态区间及物理目的跟踪；边沿序号不是cycle CSR。')
PY
sleep 8
printf '\n下面展示本轮完整验收FST生成的时序图，来源与实时运行分开记录。\n'
python3 "$VDOT_ROOT/scripts/show_recording_image.py" "$vdot_acceptance/wave-analysis/vadd-timeline.svg" --seconds 12
printf '\n阶段一完成：部署、真实输出、操作日志和向量加法链路均有记录。\n'
printf '本段实时运行目录：%s\n' "$vdot_demo"
printf '%s\n' "$vdot_demo"
sleep 5
