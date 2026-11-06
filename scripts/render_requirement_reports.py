"""Render the three numbered contest reports from verified recorded evidence."""
import argparse
from datetime import datetime
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

def parse(path):
    content = path.read_text().replace('hello xiangshan, I am 全栈漏洞队, <本机IP>',greeting)
    content = content.replace('{{BASIC_CASE_OUTPUT}}',case_output)
    content = content.replace('<!-- LOCAL_ENVIRONMENT_IMAGE -->','![实际仿真输出画面](evidence:environment-output.png)')
    assert '{{' not in content
    lines=content.splitlines(); out=[]; pending=[];i=0
    def flush():
        if pending: out.append(p(' '.join(pending)));pending.clear()
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
        elif s.startswith('- '):flush();out.append(p(s))
        else:pending.append(s)
        i+=1
    flush();return out

def footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#c8d5df'));canvas.line(48,41,A4[0]-48,41)
    x=p('全栈漏洞队 | 赛题编号交付版 | 2026-11-06',cell);x.wrap(W,20);x.drawOn(canvas,48,26)
    canvas.setFont('Latin',8);canvas.drawRightString(A4[0]-48,27,str(doc.page))

records=[]
for stage,filename in [(1,'第一阶段-环境部署与向量加法.pdf'),(2,'第二阶段-vdot设计与基础测试.pdf'),(3,'第三阶段-协同仿真与延迟分析.pdf')]:
    source=root/f'docs/submission/stage{stage}.md'
    story=[p('香山昆明湖 V2 自定义 vdot.vv',h1),p('作品源码：'+head),
           p('真实完整构建/验收源码：'+binding['tested_project_head']),
           p('补充逐例测试源码：'+basic['source_project_head']),
           p('处理器、NEMU及原有关键输入逐字节绑定；新增逐例测试另存实际输入摘要。三段官网录屏由参赛者另行完成。')]
    story += parse(source)
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
    for number in reader.xref.get(0,{}):
        obj=reader.get_object(number)
        if hasattr(obj,'get_data'):
            data=obj.get_data().lower()
            assert all(banned.encode(enc) not in data for enc in ('ascii','utf-16-be','utf-16-le'))
    headings={1:['1.1','1.2','1.3'],2:['2.1','2.2','2.3.1','2.3.2','2.3.3'],3:['3.1.1','3.1.2','3.2','3.3']}[stage]
    assert all(h in extracted for h in headings)
    if stage==2:assert all(x['vd_hex'] in extracted for x in basic['cases'])
    records.append({'stage':stage,'file':str(target.resolve()),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'pages':len(reader.pages),'required_sections':headings,'metadata_author':'全栈漏洞队','metadata_and_content_scan':'passed','source_markdown_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'visual_review':'pending'})
manifest={'status':'documents_rendered_pending_visual_review','final_project_head':head,'tested_project_head':binding['tested_project_head'],'binding_sha256':hashlib.sha256(args.binding.read_bytes()).hexdigest(),'basic_validation':str(args.basic_run.resolve()),'basic_validation_source_head':basic['source_project_head'],'reports':records,'video_responsibility':'participant','videos_included':False}
(args.output/'reports-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'reports':records},ensure_ascii=False,indent=2))
