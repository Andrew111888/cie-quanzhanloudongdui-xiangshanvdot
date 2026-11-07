"""Draw design diagrams and archived verification/PPA result figures."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager, pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
fonts = ROOT / 'reports/checklist-format/fonts'
latin = next((p for p in fonts.glob('*') if p.name.lower() == 'times.ttf'),
             Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'))
for path in (latin, Path('/usr/share/fonts/truetype/arphic/uming.ttc')):
    if path.exists():
        font_manager.fontManager.addfont(str(path))
plt.rcParams.update({'font.family': ['Times New Roman', 'AR PL UMing CN'],
                     'font.size': 11, 'svg.fonttype': 'path', 'svg.hashsalt': 'vdot-evidence',
                     'axes.unicode_minus': False, 'xtick.direction': 'in', 'ytick.direction': 'in'})

def save(fig, name):
    fig.savefig(ROOT / 'docs/figures' / name, bbox_inches='tight',
                metadata={'Date': None, 'Creator': '全栈漏洞队'})
    plt.close(fig)

def box(ax, x, y, text, width=2.1, height=.9):
    ax.add_patch(FancyBboxPatch((x, y), width, height, boxstyle='round,pad=0.04',
                               facecolor='white', edgecolor='black', linewidth=1))
    ax.text(x + width/2, y + height/2, text, ha='center', va='center')

def arrow(ax, start, end, label=''):
    ax.annotate('', end, start, arrowprops={'arrowstyle': '->', 'color': 'black'})
    if label:
        ax.text((start[0]+end[0])/2, (start[1]+end[1])/2+.1, label, ha='center', va='bottom', fontsize=10)

fig, ax = plt.subplots(figsize=(7.1, 3.3))
ax.set(xlim=(0, 10), ylim=(0, 4.4)); ax.axis('off')
for y, title, source, formula in ((2.7, '普通 vdot.vv', 'vs1、vs2\n第三源 SrcType.no', 'dot(vs1, vs2)'),
                                   (.5, '累加 vdot.acc', 'vs1、vs2、old vd\n第三源 SrcType.vp', 'old vd[31:0] + dot')):
    ax.text(.1, y+1.15, title, fontweight='bold')
    box(ax, .1, y, source, 3, .9)
    box(ax, 4.1, y, '同一共享点积\n累加数据通路', 2.5, .9)
    box(ax, 7.7, y, formula+'\n高96位清零', 2.1, .9)
    arrow(ax, (3.1,y+.45),(4.1,y+.45))
    arrow(ax, (6.6,y+.45),(7.7,y+.45))
ax.text(4.8,2.2,'普通点积累加输入取0；累加指令保留旧目标真实依赖',ha='center',fontsize=10)
save(fig, 'vdot-source-dependencies.svg')

fig, ax = plt.subplots(figsize=(7.1, 3.1))
ax.set(xlim=(0, 10), ylim=(0, 4)); ax.axis('off')
box(ax,.1,2.5,'输入请求\nvalid、dot标签',2.0,.8)
box(ax,3.0,2.5,'点积输入\n真实源 / 置零',2.1,.8)
box(ax,6.0,2.5,'一级数据寄存器\n使能 E1',2.0,.8)
box(ax,8.7,2.5,'结果\nE2',1.1,.8)
arrow(ax,(2.1,2.9),(3,2.9));arrow(ax,(5.1,2.9),(6,2.9));arrow(ax,(8,2.9),(8.7,2.9))
box(ax,3.0,.8,'E1 = accept && in_dot',3.0,.8)
box(ax,6.7,.8,'E2 = move && dot1',3.0,.8)
arrow(ax,(4.5,1.6),(7,2.5));arrow(ax,(8.2,1.6),(9.2,2.5))
ax.text(.1,.2,'dot1随一级有效标签推进；输出停顿保持，清空取消在途请求',fontsize=10)
save(fig, 'isolation-stage-enables.svg')

summary=json.loads((ROOT/'docs/data/验证摘要.json').read_text())
fig, (ax, right) = plt.subplots(1,2,figsize=(8.0,3.2),gridspec_kw={'width_ratios':[1.6,1]},constrained_layout=True)
ax.axis('off'); ax.set(xlim=(0,10),ylim=(0,6))
rows=[('基础正负与边界', f"{summary['basic_cases']}项，通过"),
      ('随机与寄存器关系', f"{summary['random_input_groups']}组、{summary['alias_modes']}种关系、TA/TU"),
      ('点积与32位回绕', f"{summary['legal_instruction_executions']}条，完整结果检查"),
      ('累加流水及别名链', f"{summary['pipeline_acc_instructions']}条，通过"),
      ('边界寄存器', 'v0/v31，通过'),
      ('非法配置及异常状态', f"{summary['exception_cases']}项，通过")]
for i,(label,result) in enumerate(rows):
    x=(i%2)*5.05
    y=4.15-(i//2)*1.85
    box(ax,x+.08,y,label+'\n'+result,4.75,1.25)
evidence=json.loads((ROOT/'docs/data/图证核对.json').read_text())['exception_reference_check']
conforming=[evidence['old_conforming'],evidence['corrected_conforming']]
different=[evidence['old_different'],0]
right.bar([0,1],conforming,color='white',edgecolor='black',label='符合异常契约')
right.bar([0,1],different,bottom=conforming,color='0.6',edgecolor='black',label='差异')
right.set(xticks=[0,1],xticklabels=['原参考','修正参考'],ylabel='参考语义检查 / 项',ylim=(0,61))
right.text(0,conforming[0]/2,str(conforming[0]),ha='center')
right.text(0,conforming[0]+different[0]/2,str(different[0]),ha='center')
right.text(1,conforming[1]/2,str(conforming[1]),ha='center')
right.legend(frameon=False,fontsize=9,loc='upper center')
save(fig,'verification-coverage.svg')

with (ROOT/'docs/data/资源时序.csv').open() as stream:
    rows=list(csv.DictReader(stream))
fig,(ax,right)=plt.subplots(1,2,figsize=(8.0,3.4),constrained_layout=True)
labels=['原点积','串接累加','CSA','前缀','提前压缩\n单元','提前压缩\n整核输出']
x=list(range(6));areas=[float(r['area_library_units']) for r in rows];slack=[float(r['setup_slack_1_5ns']) for r in rows]
ax.bar(x,areas,color='0.8',edgecolor='black');ax.set_ylabel('面积 / Liberty属性单位');ax.set_ylim(0,7000)
right.bar(x,slack,color='0.8',edgecolor='black');right.axhline(0,color='black',linewidth=.8)
right.set_ylabel('1.5 ns建立裕量 / ns');right.set_ylim(-.75,.55)
for axis in (ax,right):axis.set_xticks(x,labels,rotation=35,ha='right',fontsize=9)
for i,v in enumerate(areas):ax.text(i,v+80,f'{v:.0f}',ha='center',fontsize=8)
for i,v in enumerate(slack):right.text(i,v+(.025 if v>=0 else -.025),f'{v:+.3f}',ha='center',va='bottom' if v>=0 else 'top',fontsize=8)
save(fig,'arithmetic-area-timing.svg')
print('Generated four evidence figures')
