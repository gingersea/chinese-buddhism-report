#!/usr/bin/env python3
"""Build perfectly formatted PDF from report.md matching v80p169 academic journal style."""

import re
import os

os.chdir('/home/room115/chinese-buddhism-report')

# ── Parse report.md ──────────────────────────────────────────────
with open('report.md', 'r') as f:
    text = f.read()

lines = text.split('\n')
title = lines[0].lstrip('# ').strip()

# Abstract
abstract_lines = []
keywords = ""
in_abstract = False
for line in lines[1:]:
    if line.startswith('## 摘要'):
        in_abstract = True
        continue
    if in_abstract:
        if line.startswith('**关键词') or line.startswith('**關鍵詞'):
            keywords = line.replace('**关键词：**', '').replace('**關鍵詞：**', '').replace('**', '').strip()
            break
        if line.strip() and not line.startswith('---'):
            abstract_lines.append(line.strip())
abstract_text = '\n'.join(abstract_lines)

# Body sections
sections = []
current_sec = None

for line in lines:
    if line.startswith('## ') and ('一、' in line or '二、' in line or '三、' in line or '四、' in line or line.startswith('## 结语')):
        if current_sec:
            sections.append(current_sec)
        current_sec = {'title': line[3:].strip(), 'paras': [], 'buf': []}
        continue

    if current_sec is not None:
        if line.startswith('## 注释') or line.startswith('## 参考'):
            if current_sec['buf']:
                current_sec['paras'].append(''.join(current_sec['buf']))
                current_sec['buf'] = []
            sections.append(current_sec)
            current_sec = None
            break
        if line.strip() == '---' or line.strip() == '':
            if current_sec['buf']:
                current_sec['paras'].append(''.join(current_sec['buf']))
                current_sec['buf'] = []
        elif not line.strip().startswith('- 正文约'):
            current_sec['buf'].append(line.strip())

if current_sec is not None and current_sec not in sections:
    if current_sec['buf']:
        current_sec['paras'].append(''.join(current_sec['buf']))
    sections.append(current_sec)

# Footnotes
fn_data = []
in_fn = False
for line in lines:
    if line.startswith('## 注释'):
        in_fn = True
        continue
    if in_fn:
        if line.startswith('## 参考') or line == '---':
            break
        if line.strip():
            fn_data.append(line.strip())

# References
ref_cats = {}
in_ref = False
current_cat = None
for line in lines:
    if line.startswith('## 参考文献'):
        in_ref = True
        continue
    if in_ref:
        if line.startswith('### '):
            current_cat = line[4:].strip()
            ref_cats[current_cat] = []
            continue
        if line.strip() and current_cat:
            ref_cats[current_cat].append(line.strip())

print(f"Parsed: {len(sections)} sections, {len(fn_data)} footnotes, "
      f"{sum(len(v) for v in ref_cats.values())} references")

# ── Convert footnote markers in body to superscript HTML ─────────
FOOTNOTE_MARKERS = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'

def convert_fn_markers(text):
    """Convert ①②③ etc. to <sup class='fn-ref'>①</sup>"""
    for m in FOOTNOTE_MARKERS:
        text = text.replace(
            m,
            f'<sup class="fn-ref"><a href="#fn{FOOTNOTE_MARKERS.index(m)+1}">{m}</a></sup>'
        )
    return text

# ── Build HTML ────────────────────────────────────────────────────
html_parts = []

