"""Plot measured fragment speed ratios from a completed RTL benchmark."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

parser=argparse.ArgumentParser()
parser.add_argument('--benchmark',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
data=json.loads(args.benchmark.read_text())
assert data['status']=='passed' and data['difftest_enabled']
assert data['long_sample_count']==60 and data['chain_sample_count']==120
long=sorted(data['long_comparisons'],key=lambda row:row['k'])
chains=sorted((row for row in data['chain_comparisons'] if row['rounds']==512),key=lambda row:row['chains'])
fig,axes=plt.subplots(1,2,figsize=(10.3,3.5),layout='constrained')
axes[0].plot(range(3),[r['rvv_over_acc'] for r in long],marker='o',color='#17609b',label='Faster RVV / fused')
old=[r['old_vdot_over_acc'] for r in long]
axes[0].plot(range(3),old,marker='s',color='#bc6433',label='Original dot + add / fused')
axes[0].set(xticks=range(3),xticklabels=[str(r['k']) for r in long],xlabel='K elements',title='Loaded long dot product')
axes[1].plot(range(4),[r['dot_plus_add_over_acc'] for r in chains],marker='o',color='#17609b')
axes[1].set(xticks=range(4),xticklabels=[str(r['chains']) for r in chains],xlabel='Independent accumulator chains',title='Preloaded register loop, 512 rounds')
for ax in axes:
    ax.axhline(1,color='#58616b',linestyle='--',linewidth=1)
    ax.set_ylabel('Baseline median cycles / fused median cycles')
    ax.set_ylim(bottom=0)
    ax.grid(axis='y',alpha=.2)
    ax.spines[['top','right']].set_visible(False)
axes[0].legend(frameon=False,fontsize=8)
target=root/'docs/figures/acc-fragment-ratios.png'
fig.savefig(target,dpi=200,facecolor='white',metadata={'Software':'全栈漏洞队'})
plt.close(fig)
sidecar={'status':'verified','scope':'measured complete fragments, five-repeat medians; unitless ratios, not bare FU latency','input_sha256':hashlib.sha256(args.benchmark.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
target.with_suffix('.json').write_text(json.dumps(sidecar,ensure_ascii=False,indent=2)+'\n')
print(target)
