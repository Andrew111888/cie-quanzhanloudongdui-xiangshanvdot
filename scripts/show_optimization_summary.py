"""Print a compact, readable subset of the fully verified raw comparisons."""
import argparse,json,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('report',type=Path);a=p.parse_args()
e=json.loads((a.report/'evidence.json').read_text())
assert e['status']=='verified' and e['ab_inputs_identical']

def median(phase,kind,var,tu,dep):
 rows=e['runs'][phase][kind]['rows']
 values=[x[-1 if kind=='RVV' else -2] for x in rows if x[0]==var and x[1]==tu and (x[2]==dep and x[3]==512 if kind=='RVV' else x[2]==512)]
 assert len(values)==5
 return statistics.median(values)
print('每组预热后5次重复，下面展示512次/块的中位片段周期。')
print('scenario           before-dot  after-dot   faster-RVV  RVV/after')
for label,kind,tu,dep in [('independent TA','RVV',0,0),('independent TU','RVV',1,0),('true-chain TA','RVV',0,1),('true-chain TU','RVV',1,1),('memory TA','MEMORY',0,None),('memory TU','MEMORY',1,None)]:
 b=median('before',kind,2,tu,dep);c=median('after',kind,2,tu,dep);best=min(median('after',kind,v,tu,dep) for v in [0,1])
 print('%-17s %10d %10d %12d %10.3f'%(label,b,c,best,best/c))
print('\nTU独立寄存器前/后改善：%.3f倍。'%(median('before','RVV',2,1,0)/median('after','RVV',2,1,0)))
print('真实依赖链和含访存负载逐组报告，不能套用该寄存器收益。')
print('循环外初始化、循环与末尾存储的边界已披露；不是裸FU延迟。')
print('两条RVV候选均公开，选实测较快者；减少指令不保证周期下降。')
print('没有综合或功耗测量，不推断面积、频率或能效。')