html_parts.append('''<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<style>
@page {
    size: 524pt 737pt;
    margin: 62pt 75pt 72pt 75pt;

    @top-left {
        content: "中國文化研究所學報  第80期（2025年1月）";
        font-family: "Noto Sans CJK SC", sans-serif;
        font-size: 8pt;
        color: #333;
    }
    @top-right {
        content: "姜欢耘";
        font-family: "Noto Sans CJK SC", sans-serif;
        font-size: 8pt;
        color: #333;
    }
    @bottom-center {
        content: counter(page);
        font-family: "Noto Serif CJK SC", serif;
        font-size: 9pt;
    }
}

@page :first {
    @top-left {
        content: none;
    }
    @top-right {
        content: none;
    }
}

body {
    font-family: "Noto Serif CJK SC", "WenQuanYi Micro Hei", serif;
    font-size: 10.5pt;
    line-height: 1.85;
    text-align: justify;
    orphans: 2;
    widows: 2;
}

/* ── Title area ── */
.title-page-header {
    text-align: center;
    font-family: "Noto Sans CJK SC", sans-serif;
    font-size: 9pt;
    margin-bottom: 36pt;
    color: #333;
}
.doi-line {
    text-align: left;
    font-size: 8pt;
    margin-bottom: 48pt;
}
h1.title {
    font-family: "Noto Sans CJK SC", sans-serif;
    font-size: 15pt;
    font-weight: bold;
    text-align: center;
    line-height: 1.5;
    margin-bottom: 24pt;
}
p.author {
    text-align: center;
    font-size: 11pt;
    margin-top: 24pt;
    margin-bottom: 48pt;
}
p.author sup a {
    text-decoration: none;
    color: #000;
}

/* ── Abstract ── */
.abstract {
    margin-bottom: 24pt;
}
h2.abstract-heading {
    font-family: "Noto Sans CJK SC", sans-serif;
    font-size: 11pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 12pt;
}
p.abstract-text {
    text-indent: 0;
    margin: 0 0 8pt 0;
}
p.keywords {
    text-indent: 0;
    margin: 8pt 0 0 0;
    font-size: 10pt;
}

/* ── Section headings ── */
h2.sec-title {
    font-family: "Noto Sans CJK SC", sans-serif;
    font-size: 11pt;
    font-weight: bold;
    margin: 18pt 0 10pt 0;
    page-break-after: avoid;
}

/* ── Body text ── */
p.body-text {
    text-indent: 2em;
    margin: 0 0 6pt 0;
    text-align: justify;
}
sup.fn-ref {
    font-size: 7.5pt;
    line-height: 0;
}
sup.fn-ref a {
    text-decoration: none;
    color: #000;
}

/* ── Word count ── */
p.wordcount {
    text-align: left;
    font-size: 9pt;
    margin-top: 12pt;
    margin-bottom: 24pt;
}

/* ── Footnotes ── */
.footnotes {
    margin-top: 24pt;
    padding-top: 10pt;
    page-break-before: auto;
}
.fn-heading {
    font-family: "Noto Sans CJK SC", sans-serif;
    font-size: 11pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 14pt;
}
.fn-item {
    margin-bottom: 5pt;
}
p.fn-text {
    font-size: 9pt;
    line-height: 1.5;
    text-indent: 0;
    margin: 0;
    padding-left: 1.5em;
    text-indent: -1.5em;
}
span.fn-marker {
    font-size: 8pt;
}

/* ── Bibliography ── */
.bibliography {
    margin-top: 28pt;
    padding-top: 10pt;
    page-break-before: auto;
}
.bib-heading {
    font-family: "Noto Sans CJK SC", sans-serif;
    font-size: 11pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 14pt;
}
h3.bib-cat {
    font-family: "Noto Serif CJK SC", serif;
    font-size: 10.5pt;
    font-weight: normal;
    margin: 12pt 0 6pt 0;
    padding-left: 2em;
    text-indent: -2em;
}
p.bib-item {
    font-size: 9pt;
    line-height: 1.5;
    margin: 2pt 0;
    padding-left: 2em;
    text-indent: -2em;
}

/* ── Page break control ── */
.page-break {
    page-break-before: always;
}
</style>
</head>
<body>
''')

# ── First page ──
html_parts.append('<div class="doi-line">DOI: 10.0000/JCS.CUHK.202501_(80).XXXX</div>')
html_parts.append(f'<h1 class="title">{title}</h1>')
html_parts.append('<p class="author">姜欢耘<sup class="fn-ref"><a href="#fn-author">*</a></sup></p>')

# Abstract block
html_parts.append('<div class="abstract">')
html_parts.append('<h2 class="abstract-heading">摘要</h2>')
html_parts.append(f'<p class="abstract-text">{abstract_text}</p>')
html_parts.append(f'<p class="keywords"><b>關鍵詞：</b> {keywords}</p>')
html_parts.append('</div>')

# ── Body sections ──
for sec in sections:
    html_parts.append(f'<h2 class="sec-title">{sec["title"]}</h2>')
    for para in sec['paras']:
        processed = convert_fn_markers(para)
        html_parts.append(f'<p class="body-text">{processed}</p>')

# Word count
html_parts.append('<p class="wordcount">- 正文約3,100字 -</p>')

# ── Footnotes ──
html_parts.append('<div class="footnotes">')
html_parts.append('<h2 class="fn-heading">注釋</h2>')

# Author footnote
html_parts.append('<div class="fn-item" id="fn-author">')
html_parts.append('<p class="fn-text"><span class="fn-marker">*</span> 姜欢耘，香港中文大學中國文化研究所，學生證號：1155233165。</p>')
html_parts.append('</div>')

for i, fn in enumerate(fn_data):
    # Remove the marker from text, we add it back
    m = re.match(r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]+\s*(.*)', fn.strip())
    if m:
        content = m.group(1)
        marker = FOOTNOTE_MARKERS[i]
        html_parts.append(f'<div class="fn-item" id="fn{i+1}">')
        html_parts.append(f'<p class="fn-text"><span class="fn-marker">{marker}</span> {content}</p>')
        html_parts.append('</div>')

html_parts.append('</div>')

# ── Bibliography ──
html_parts.append('<div class="bibliography">')
html_parts.append('<h2 class="bib-heading">引用書目</h2>')

for cat_name, items in ref_cats.items():
    html_parts.append(f'<h3 class="bib-cat">（{cat_name}）</h3>')
    for item in items:
        # Escape HTML entities
        item_escaped = item.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html_parts.append(f'<p class="bib-item">{item_escaped}</p>')

html_parts.append('</div>')

html_parts.append('</body></html>')

html_content = '\n'.join(html_parts)

# Write HTML
with open('report_formatted.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"HTML written: {len(html_content)} chars")
print("Generating PDF via WeasyPrint...")