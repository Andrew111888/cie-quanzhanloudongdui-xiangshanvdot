"""Plot the archived GEMV samples and the operand-isolation activity counts."""
import csv
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager, pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
latin = next((p for p in (ROOT / 'reports/checklist-format/fonts').glob('*')
              if p.name.lower() == 'times.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'))
for path in (latin,
             Path('/usr/share/fonts/truetype/arphic/uming.ttc')):
    if path.exists():
        font_manager.fontManager.addfont(str(path))
plt.rcParams.update({
    'font.family': ['Times New Roman', 'AR PL UMing CN'],
    'font.size': 11, 'svg.fonttype': 'path', 'svg.hashsalt': 'vdot-architecture',
    'axes.spines.top': False, 'axes.spines.right': False,
    'xtick.direction': 'in', 'ytick.direction': 'in',
    'axes.unicode_minus': False,
})
summary = json.loads((ROOT / 'docs/data/架构补充验证.json').read_text())
with (ROOT / 'docs/data/GEMV周期.csv').open() as stream:
    samples = list(csv.DictReader(stream))

def cycles(variant, m, k):
    return [int(row['cycles']) for row in samples
            if (int(row['variant']), int(row['m']), int(row['k'])) == (variant, m, k)]

fig, ax = plt.subplots(figsize=(7.0, 2.8), constrained_layout=True)
for m, marker, style in ((1, 'o', '-'), (4, 's', '--'), (8, '^', '-.')):
    medians, lows, highs = [], [], []
    for k in (32, 128, 512):
        baseline = min((1, 2), key=lambda variant: statistics.median(cycles(variant, m, k)))
        rvv, acc = cycles(baseline, m, k), cycles(3, m, k)
        ratio = statistics.median(rvv) / statistics.median(acc)
        expected = next(row['rvv_over_acc'] for row in summary['gemv']['comparisons']
                        if row['m'] == m and row['k'] == k)
        assert abs(ratio - expected) < 1e-12
        medians.append(ratio)
        lows.append(ratio - min(rvv) / max(acc))
        highs.append(max(rvv) / min(acc) - ratio)
    ax.errorbar(range(3), medians, yerr=[lows, highs], color='black', marker=marker,
                linestyle=style, capsize=3, label=f'M={m}')
ax.axhline(1, color='0.55', linestyle=':', linewidth=1)
ax.set_xticks(range(3), ['32', '128', '512'])
ax.set_xlabel('点积长度 K / 对')
ax.set_ylabel('周期比 RVV / vdot.acc')
ax.set_ylim(.4, 1.55)
ax.legend(ncol=3, loc='upper right', frameon=False)
ax.annotate('1.412', xy=(0, 274 / 194), xytext=(.18, 1.44), fontsize=10)
fig.savefig(ROOT / 'docs/figures/gemv-measured-ratios.svg', metadata={'Date': None, 'Creator': '全栈漏洞队'})
plt.close(fig)

modes = summary['operand_isolation']['modes']
fig, ax = plt.subplots(figsize=(7.0, 2.8), constrained_layout=True)
positions = list(range(len(modes)))
original = [row['baseline_stage1'] / 1000 for row in modes]
isolated = [row['isolated_stage1'] / 1000 for row in modes]
left = ax.bar([x - .19 for x in positions], original, width=.36,
              facecolor='0.85', edgecolor='black', label='原路径')
right = ax.bar([x + .19 for x in positions], isolated, width=.36,
               facecolor='white', edgecolor='black', hatch='///', label='隔离候选')
for bars in (left, right):
    ax.bar_label(bars, fmt='%.1f', padding=3, fontsize=9)
ax.set_xticks(positions, ['连续点积', '点积与气泡\n停顿、清空', '约25%点积\n混合流', '突发点积\n混合流'])
ax.set_ylabel('一级寄存器位翻转 / 千次')
ax.set_ylim(0, 1320)
ax.legend(ncol=2, loc='upper right', frameon=False)
fig.savefig(ROOT / 'docs/figures/isolation-stage1-activity.svg', metadata={'Date': None, 'Creator': '全栈漏洞队'})
plt.close(fig)
print('Generated two figures from archived measurements')
