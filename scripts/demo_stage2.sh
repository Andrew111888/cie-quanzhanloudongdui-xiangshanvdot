#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/env.sh"
vdot_root=${VDOT_REPRO_ROOT:-/home/yh/cie/vdot-kmhv2-repro-20261105}
vdot_acceptance=${VDOT_ACCEPTANCE_DIR:?Set the completed clean acceptance report}
python3 - "$vdot_acceptance/acceptance.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1]))['status']=='passed'
PY
printf '\n阶段二：vdot 设计与真实整核功能演示\n'
printf '队伍：全栈漏洞队。完整验收已完成；下面另行实时运行smoke和寄存器边界测试。\n'
printf '\n暂定契约：低8对有符号int8；低32位补码结果，高96位清零。\n'
printf 'SEW=8 VLEN=128 LMUL=1 VL=8 vstart=0 vm=1；尚无赛题方语义确认。\n'
printf '\n$ cat contract.json\n'
cat "$vdot_root/contract.json"
sleep 4
clear
printf '实际Chisel算术路径：8路有符号乘法、17/18/19位加法树、两级流水。\n'
sed -n '18,39p' "$vdot_root/third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala"
printf '\n接入：VecDecoder -> 原VIMac调度/读源 -> VdotDatapath -> 原写回/ROB。\n'
printf '共享乘法槽位；没有新增独立发射端口。\n'
sleep 5
clear
printf 'smoke真实测试循环的6组输入，每组5种模式：\n'
printf '  1*1*8=8；(-1)*1*8=-8\n'
printf '  (-128)*(-128)*8=131072；(-128)*127*8=-130048\n'
printf '  127*127*8=129032；0*(-128)*8=0\n'
printf '  独立目标、vd=vs1、vd=vs2、两源相同、等价向量基线。\n'
printf 'C模型逐项断言完整128位；另外检查7种非法形式及普通非法0x7b。\n\n'
printf '$ bash scripts/run_rtl.sh vdot_smoke\n'
bash "$vdot_root/scripts/run_rtl.sh" vdot_smoke > "$vdot_acceptance/video-stage2-smoke.log" 2>&1
cat "$vdot_acceptance/video-stage2-smoke.log"
vdot_smoke=$(sed -n 's/^RTL evidence: //p' "$vdot_acceptance/video-stage2-smoke.log")
rg 'VDOT_PASS|Difftest enabled|HIT GOOD TRAP|instrCnt' "$vdot_smoke/run.log"
sleep 4
printf '\n$ bash scripts/run_rtl.sh register_test\n'
bash "$vdot_root/scripts/run_rtl.sh" register_test > "$vdot_acceptance/video-stage2-register.log" 2>&1
cat "$vdot_acceptance/video-stage2-register.log"
vdot_register=$(sed -n 's/^RTL evidence: //p' "$vdot_acceptance/video-stage2-register.log")
rg 'REGISTER_PASS|Difftest enabled|HIT GOOD TRAP|instrCnt' "$vdot_register/run.log"
sleep 4
clear
printf '以下回顾已完成的完整回归日志，不冒充本段重新运行：\n'
python3 - "$vdot_acceptance/acceptance.json" <<'PY'
import json,re,sys
from pathlib import Path
d=json.load(open(sys.argv[1]));print('验收源码提交：',d['source_project_head'])
for case in ('random','pipeline'):
 p=Path(d['rtl_runs'][case]);text=re.sub(r'\x1b\[[0-9;]*m','',(p/'run.log').read_text())
 print('\n'+case+': '+str(p))
 for line in text.splitlines():
  if any(key in line for key in ('VDOT_PASS','PIPELINE_PASS','HIT GOOD TRAP','instrCnt')): print(line)
 assert (p/'exit-status.txt').read_text().strip()=='0'
PY
printf '\n1000组随机含4000次合法vdot；流水压力含1664条vdot。\n'
printf '阶段二演示结束，实际原始日志和输入摘要随验收目录保留。\n'
sleep 7
