"""Render five Chinese-named reports; keep execution logs as original files."""
import argparse
import hashlib
import html
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess
import textwrap

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle, Image, XPreformatted

parser = argparse.ArgumentParser()
parser.add_argument('--binding', type=Path, required=True)
parser.add_argument('--basic-run', type=Path, required=True)
parser.add_argument('--stage1-evidence', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
binding = json.loads(args.binding.read_text())
head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
assert binding['status'] == 'verified' and binding['final_project_head'] == head
for name, value in binding['tracked_file_sha256'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest() == value, name
basic = json.loads((args.basic_run/'cases.json').read_text())
assert basic['status'] == 'passed' and basic['source_unchanged'] and basic['difftest_enabled']
basic_text = re.sub(r'\x1b\[[0-9;]*m','',(args.basic_run/'run.log').read_text())
assert hashlib.sha256((args.basic_run/'run.log').read_bytes()).hexdigest() == basic['run_log_sha256']
case_output = '\n'.join(s for s in basic_text.splitlines() if s.startswith(('BASIC_CASE ', 'VDOT_BASIC_PASS')))
assert case_output.count('BASIC_CASE ') == 6
greet_log = args.stage1_evidence/'1.1-environment-validation/acceptance-run/run.log'
greeting = next(s for s in greet_log.read_text().splitlines() if s.startswith('hello xiangshan, I am '))
args.output.mkdir(parents=True, exist_ok=True)
temporary = root/'tmp/pdfs/requirements'
temporary.mkdir(parents=True,exist_ok=True)
for name, filename in [('Latin','DejaVuSans.ttf'),('Mono','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+filename))
pdfmetrics.registerFont(TTFont('CJK','/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'))
W = A4[0]-96
body = ParagraphStyle('body',fontName='Latin',fontSize=9.3,leading=14.7,spaceAfter=7,wordWrap='CJK')
cell = ParagraphStyle('cell',parent=body,fontSize=7.6,leading=11,spaceAfter=0)
reference_style = ParagraphStyle('reference',parent=body,fontSize=8.2,leading=12,spaceAfter=4)
h1 = ParagraphStyle('h1',parent=body,fontSize=18,leading=25,textColor=colors.HexColor('#163c56'),spaceBefore=10,spaceAfter=14,keepWithNext=True)
h2 = ParagraphStyle('h2',parent=h1,fontSize=13,leading=20,spaceBefore=13,spaceAfter=8)
h3 = ParagraphStyle('h3',parent=h1,fontSize=10.5,leading=17,spaceBefore=10,spaceAfter=6)
code = ParagraphStyle('code',parent=body,fontName='Mono',fontSize=7.1,leading=10.8,backColor=colors.HexColor('#f0f4f8'),borderPadding=7,spaceBefore=5,spaceAfter=12)

def mixed(s):
    return re.sub(r'([\u2e80-\ua4cf\uac00-\ud7ff\uf900-\ufaff\uff01-\uff60]+)',r'<font name="CJK">\1</font>',s)

def inline(s):
    s = html.escape(s.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-'))
    s = re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#17609b">\1</link>',s)
    s = re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',s)
    return mixed(s.replace('**','').replace('`',''))

def p(s,style=body):
    return Paragraph(inline(s),style)

def parse(path, content):
    content = content.replace('hello xiangshan, I am 全栈漏洞队, <本机IP>',greeting)
    content = content.replace('{{BASIC_CASE_OUTPUT}}',case_output)
    content = content.replace('<!-- LOCAL_ENVIRONMENT_IMAGE -->','![实际仿真输出画面](evidence:environment-output.png)')
    content = content.split('\n',1)[1]
    content = content.replace('\n队伍：全栈漏洞队。参赛单位：西安电子科技大学。\n','\n',1)
    assert '{{' not in content
    lines=content.splitlines(); out=[]; pending=[];i=0;reference_section=False
    def flush():
        if pending:
            text=' '.join(pending)
            footnote=reference_section or text.startswith('上述为原日志差异行按版面折行。')
            out.append(p(text,reference_style if footnote else body));pending.clear()
    while i<len(lines):
        s=lines[i]
        if not s.strip():flush();i+=1;continue
        if s.startswith('```'):
            flush();i+=1;parts=[]
            while i<len(lines) and not lines[i].startswith('```'):
                parts.extend(textwrap.wrap(lines[i],width=104,replace_whitespace=False,drop_whitespace=False) or ['']);i+=1
            out.append(XPreformatted(mixed(html.escape('\n'.join(parts))),code));i+=1;continue
        if s.startswith('|'):
            flush();rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cs=[x.strip() for x in lines[i].strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in cs):rows.append(cs)
                i+=1
            n=len(rows[0]);assert all(len(row)==n for row in rows)
            weights={2:[.85,2.1],3:[1.0,1.4,2.1],4:[1.2,.8,1.2,2],5:[1.4,.55,1.6,1.6,.6],6:[1.7,.4,.6,.75,.75,.6]}.get(n,[1]*n)
            if rows[0][0]=='观察事件':weights=[1.3,.5,.6,2.9]
            if rows[0][0].startswith('512次'):weights=[1.7,.8,.8,.8,.9]
            t=LongTable([[p(c,cell) for c in row] for row in rows],colWidths=[W*x/sum(weights) for x in weights],repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eef5')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f9fb')]),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#c8d5df')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            t.spaceAfter=10;out.append(t);continue
        im=re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)',s)
        if im:
            flush()
            source=(args.stage1_evidence/'1.1-environment-validation'/im[2].removeprefix('evidence:')) if im[2].startswith('evidence:') else path.parent/im[2]
            source=source.resolve(strict=True)
            if source.suffix=='.svg':
                png=temporary/(source.stem+'.png')
                subprocess.run(['/usr/bin/convert','-density','170','-background','white',str(source),str(png)],check=True)
                source=png
            pic=Image(str(source));scale=min(W/pic.imageWidth,290/pic.imageHeight)
            pic.drawWidth=pic.imageWidth*scale;pic.drawHeight=pic.imageHeight*scale
            out += [pic,p(im[1],cell),Spacer(1,10)];i+=1;continue
        if s.startswith('#'):
            flush();level=len(s)-len(s.lstrip('#'));out.append(p(s.lstrip('#').strip(),h1 if level==1 else h2 if level==2 else h3))
            reference_section=s.lstrip('#').strip()=='参考资料'
        elif s.startswith('- '):flush();out.append(p(s,reference_style if reference_section else body))
        else:pending.append(s)
        i+=1
    flush();return out

def footer(canvas,doc):
    canvas.setFont('Latin',8)
    canvas.drawCentredString(A4[0]/2,27,str(doc.page))

def split_at(content, marker):
    assert content.count(marker) == 1, marker
    before, after = content.split(marker, 1)
    return before.rstrip(), marker.lstrip('\n') + after

stage1 = (root/'docs/submission/stage1.md').read_text()
stage2 = (root/'docs/submission/stage2.md').read_text()
stage3 = (root/'docs/submission/stage3.md').read_text()
stage1_environment, stage1_remaining = split_at(stage1, '\n## 1.2 ')
_, stage1_process = split_at(stage1_remaining, '\n## 1.3 ')
stage1_process = stage1_environment + '\n\n' + stage1_process
stage2_design, stage2_tests = split_at(stage2, '\n## 2.3.1 ')
stage3_cosim, stage3_performance = split_at(stage3, '\n## 3.2 ')
stage3_cosim = stage3_cosim.replace(
    '\n\n原始正例、负例、恢复三份日志', '\n原始正例、负例、恢复三份日志', 1)

def document(title, content):
    if content.startswith('# '):
        return '# '+title+'\n'+content.split('\n',1)[1]
    return '# '+title+'\n\n队伍：全栈漏洞队。参赛单位：西安电子科技大学。\n\n'+content

documents = [
    (1, '一阶段过程文档', ['1.1','1.3'], document('一阶段过程文档', stage1_process)),
    (2, '二阶段设计文档', ['2.1','2.2'], document('二阶段设计文档', stage2_design)),
    (2, '二阶段基础测试文档', ['2.3.1','2.3.2','2.3.3'], document('二阶段基础测试文档',
     '测试配置为SEW=8、VLEN=128、LMUL=1、VL=8、vstart=0、vm=1。两源低8对有符号int8相乘求和，结果存入目标低32位，高96位清零。\n\n'+stage2_tests)),
    (3, '三阶段协同仿真文档', ['3.1.1','3.1.2'], document('三阶段协同仿真文档', stage3_cosim)),
    (3, '三阶段性能分析文档', ['3.2','3.3'], document('三阶段性能分析文档',
     '本报告比较vdot与等价RVV基线。两条路径均计算低8对有符号int8的点积，结果存入目标低32位，高96位清零。\n\n'+stage3_performance)),
]

records=[]
for stage,title,headings,content in documents:
    filename=title+'.pdf'
    source=root/f'docs/submission/stage{stage}.md'
    story=[p(title,h1),p('香山昆明湖 V2 自定义 vdot.vv'),
           p('队伍：全栈漏洞队。参赛单位：西安电子科技大学。'),Spacer(1,10)]
    story += parse(source,content)
    buf=BytesIO();SimpleDocTemplate(buf,pagesize=A4,leftMargin=48,rightMargin=48,topMargin=43,bottomMargin=56).build(story,onFirstPage=footer,onLaterPages=footer)
    writer=PdfWriter();writer.clone_reader_document_root(PdfReader(BytesIO(buf.getvalue())))
    writer.metadata={'/Author':'全栈漏洞队'};writer.root_object.pop(NameObject('/Metadata'),None)
    writer.compress_identical_objects(remove_duplicates=True,remove_unreferenced=True)
    target=args.output/filename
    with target.open('wb') as f:writer.write(f)
    reader=PdfReader(target);assert dict(reader.metadata)=={'/Author':'全栈漏洞队'} and reader.xmp_metadata is None
    extracted='\n'.join(page.extract_text() for page in reader.pages)
    assert '{{' not in extracted and '<本机IP>' not in extracted
    banned='co'+'dex'
    assert banned not in extracted.lower() and banned.encode() not in target.read_bytes().lower()
    forbidden_metadata_keys={key.casefold() for key in (
        '/Company','/Organization','/Unit','/LastModifiedBy','/LastSavedBy','/LastAuthor',
        '/Creator','/CreatorTool','/Producer','/CreationDate','/ModDate','/ModifyDate',
        '/LastModified','/Metadata','/MetadataDate')}
    for number in reader.xref.get(0,{}):
        obj=reader.get_object(number)
        if isinstance(obj,dict):
            found=forbidden_metadata_keys & {str(key).casefold() for key in obj}
            assert not found, (filename,found)
        if hasattr(obj,'get_data'):
            data=obj.get_data().lower()
            assert all(banned.encode(enc) not in data for enc in ('ascii','utf-16-be','utf-16-le'))
    assert all(h in extracted for h in headings)
    if title=='二阶段基础测试文档':assert all(x['vd_hex'] in extracted for x in basic['cases'])
    records.append({'stage':stage,'title':title,'file':str(target.resolve()),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'pages':len(reader.pages),'required_sections':headings,'metadata_author':'全栈漏洞队','metadata_fields':dict(reader.metadata),'company_metadata_present':False,'last_modified_by_metadata_present':False,'xmp_present':False,'metadata_and_content_scan':'passed','source_markdown_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'section_content_sha256':hashlib.sha256(content.encode()).hexdigest(),'visual_review':'pending'})
manifest={'status':'documents_rendered_pending_visual_review','final_project_head':head,'tested_project_head':binding['tested_project_head'],'binding_sha256':hashlib.sha256(args.binding.read_bytes()).hexdigest(),'basic_validation':str(args.basic_run.resolve()),'basic_validation_source_head':basic['source_project_head'],'reports':records,'video_responsibility':'participant','videos_included':False}
(args.output/'reports-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'reports':records},ensure_ascii=False,indent=2))
