"""Render the verified accumulating-dot experiment as a Chinese PDF report."""
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
parser.add_argument('--receipt', type=Path, required=True)
parser.add_argument('--input', type=Path, default=Path('docs/累加融合实验结果.md'))
parser.add_argument('--output', type=Path, default=Path('output/pdf/累加融合实验报告.pdf'))
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
receipt = json.loads(args.receipt.read_text())
assert receipt['status'] == 'passed'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
for name, value in receipt['evidence_sha256'].items():
    assert digest(Path(name)) == value, name
source = args.input.resolve(strict=True)
args.output.parent.mkdir(parents=True, exist_ok=True)
temporary = root/'tmp/pdfs/acc-report'
temporary.mkdir(parents=True, exist_ok=True)
for name, file in [('Latin','DejaVuSans.ttf'),('Mono','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
pdfmetrics.registerFont(TTFont('CJK','/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'))
width = A4[0]-96
body = ParagraphStyle('body',fontName='Latin',fontSize=9.3,leading=14.7,spaceAfter=7,wordWrap='CJK')
cell = ParagraphStyle('cell',parent=body,fontSize=7.7,leading=11.5,spaceAfter=0)
h1 = ParagraphStyle('h1',parent=body,fontSize=18,leading=25,textColor=colors.HexColor('#163c56'),spaceAfter=14,keepWithNext=True)
h2 = ParagraphStyle('h2',parent=h1,fontSize=12.5,leading=19,spaceBefore=12,spaceAfter=8)
h3 = ParagraphStyle('h3',parent=h1,fontSize=10.5,leading=17,spaceBefore=8,spaceAfter=5)
code = ParagraphStyle('code',parent=body,fontName='Mono',fontSize=7.2,leading=11,backColor=colors.HexColor('#f0f4f8'),borderPadding=6,spaceAfter=12)

def mixed(text):
    return re.sub(r'([\u2e80-\ua4cf\uac00-\ud7ff\uf900-\ufaff\uff01-\uff60]+)',r'<font name="CJK">\1</font>',text)

def paragraph(text,style=body):
    text=html.escape(text.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-'))
    text=re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#17609b">\1</link>',text)
    text=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',text)
    return Paragraph(mixed(text.replace('**','').replace('`','')),style)

lines=source.read_text().splitlines();story=[];pending=[];i=0
def flush():
    if pending:story.append(paragraph(' '.join(pending)));pending.clear()
while i<len(lines):
    line=lines[i]
    if not line.strip():flush();i+=1;continue
    if line.startswith('```'):
        flush();i+=1;parts=[]
        while i<len(lines) and not lines[i].startswith('```'):
            parts.extend(textwrap.wrap(lines[i],width=102,replace_whitespace=False,drop_whitespace=False) or ['']);i+=1
        story.append(XPreformatted(mixed(html.escape('\n'.join(parts))),code));i+=1;continue
    if line.startswith('|'):
        flush();rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            row=[s.strip() for s in lines[i].strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?',s) for s in row):rows.append(row)
            i+=1
        n=len(rows[0]);assert all(len(row)==n for row in rows)
        weights={2:[1,2.4],3:[2.4,1,1.4],4:[1.5,1,1,1],5:[1.8,1,1,1,1]}.get(n,[1]*n)
        if rows[0][0]=='K':weights=[.35,1.15,1.15,1.15,1.15,.8]
        if rows[0][0]=='独立链数':weights=[.7,1.5,1.5,1,1.4]
        table=LongTable([[paragraph(s,cell) for s in row] for row in rows],colWidths=[width*x/sum(weights) for x in weights],repeatRows=1,hAlign='LEFT',rowSplitRange=(2,len(rows)-2) if len(rows)>3 else None)
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eef5')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f9fb')]),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#c8d5df')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));table.spaceAfter=10;story.append(table);continue
    match=re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)',line)
    if match:
        flush();path=(source.parent/match[2]).resolve(strict=True)
        if path.suffix=='.svg':
            png=temporary/(path.stem+'.png');subprocess.run(['/usr/bin/convert','-density','160','-background','white',str(path),str(png)],check=True);path=png
        picture=Image(str(path));scale=min(width/picture.imageWidth,240/picture.imageHeight)
        picture.drawWidth=picture.imageWidth*scale;picture.drawHeight=picture.imageHeight*scale
        story.extend([picture,paragraph(match[1],cell),Spacer(1,10)]);i+=1;continue
    if line.startswith('#'):
        flush();level=len(line)-len(line.lstrip('#'));story.append(paragraph(line.lstrip('#').strip(),h1 if level==1 else h2 if level==2 else h3))
    elif line.startswith('- '):flush();story.append(paragraph(line))
    else:pending.append(line)
    i+=1
flush()
def footer(canvas,doc):
    canvas.setFont('Latin',8);canvas.drawCentredString(A4[0]/2,27,str(doc.page))
buffer=BytesIO();SimpleDocTemplate(buffer,pagesize=A4,leftMargin=48,rightMargin=48,topMargin=43,bottomMargin=64).build(story,onFirstPage=footer,onLaterPages=footer)
writer=PdfWriter();writer.clone_reader_document_root(PdfReader(BytesIO(buffer.getvalue())))
writer.metadata={'/Author':'全栈漏洞队'};writer.root_object.pop(NameObject('/Metadata'),None)
writer.compress_identical_objects(remove_duplicates=True,remove_unreferenced=True)
with args.output.open('wb') as stream:writer.write(stream)
reader=PdfReader(args.output);assert dict(reader.metadata)=={'/Author':'全栈漏洞队'} and reader.xmp_metadata is None
ban='co'+'dex';assert ban not in '\n'.join(page.extract_text() for page in reader.pages).casefold()
for number in reader.xref.get(0,{}):
    obj=reader.get_object(number)
    if isinstance(obj,dict):assert not {str(key).casefold() for key in obj}&{key.casefold() for key in ('/Company','/Organization','/Unit','/LastModifiedBy','/LastSavedBy','/LastAuthor','/Creator','/CreatorTool','/Producer','/CreationDate','/ModDate','/ModifyDate','/LastModified','/Metadata','/MetadataDate')}
    if hasattr(obj,'get_data'):assert all(ban.encode(encoding) not in obj.get_data().lower() for encoding in ('ascii','utf-16-be','utf-16-le'))
record={'status':'rendered_pending_visual_review','file':str(args.output.resolve()),'sha256':digest(args.output),'pages':len(reader.pages),'author':'全栈漏洞队','metadata':dict(reader.metadata),'xmp_present':False,'source_sha256':digest(source),'receipt_sha256':digest(args.receipt),'footer':'centered_page_number_only'}
args.output.with_suffix('.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps(record,ensure_ascii=False))
