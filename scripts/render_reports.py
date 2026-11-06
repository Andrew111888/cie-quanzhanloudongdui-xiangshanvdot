"""Render source-bound reports, retaining only the team author in PDF metadata."""
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from pathlib import Path
import argparse
import hashlib
import html
import json
import re
import subprocess
import textwrap
from pypdf import PdfReader, PdfWriter

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, LongTable,
                               TableStyle, Image, XPreformatted, PageBreak)

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--binding', type=Path, help='Verified final source binding; omitting this creates draft PDFs')
parser.add_argument('--output', type=Path, help='Use a new directory to preserve previously issued reports')
parser.add_argument('--report-date', default=datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat(),
                    help='Human-facing evidence review date, YYYY-MM-DD')
args = parser.parse_args()
if re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.report_date) is None:
    raise SystemExit('Invalid report date')
binding = None
if args.binding:
    binding = json.loads(args.binding.read_text())
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    if binding['status'] != 'verified' or binding['final_project_head'] != head:
        raise SystemExit('Final report binding does not match the current source commit')
    for name, digest in binding['tracked_file_sha256'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise SystemExit('Source/document changed after binding: ' + name)
output = args.output.resolve() if args.output else root / ('output/pdf-release' if binding else 'output/pdf')
temporary = root / 'tmp/pdfs'
output.mkdir(parents=True, exist_ok=True)
temporary.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('CJK', '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'))
pdfmetrics.registerFontFamily('CJK', normal='CJK', bold='CJK', italic='CJK', boldItalic='CJK')
pdfmetrics.registerFont(TTFont('Latin', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFontFamily('Latin', normal='Latin', bold='Latin', italic='Latin', boldItalic='Latin')
pdfmetrics.registerFont(TTFont('Mono', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
width = A4[0] - 96
body = ParagraphStyle('Body', fontName='Latin', fontSize=9.3, leading=14,
                      spaceAfter=6, wordWrap='CJK', splitLongWords=True)
table_body = ParagraphStyle('Table', parent=body, fontSize=7.7, leading=11, spaceAfter=0)
h1 = ParagraphStyle('H1', parent=body, fontSize=18, leading=25, textColor=colors.HexColor('#142d4e'),
                    spaceBefore=16, spaceAfter=13, keepWithNext=True)
h2 = ParagraphStyle('H2', parent=h1, fontSize=12, leading=19, spaceBefore=14, spaceAfter=7)
code_style = ParagraphStyle('Code', parent=body, fontSize=7.2, leading=10,
                            fontName='Mono', backColor=colors.HexColor('#f0f3f7'), borderPadding=7)
notice = ParagraphStyle('Notice', parent=body, fontSize=9.8, leading=17,
                        textColor=colors.HexColor('#8c341e'), backColor=colors.HexColor('#fff2eb'),
                        borderPadding=9, spaceBefore=10, spaceAfter=20)


def clean(text):
    return text.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-')


def inline(text):
    value = html.escape(clean(text))
    value = re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)', r'<link href="\2" color="#2367aa">\1</link>', value)
    value = re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', value)
    value = re.sub(r'`([^`]+)`', r'\1', value)
    return mixed_fonts(value.replace('**', ''))


def mixed_fonts(value):
    # Droid Sans Fallback intentionally omits ASCII. Use explicit CJK runs
    # alongside embedded DejaVu, including tables, code and footer text.
    return re.sub(r'([\u2e80-\ua4cf\uac00-\ud7ff\uf900-\ufaff\uff01-\uff60]+)',
                  r'<font name="CJK">\1</font>', value)


def paragraph(text, style=body):
    return Paragraph(inline(text), style)


def markdown(path):
    lines = path.read_text().splitlines()
    elements, pending = [], []
    def flush():
        if pending:
            elements.append(paragraph(' '.join(pending)))
            pending.clear()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            flush(); i += 1; continue
        if line.startswith('```'):
            flush(); i += 1; code = []
            while i < len(lines) and not lines[i].startswith('```'):
                code.extend(textwrap.wrap(clean(lines[i]), width=104,
                                          replace_whitespace=False, drop_whitespace=False) or [''])
                i += 1
            elements += [XPreformatted(mixed_fonts(html.escape('\n'.join(code))), code_style), Spacer(1, 9)]
            i += 1; continue
        if line.startswith('|'):
            flush(); rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [s.strip() for s in lines[i].strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', cell) for cell in cells):
                    rows.append(cells)
                i += 1
            count = len(rows[0])
            if any(len(row) != count for row in rows): raise ValueError('Malformed Markdown table: ' + str(path))
            # Preserve room for descriptions and full hashes; CJK wrapping also
            # breaks long ASCII identities without cropping them.
            weights = [1.0] * count
            if count == 2: weights = [0.8, 2.0]
            if count == 3: weights = [1.1, 1.2, 1.8]
            table = LongTable([[paragraph(cell, table_body) for cell in row] for row in rows],
                              colWidths=[width*w/sum(weights) for w in weights],
                              repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8eef6')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9fc')]),
                ('GRID', (0, 0), (-1, -1), .35, colors.HexColor('#cbd5e2')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6), ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements += [table, Spacer(1, 10)]
            continue
        image = re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)', line)
        if image:
            flush(); image_path = path.parent / image[2]
            if image_path.suffix == '.svg':
                rendered = temporary / (image_path.stem + '.png')
                subprocess.run(['/usr/bin/convert', '-density', '160', '-background', 'white',
                                str(image_path), str(rendered)], check=True)
                image_path = rendered
            picture = Image(str(image_path))
            ratio = min(width / picture.imageWidth, 300 / picture.imageHeight)
            picture.drawWidth = picture.imageWidth * ratio
            picture.drawHeight = picture.imageHeight * ratio
            elements += [picture, paragraph(image[1], table_body), Spacer(1, 10)]
            i += 1; continue
        if line.startswith('#'):
            flush(); level = len(line) - len(line.lstrip('#'))
            elements.append(paragraph(line.lstrip('#').strip(), h1 if level == 1 else h2))
        elif re.match(r'^(?:- |\d+\. )', line):
            flush(); elements.append(paragraph(line))
        else:
            pending.append(line)
        i += 1
    flush()
    return elements


def footer(canvas, doc):
    canvas.setStrokeColor(colors.HexColor('#cbd5e2'))
    canvas.line(48, 42, A4[0]-48, 42)
    canvas.setFont('Latin', 7.5)
    canvas.setFillColor(colors.HexColor('#61738a'))
    label = paragraph('全栈漏洞队 | ' + ('最终交付版' if binding else '开发审阅版') + ' | ' + args.report_date,
                      ParagraphStyle('Footer', parent=body, fontSize=7.5, leading=10))
    label.wrap(width, 12)
    label.drawOn(canvas, 48, 27)
    canvas.drawRightString(A4[0]-48, 29, f'{doc.page}')


reports = [
    ('stage1-environment-waveform-draft.pdf', '阶段一 - 环境与向量加法',
     ['STAGE1_WAVEFORM.md', 'CLEAN_REPRODUCTION.md', 'BUILDING.md', 'BOOTSTRAP.md']),
    ('stage2-vdot-design-verification-draft.pdf', '阶段二 - 设计与功能验证',
     ['DESIGN.md', 'VALIDATION.md']),
    ('stage3-difftest-performance-draft.pdf', '阶段三 - 协同验证与性能',
     ['DIFFTEST_CHECKS.md', 'PERFORMANCE.md', 'EVIDENCE_INDEX.md']),
]
if binding:
    final_documents = [
        ['results/stage1-clean.md', 'CLEAN_REPRODUCTION.md', 'BUILDING.md', 'BOOTSTRAP.md'],
        ['DESIGN.md', 'results/stage2-clean.md'],
        ['results/stage3-clean.md', 'OPTIMIZATION_RESULTS.md', 'OPTIMIZATION.md'],
    ]
    reports = [(name, title, documents) for (name, title, _), documents in zip(reports, final_documents)]
artifact_records = []
for filename, title, documents in reports:
    if binding:
        filename = filename.replace('-draft.pdf', '.pdf')
    target = output / filename
    status_notice = ('最终交付版：完整干净检出验收已通过。各结果的实际构建提交、最终源码提交、输入摘要与证据目录由绑定清单明确区分。未明确的赛题语义仍按暂定契约披露，未得到官方确认。'
                     if binding else '开发审阅版：定向、1000组随机、真实差分反例与恢复、流水压力和性能数据均已有证据。未修改原核的干净构建与vadd已通过；扩展核干净构建、最终录屏与打包仍待完成，不作为正式提交包。')
    story = [paragraph('香山昆明湖 V2 自定义 vdot.vv', h1), paragraph(title, h2),
             paragraph('队伍：全栈漏洞队。证据核对日期：' + args.report_date + '。'),
             paragraph(status_notice, notice)]
    if binding:
        story += [paragraph('最终作品源码提交：' + binding['final_project_head']),
                  paragraph('实际干净构建源码提交：' + binding['tested_project_head']),
                  paragraph('两者的处理器、NEMU、工作负载、配置和验收分析输入已逐字节核对。')]
    for number, name in enumerate(documents):
        if number: story.append(PageBreak())
        story += markdown(root / 'docs' / name)
    doc = SimpleDocTemplate(str(target), pagesize=A4, rightMargin=48, leftMargin=48,
                            topMargin=45, bottomMargin=55, title=title,
                            author='全栈漏洞队', pageCompression=1)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    original = PdfReader(BytesIO(target.read_bytes()), strict=True)
    sanitized = PdfWriter()
    sanitized.clone_reader_document_root(original)
    sanitized.metadata = {'/Author': '全栈漏洞队'}
    sanitized.root_object.pop('/Metadata', None)
    sanitized.compress_identical_objects(remove_duplicates=False, remove_unreferenced=True)
    with target.open('wb') as stream:
        sanitized.write(stream)
    verified = PdfReader(target, strict=True)
    if dict(verified.metadata or {}) != {'/Author': '全栈漏洞队'} or '/Metadata' in verified.root_object:
        raise RuntimeError('PDF metadata policy failed: ' + target.name)
    artifact_records.append({'file': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                             'document_sha256': {name: hashlib.sha256((root/'docs'/name).read_bytes()).hexdigest()
                                                 for name in documents}})
    print(target)
(output / 'reports-manifest.json').write_text(json.dumps({'status': 'final' if binding else 'draft',
    'final_project_head': binding['final_project_head'] if binding else None,
    'binding_sha256': hashlib.sha256(args.binding.read_bytes()).hexdigest() if binding else None,
    'reports': artifact_records}, ensure_ascii=False, indent=2) + '\n')
