#!/usr/bin/env bash
# Record with record_terminal.py; this executes the preserved pristine core.
set -euo pipefail
source "$(dirname -- "$0")/env.sh"
vdot_repro=${VDOT_REPRO_ROOT:-/home/yh/cie/vdot-kmhv2-repro-20261105}
vdot_demo="$VDOT_ROOT/reports/demo-stage1-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$vdot_demo"
printf '\n阶段一：未修改香山原核的真实向量加法演示\n'
printf '队伍：全栈漏洞队；显示本机实际命令，不回放测试结果。\n\n'
printf '$ git -C <clean-XiangShan> rev-parse HEAD\n'
git -C "$vdot_repro/third_party/XiangShan" rev-parse HEAD
printf '\n此前已完成的原核构建：CHIRRTL -> firtool -> Verilator/C++。\n'
printf '这里展示保存产物的摘要；本段不重新进行全量构建。\n'
(cd "$vdot_repro" && sha256sum --check reports/pristine-preserved.sha256)
printf '\n源代码在随后扩展复现中已应用补丁；本次运行下面单独保存的原核产物。\n'
vdot_command=("$vdot_repro/build/pristine/emu" \
  -i "$vdot_repro/build/pristine/vadd_test.bin" \
  -F "$vdot_repro/build/pristine/flash.bin" --ram-size=128MB \
  "--diff=$vdot_repro/build/pristine/reference.so" --no-squash -C 100000 \
  --dump-wave-full -b 0 -e 10000 "--wave-path=$vdot_demo/wave.fst")
printf '\n$ '; printf '%q ' "${vdot_command[@]}"; printf '\n\n'
/usr/bin/time -v -o "$vdot_demo/time.txt" "${vdot_command[@]}" \
  > "$vdot_demo/run-original.log" 2>&1
printf '0\n' > "$vdot_demo/exit-status.txt"
# Retain the exact original privately and label the display-only IP omission.
python3 - "$vdot_demo/run-original.log" <<'PY'
from pathlib import Path
import re,sys
text=Path(sys.argv[1]).read_text(errors='replace')
text=re.sub(r'(?m)^(hello xiangshan, I am [^,\r\n]+), [^\r\n]+',
            r'\1, <本机IP在原始日志中；公开画面省略>', text)
print(text)
PY
python3 "$VDOT_ROOT/scripts/check_run.py" "$vdot_demo/run-original.log" VADD_PASS
printf '\n从刚生成的真实FST提取接口握手；采样为后端上升沿之前。\n'
python3 "$VDOT_ROOT/scripts/extract_wave_events.py" "$vdot_demo/wave.fst" --output "$vdot_demo/events"
python3 - "$vdot_demo/events/events.json" <<'PY'
import json,sys
a=json.load(open(sys.argv[1]));pc=0x80000118
c=[e for e in a if e['kind']=='commit' and e.get('pc')==pc]
assert len(c)==1;c=c[0];tag=c['rob_flag'],c['rob_value']
ren=[e for e in a if e['kind']=='rename' and e.get('pc')==pc
     and (e.get('rob_flag'),e.get('rob_value'))==tag and e['edge']<=c['edge']]
r=max(ren,key=lambda e:e['edge']);p=r['pdest']
print('PC=0x80000118, instruction=0x02850657, ROB=%s, P=%s'%(tag,p))
for kind in ('rename','issue','fu_in','fu_out','writeback','commit'):
 es=[e for e in a if e['kind']==kind and r['edge']<=e['edge']<=c['edge']
     and (e.get('rob_flag'),e.get('rob_value'))==tag and e.get('pdest')==p]
 assert len(es)==1,(kind,len(es));e=es[0]
 print('%-12s edge=%s  %s'%(kind,e['edge'],e['source']))
 if 'data' in e:
  assert e['data']==int('34302c2824201c1814100c080400fcf8',16)
  print('  result=%032x'%e['data'])
print('实际结果正确；按同一ROB及物理目的跟踪，不拼接早先投机执行。')
PY
printf '\n阶段一演示完成。完整原始日志、FST与命令保存在：\n%s\n' "$vdot_demo"
printf '全部赛题交付还需扩展核干净复现及其他阶段材料。\n'
sleep 5
