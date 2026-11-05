"""Compare unchanged workloads on preserved and optimized RTL simulators."""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import re
import statistics

parser = argparse.ArgumentParser()
parser.add_argument('--before-rvv', type=Path, required=True)
parser.add_argument('--before-memory', type=Path, required=True)
parser.add_argument('--after-rvv', type=Path)
parser.add_argument('--after-memory', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if bool(args.after_rvv) != bool(args.after_memory):
    raise SystemExit('Provide both after runs, or neither.')
args.output.mkdir(parents=True, exist_ok=False)


def load(directory, kind):
    text = re.sub(r'\x1b\[[0-9;]*m', '', (directory / 'run.log').read_text(errors='replace'))
    marker = 'RVV_BENCH_PASS' if kind == 'RVV' else 'MEMORY_DOT_PASS'
    if (directory / 'exit-status.txt').read_text().strip() != '0' or marker not in text:
        raise ValueError('Incomplete run: ' + str(directory))
    if 'Difftest enabled.' not in text or 'HIT GOOD TRAP' not in text:
        raise ValueError('Missing real RTL/Difftest completion.')
    if re.search(r'ABORT|different at pc|BAD TRAP|CRITICAL ERROR|EXCEEDING CYCLE', text):
        raise ValueError('Failed RTL run: ' + str(directory))
    rows = [tuple(map(int, line.split(',')[1:])) for line in text.splitlines() if line.startswith(kind + ',')]
    expected = set(itertools.product(range(3), range(2), range(2), (32,128,512), range(5))) if kind == 'RVV' else set(itertools.product(range(3), range(2), (32,128,512), range(5)))
    identities = [row[:-1] if kind == 'RVV' else row[:-2] for row in rows]
    if len(identities) != len(set(identities)) or set(identities) != expected:
        raise ValueError('Missing or duplicated measurements.')
    if any(row[-1 if kind == 'RVV' else -2] <= 0 for row in rows):
        raise ValueError('Nonpositive elapsed cycles.')
    if kind == 'MEMORY':
        for length in (32,128,512):
            checksums = {row[-1] for row in rows if row[2] == length}
            if len(checksums) != 1:
                raise ValueError('Memory paths produced different checksums.')
    digests = {}
    for line in (directory / 'artifacts.sha256').read_text().splitlines():
        digest, path = line.split(maxsplit=1)
        data = Path(path).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Run input changed: ' + path)
        digests[Path(path).name] = digest
    return rows, digests


def summary(rows, kind):
    grouped = {}
    for row in rows:
        key = row[:-2] if kind == 'RVV' else row[:-3]
        grouped.setdefault(key, []).append(row[-1] if kind == 'RVV' else row[-2])
    return {key: (statistics.median(values), min(values), max(values)) for key, values in grouped.items()}


records = {}
for phase, rvv, memory in [('before', args.before_rvv, args.before_memory), ('after', args.after_rvv, args.after_memory)]:
    if rvv is None:
        continue
    records[phase] = {}
    for kind, directory in [('RVV', rvv), ('MEMORY', memory)]:
        rows, hashes = load(directory, kind)
        records[phase][kind] = {'directory': str(directory), 'rows': rows, 'hashes': hashes, 'summary': summary(rows, kind)}
        header = ['variant','tail_undisturbed','dependent','iterations','repeat','cycles'] if kind == 'RVV' else ['variant','tail_undisturbed','blocks','repeat','cycles','checksum']
        with (args.output / f'{phase}-{kind.lower()}.csv').open('w') as stream:
            writer = csv.writer(stream, lineterminator='\n'); writer.writerow(header); writer.writerows(rows)
if 'after' in records:
    for kind in ('RVV','MEMORY'):
        left, right = records['before'][kind]['hashes'], records['after'][kind]['hashes']
        for name in left.keys() | right.keys():
            if name != 'emu' and left.get(name) != right.get(name):
                raise ValueError('A/B workload/reference/flash inputs differ: ' + name)

lines = ['# 优化与性能对照', '',
         '所有数据均来自真实RTL/NEMU差分。寄存器基准包含循环和最终存储；内存内核包含逐块输入加载、计算及完整128位输出存储。两者均为预热后的测量，不是裸功能单元延迟。', '',
         'variant 0：每轮清零并切换配置的原等价序列；variant 1：预先清零目标和独立零种子，循环复用；variant 2：vdot。独立输入的前8项为混合符号，真实依赖链初值只在低32位含四个1，后续结果为4，其他位清零。每个结果均在程序中检查完整128位。', '',
         '内存内核每块两源各加载8字节（源块间距16字节），写回16字节结果，包含正负边界与固定种子随机数据，每块与独立C黄金值逐项核对。容量为32/128/512块，对应有效点积输入256/1024/4096项；不宣称冷缓存或整模型性能。', '']
for phase, record in records.items():
    lines += [f'## {phase}：相对两种等价RVV序列', '', '| 场景 | tu | 真依赖 | 长度 | 原基线 | 优化基线 | vdot | 优化基线/vdot |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for kind, scenario in [('RVV','寄存器'),('MEMORY','含访存')]:
        for tu in (0,1):
            for dependent in ((0,1) if kind == 'RVV' else (None,)):
                for length in (32,128,512):
                    def value(variant):
                        key = (variant,tu,dependent,length) if kind == 'RVV' else (variant,tu,length)
                        return record[kind]['summary'][key][0]
                    a,b,c = (value(v) for v in range(3))
                    lines.append(f'| {scenario} | {tu} | {dependent if dependent is not None else "逐块独立"} | {length} | {a:g} | {b:g} | {c:g} | {b/c:.3f} |')
if 'after' in records:
    lines += ['', '## 旧目标依赖消除前后', '', '| 场景 | tu | 真依赖 | 长度 | before vdot | after vdot | before/after |', '|---|---:|---:|---:|---:|---:|---:|']
    for kind, scenario in [('RVV','寄存器'),('MEMORY','含访存')]:
        for key, before in sorted(records['before'][kind]['summary'].items()):
            if key[0] != 2:
                continue
            after = records['after'][kind]['summary'][key]
            _,tu,*rest = key
            dependent,length = rest if kind == 'RVV' else ('逐块独立',rest[0])
            lines.append(f'| {scenario} | {tu} | {dependent} | {length} | {before[0]:g} | {after[0]:g} | {before[0]/after[0]:.3f} |')
lines += ['', '完整范围（min/max）、180条寄存器样本与90条内存样本分别保留在CSV中。不同TU、依赖或输入布局不能跨组相除。没有综合或功耗证据时，不据周期结果推断面积、频率或能效。', '']
(args.output / 'report.md').write_text('\n'.join(lines))
serializable = {phase:{kind:{k:v for k,v in item.items() if k != 'summary'} for kind,item in record.items()} for phase,record in records.items()}
(args.output / 'evidence.json').write_text(json.dumps({'status':'verified','ab_inputs_identical': 'after' in records,'runs':serializable},indent=2)+'\n')
print('OPTIMIZATION_REPORT_VERIFIED', args.output / 'report.md')
