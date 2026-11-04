"""Summarize measured RTL cycle samples, never NEMU wall time/instruction counts."""
import argparse
import csv
import pathlib
import re
import statistics

parser = argparse.ArgumentParser()
parser.add_argument('log', type=pathlib.Path)
parser.add_argument('--engine', choices=['rtl'], required=True)
parser.add_argument('--output', type=pathlib.Path, required=True)
args = parser.parse_args()
text = re.sub(r'\x1b\[[0-9;]*m', '', args.log.read_text(errors='replace'))
rows = [[int(x) for x in m] for m in re.findall(r'^BENCH,(\d+),(\d+),(\d+),(\d+),(\d+)\s*$', text, re.M)]
if 'BENCH_PASS' not in text or len(rows) != 60:
    raise SystemExit('missing complete benchmark: expected 60 samples and BENCH_PASS')
groups = {}
for dep, base, count, repeat, cycles in rows:
    key = dep, base, count
    if repeat in groups.setdefault(key, {}): raise SystemExit('duplicate sample')
    if cycles <= 0: raise SystemExit('nonpositive cycle count')
    groups[key][repeat] = cycles
result = ['# RTL 性能结果', '', f'原始日志：{args.log}', '',
          '测量范围包含必要向量配置、循环与末尾结果存储，属于程序片段周期，不能解释为裸功能单元延迟。', '',
          '| 依赖链 | 迭代数 | 基线周期中位数（范围） | vdot周期中位数（范围） | 加速比 |',
          '|---|---:|---:|---:|---:|']
for dep in (0, 1):
    for count in (32, 128, 512):
        values = []
        for base in (1, 0):
            group = groups.get((dep, base, count), {})
            if set(group) != set(range(5)): raise SystemExit('missing repeat')
            data = list(group.values())
            values.append((statistics.median(data), min(data), max(data)))
        b, d = values
        result.append(f'| {"有" if dep else "无"} | {count} | {b[0]:g}（{b[1]}–{b[2]}） | {d[0]:g}（{d[1]}–{d[2]}） | {b[0]/d[0]:.3f} |')
args.output.write_text('\n'.join(result) + '\n')
with args.output.with_suffix('.csv').open('w') as file:
    writer = csv.writer(file)
    writer.writerow(['dependent','baseline','iterations','repeat','cycles'])
    writer.writerows(rows)
