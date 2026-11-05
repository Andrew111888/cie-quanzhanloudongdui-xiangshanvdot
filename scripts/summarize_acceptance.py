"""Produce canonical final-result documents from completed clean acceptance."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('acceptance', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
acceptance_path = args.acceptance.resolve(strict=True)
acceptance = json.loads((acceptance_path / 'acceptance.json').read_text())
if acceptance['status'] != 'passed' or not acceptance['source_unchanged']:
    raise SystemExit('Cannot summarize an incomplete clean acceptance')
out = root / 'docs/results'
data = root / 'docs/data/clean'
figures = root / 'docs/figures'
for directory in (out, data, figures): directory.mkdir(parents=True, exist_ok=True)
source = json.loads((acceptance_path / 'source-after.json').read_text())
wave = json.loads((acceptance_path / 'wave-analysis/analysis.json').read_text())
pipeline = json.loads((acceptance_path / 'pipeline-analysis/pipeline-analysis.json').read_text())
runs = {name: Path(path) for name, path in acceptance['rtl_runs'].items()}


def plain(path):
    return re.sub(r'\x1b\[[0-9;]*m', '', path.read_text(errors='replace'))


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
    return digest.hexdigest()


def stats(directory):
    text = plain(directory/'run.log')
    if (directory/'exit-status.txt').read_text().strip()!='0' or 'HIT GOOD TRAP' not in text or 'Difftest enabled.' not in text:
        raise ValueError('Missing completed differential result: '+str(directory))
    match=re.search(r'instrCnt = ([\d,]+), cycleCnt = ([\d,]+)',text)
    return tuple(int(s.replace(',','')) for s in match.groups())


def identities(directory):
    return {Path(name).name:digest for digest,name in
            (line.split(maxsplit=1) for line in (directory/'artifacts.sha256').read_text().splitlines())}


raw_sources = {}
for name, directory in runs.items():
    stats(directory)
    raw_sources[str(directory/'run.log')] = sha(directory/'run.log')
reference = identities(runs['smoke'])
fault_directory=Path(next(s.removeprefix('Fault-check evidence: ') for s in
                         (acceptance_path/'fault-check.log').read_text().splitlines()
                         if s.startswith('Fault-check evidence: ')))
fault=json.loads((fault_directory/'detected-mismatch.json').read_text())
if (fault['reference'],fault['dut'],fault['exit_status']) != (9,8,1):
    raise SystemExit('Missing exact vector comparator counterexample')
mapping = {'benchmark.csv':acceptance_path/'performance.csv',
           'wave-events.csv':acceptance_path/'wave-analysis/events.csv',
           'flush-events.csv':acceptance_path/'pipeline-analysis/pipeline-events.csv',
           'burst-throughput.csv':acceptance_path/'pipeline-analysis/burst-throughput.csv'}
for name, path in mapping.items():
    old=path.read_bytes();normalized=old.replace(b'\r\n',b'\n')
    if list(csv.reader(old.decode().splitlines()))!=list(csv.reader(normalized.decode().splitlines())):
        raise ValueError('CSV normalization changed values')
    (data/name).write_bytes(normalized)
for name in ('vadd-timeline.svg','latency-timeline.svg'):
    shutil.copyfile(acceptance_path/'wave-analysis'/name,figures/('clean-'+name))
provenance={'status':'completed_clean_acceptance','tested_project_head':source['project_head'],
            'acceptance_directory':str(acceptance_path),'acceptance_sha256':sha(acceptance_path/'acceptance.json'),
            'repositories':{name:{'head':item['head'],'changed_source_sha256':item['changed_source_sha256']}
                            for name,item in source['repositories'].items()},
            'emu_sha256':reference['emu'],
            'reference_sha256':reference['riscv64-nemu-interpreter-so'],
            'raw_log_sha256':raw_sources,
            'csv_sha256':{name:sha(data/name) for name in mapping},
            'fst_sha256':{'vadd':wave['vadd_source']['fst_sha256'],
                          'latency':wave['latency_source']['fst_sha256'],
                          'pipeline':pipeline['metadata']['fst_sha256']}}
(data/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
common=(f'实际干净构建/验收的作品源码提交：`{source["project_head"]}`。'
        '最终作品提交由发布包的source-binding.json给出；处理器、NEMU、工作负载、配置与分析输入逐字节一致，后续文档/演示工具差异单独记录。\n\n'
        f'单核MinimalConfig，VLEN=128，真实NEMU差分开启。emu SHA256：`{reference["emu"]}`；'
        f'正常REF SHA256：`{reference["riscv64-nemu-interpreter-so"]}`。\n\n')
vadd=wave['vadd'];events=vadd['events'];rename=vadd['renames'][0]
table=['| 环节 | FST上升沿序号 | 关联 |','|---|---:|---|']
for kind,label in [('decode','译码'),('rename','重命名'),('issue','发射'),('fu_in','FU输入'),
                   ('fu_out','FU结果'),('writeback','控制写回'),('preg_write','物理向量写入'),('commit','ROB提交')]:
    es=[e for e in events if e['kind']==kind]
    if len(es)!=1:raise ValueError('Ambiguous vadd stage '+kind)
    table.append(f'| {label} | {es[0]["edge"]} | '+(f'PC={vadd["pc"]:#x}' if kind=='decode' else
                 f'ROB=({vadd["rob_flag"]},{vadd["rob_value"]})，P={rename["pdest"]}')+' |')
pristine_root=acceptance_path.parents[1]
pristine_run=Path((pristine_root/'reports/pristine-vadd-evidence.txt').read_text().strip())
pristine_identity=identities(pristine_run)
stage1=('# 阶段一：环境与向量加法最终结果\n\n'+common+
        '独立检出先完成未修改香山/NEMU的全量构建与标准向量vadd，再应用补丁并从空硬件生成目录重建扩展核。'
        '复用固定外部工具与下载缓存，不复制开发目录的RTL、C++或模拟器；这不是全新操作系统验证。\n\n'
        f'原核emu SHA256：`{pristine_identity["emu"]}`。原核vadd目录：`{pristine_run}`；'
        f'扩展核vadd目录：`{runs["vadd"]}`。两者均有VADD_PASS、Difftest启用、GOOD TRAP和原始退出0。\n\n'
        f'目标编码0x02850657，PC={vadd["pc"]:#x}，配置SEW=8、VL=16、LMUL=1。'
        '完整128位实测结果为34302c2824201c1814100c080400fcf8。\n\n'+'\n'.join(table)+
        '\n\n![干净扩展核实际握手](../figures/clean-vadd-timeline.svg)\n\n'
        f'同PC译码尝试的边沿为{wave["vadd_decode_attempt_edges"]}，按实际提交反向选择对应重命名并限定ROB动态区间，不能仅用重用的物理目的拼接。'
        '叶FU入口的ROB取自同拍父Exu接收入口，不借用延后ctrlPipe。边沿序号在采集内计数、上升沿前采样，不是cycle CSR或物理频率。\n\n'
        '完整部署命令、固定版本、失败修复与资源参数见构建文档和证明材料包operation-logs/build-history。'
        '原始环境输出包含赛题所需团队和本机IP；公开录屏只省略IP展示，原始日志仍留在证明材料中。\n')
smoke_stats=stats(runs['smoke']);random_stats=stats(runs['random']);pipeline_stats=stats(runs['pipeline'])
random_text=plain(runs['random']/'run.log');register_text=plain(runs['register']/'run.log')
assert 'VDOT_PASS random_cases=1000 directed_cases=6 modes=5 illegal_cases=7' in random_text
assert 'REGISTER_PASS cases=8' in register_text
case=pipeline['cases'][0]
case_rows=['| 控制事件 | 边沿 | 身份 |','|---|---:|---|']
for key,label in [('branch_rename','分支重命名'),('wrong_rename','错路vdot重命名'),('wrong_input','错路FU输入'),
                  ('wrong_output','错路结果/写回'),('redirect','较老分支冲刷'),('correct_rename','正路vdot重命名'),
                  ('correct_commit','正路vdot提交')]:
 e=case[key];case_rows.append(f'| {label} | {e["edge"]} | ROB=({e.get("rob_flag")},{e.get("rob_value")})'+
                             (f'，P={e["pdest"]}' if 'pdest' in e else '')+' |')
stage2=('# 阶段二：整核功能与流水验证最终结果\n\n'+common+
        '采用低8个有符号int8乘积求和，低32位补码、高96位清零的暂定契约；支持域SEW8/VLEN128/LMUL1/VL8/vstart0/vm1。'
        '已向官方Issue #126询问范围、布局、版本和编码，尚未视为官方确认。\n\n'
        '| 检查 | 实际通过内容 |\n|---|---|\n'
        '| 基础输入 | 1/1→8，-1/1→-8，-128/-128→131072，-128/127→-130048，127/127→129032，0/-128→0 |\n'
        '| 5种模式 | 独立目标、vd=vs1、vd=vs2、两源相同、等价向量基线；两源相同时黄金值改为A·A |\n'
        '| 异常 | SEW16、LMUL2、VL7、VL0、vstart1、LMUL1/2、vm0；目标/vstart保持及mtval，随后普通非法0x7b |\n'
        '| 随机 | 固定种子20261104，1000组×5模式，4000次合法随机vdot和1000次等价基线 |\n'
        '| 寄存器边界 | v0/v31及两源/目的重叠，8种组合，完整结果与非目标寄存器保持 |\n'
        '| 流水压力 | 种子20261105，64组、1664条vdot，不同目的8连发、vadd生产者、16次真依赖链和两种分支 |\n\n'
        f'smoke实际{smoke_stats[0]}条指令/{smoke_stats[1]}周期；完整随机{random_stats[0]}条指令/{random_stats[1]}周期；'
        f'流水压力{pipeline_stats[0]}条指令/{pipeline_stats[1]}周期，均原始退出0、完成标记、GOOD TRAP、真实差分无差异。\n\n'
        'C黄金模型逐个检查完整128位结果；NEMU独立执行；独立Python参考模型及Chisel/Verilator数据通路另行验证。'
        '独立使能压力不能替代整核，实际整核目录由provenance.json和证明包列出。\n\n'
        f'补充诊断FST实测{len(pipeline["cases"])}条已完成物理写回、随后被较老分支冲刷且未提交的vdot。第一例如下：\n\n'+
        '\n'.join(case_rows)+'\n\n'
        '匹配同时使用PC、ROB分配到槽复用的动态区间及物理目的；正路可能复用同一物理寄存器，不能据此把两条指令串为一条。'
        '完整压力程序另验证未选目标保持哨兵。\n\n'
        '诊断采集故意在28000周期停止，正常验收器拒绝其功能PASS；仅在与完整压力运行4项输入摘要一致后用于波形分析。'
        '观察到vdot译码/重命名反压，未观察到FU输出反压或冲刷恰在两级算术内部，不将这些具体时序计入覆盖。\n')
perf=(acceptance_path/'performance.md').read_text()
perf=perf.replace('# RTL 性能结果','# 程序片段的60条RTL样本')
pairs=wave['fu_pairs'];fu_rows=['| 算术及微操作 | P | 输入边沿 | 结果边沿 | 周期 |','|---|---:|---:|---:|---:|']
for name in ('multiply','reduce','vdot'):
 for p in pairs[name]:fu_rows.append(f'| {name} uop{p["uop"]} | {p["pdest"]} | {p["input_edge"]} | {p["output_edge"]} | {p["cycles"]} |')
stage3=('# 阶段三：协同仿真与实测性能最终结果\n\n'+common+
        'Difftest启用全部32个128位向量寄存器和7项向量CSR比较，NEMU导出前缀1400字节；未修改checker、跳过规则或结果同步策略。'
        '未跳过vdot提交后参考模型独立推进，再比较完整架构向量状态。\n\n'
        '故障库在独立源码副本中仅将结果低位异或1，正常源码与正常库不改写；同一emu/smoke/flash依次运行正确→错误→恢复。'
        '负例实际字段为v12_low，REF=9、DUT=8，ABORT且原始退出1；提交历史同时要求首个02a4060b为未跳过、非delayed的v12写入。\n\n'
        f'负例首条vdot提交PC为0x{fault["first_vdot_commit_pc"]}。差异日志：\n\n```text\n{fault["observed_line"]}\n```\n\n'
        '差异行的诊断PC不保证是vdot地址，不能混淆。恢复正常库后smoke通过，输入SHA256不变。\n\n'
        '异常契约v2：后期配置检查cause2/xtval0；非零vstart由译码拒绝、xtval为指令位。NEMU仅消费一次自定义非架构标志，普通非法0x7b保持原报告；没有关闭TVAL或豁免比较。\n\n'+perf+'\n'
        '基线用vwmul生成16位有符号乘积、vwredsum扩宽归约到32位，预先清零高96位。两路径输入、目标布局、内存条件和测量边界一致；'
        '每种长度32/128/512预热后重复5次，区分真结果依赖和无显式结果依赖。波形关闭。\n\n'
        '基线逐次完成清零和配置恢复，未测量跨迭代复用已清零目标等循环优化，也未穷举最优RVV序列。'
        '加速比仅相对此处公开的等价组合，不推广为所有软件实现的最佳加速比。\n\n'
        'vdot循环使用ta/ma，原有派发/发射逻辑可消除通用旧vd源等待；本实现没有专门删除该源。'
        '基线按算法切换SEW和tu/mu以保证完整结果布局，末尾恢复相同vtype；该片段结果不能推广到所有tu/mu配置。\n\n'
        '## 实际算术路径与独立突发吞吐\n\n'+'\n'.join(fu_rows)+'\n\n'
        f'此次等价基线首个乘法接收到最终归约结果为{wave["baseline_input_to_final_result_cycles"]}周期，含配置、清零及依赖调度；'
        f'vdot输入至结果为{wave["vdot_input_to_result_cycles"]}周期。归约uop0写内部临时物理目的，uop1才写v12完整结果8，不能把部分和当作最终结果。\n\n'
        '![实际算术路径](../figures/clean-latency-timeline.svg)\n\n'
        f'另有{len(pipeline["independent_bursts"])}组×8条独立vdot的输入和输出连续逐周期握手，逐条核对实际两源的黄金和、完整128位结果、ROB、P与提交。'
        '这些突发的实测接收/输出间隔为1周期，不代表任意负载的持续吞吐上限。片段周期不能称为FU延迟。\n\n'
        '实现融合乘法/归约并减少SEW配置和结果整理，复用VIMac槽位，与普通向量乘法竞争资源。'
        '未部署LLM或推荐模型，没有综合、时序、面积或功耗数据，不声称端到端应用、面积、频率或能效收益。\n')
for name,value in [('stage1-clean.md',stage1),('stage2-clean.md',stage2),('stage3-clean.md',stage3)]:
    (out/name).write_text(value)
(root/'docs/FINAL_RESULTS.md').write_text('# 干净检出完整验收\n\n'
    '下列报告全部来自已完成的独立检出验收。最终源码与实际构建提交通过发布包source-binding.json连接，不改写原始证据身份。\n\n'
    '- [阶段一：环境与向量加法](results/stage1-clean.md)\n'
    '- [阶段二：整核功能与流水](results/stage2-clean.md)\n'
    '- [阶段三：协同仿真与性能](results/stage3-clean.md)\n'
    '- [原始数据与来源摘要](data/clean/provenance.json)\n\n'
    '赛题未明确语义仍按contract.json暂定解释披露，官方问题见QUESTIONS.md；不将工程验收通过表述为官方评审通过。\n')
print('CLEAN_ACCEPTANCE_DOCUMENTS_CREATED',out)
