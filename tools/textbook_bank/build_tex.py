"""Export individually editable TeX statements and visibly unreviewed OCR drafts.

Never promote an OCR string to a checked mathematical transcription. The first
chapter has manually transcribed statements; other chapters remain review work.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from PIL import Image
from chapter1_transcriptions import ENTRIES

SYMBOLS = {'π':r'\pi','α':r'\alpha','β':r'\beta','γ':r'\gamma','θ':r'\theta',
 'φ':r'\varphi','ω':r'\omega','Δ':r'\Delta','∞':r'\infty','∈':r'\in',
 '∉':r'\notin','∪':r'\cup','∩':r'\cap','⊆':r'\subseteq','⊂':r'\subset',
 '∅':r'\varnothing','∃':r'\exists','∀':r'\forall','≤':r'\le','≥':r'\ge',
 '≠':r'\ne','±':r'\pm','×':r'\times','÷':r'\div','√':r'\surd',
 '∠':r'\angle','△':r'\triangle','⊥':r'\perp','∥':r'\parallel',
 '⇒':r'\Rightarrow','⇔':r'\Leftrightarrow','²':r'{}^2','³':r'{}^3',
 '⁴':r'{}^4','⁵':r'{}^5','⁶':r'{}^6','⁷':r'{}^7','⁸':r'{}^8','⁹':r'{}^9',
 '₀':r'{}_0','₁':r'{}_1','₂':r'{}_2','₃':r'{}_3','℃':r'{}^\circ\mathrm C',
 '°':r'{}^\circ','·':r'\cdot','•':r'\bullet','−':'-', '→':r'\to','≈':r'\approx',
 '∑':r'\sum','σ':r'\sigma','μ':r'\mu','δ':r'\delta','λ':r'\lambda',
 'ρ':r'\rho','η':r'\eta','ε':r'\varepsilon','ϕ':r'\phi','∵':r'\because','∴':r'\therefore',
 '‰':r'\text{\textperthousand}', '€':r'\text{[OCR:EUR]}', '£':r'\text{[OCR:GBP]}'}
ESCAPE={'\\':r'\textbackslash{}','{':r'\{','}':r'\}','$':r'\$',
 '&':r'\&','#':r'\#','%':r'\%','_':r'\_','^':r'\textasciicircum{}','~':r'\textasciitilde{}'}

def tex(s):
    result=[]
    for c in str(s):
        if c in SYMBOLS: result.append(r'\ensuremath{'+SYMBOLS[c]+'}')
        elif c in ESCAPE: result.append(ESCAPE[c])
        elif c=='\t': result.append(' ')
        elif c=='\n': result.append('\n')
        elif 32<=ord(c)<=126 or 0x4e00<=ord(c)<=0x9fff or 0x3000<=ord(c)<=0x303f or 0xff00<=ord(c)<=0xffef or c in '“”‘’…—–、': result.append(c)
        else: result.append(r'\ocrglyph{'+f'{ord(c):04X}'+'}')
    return ''.join(result)

PREAMBLE=r'''% !TeX program = xelatex
\documentclass[UTF8,a4paper,zihao=-4,fontset=windows,oneside,openany]{ctexbook}
\usepackage[margin=22mm,headheight=15pt]{geometry}
\usepackage{amsmath,amssymb,graphicx,xcolor,needspace,longtable,fancyhdr}
\usepackage[unicode,hidelinks]{hyperref}
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}
\setlength{\emergencystretch}{3em}
\linespread{1.2}
\raggedbottom
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{湘教版数学必修第一册：教师转写工作稿}
\fancyhead[R]{题干与公式可编辑}
\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0.3pt}
\newcommand{\subq}[1]{\par\Needspace{2\baselineskip}\noindent（#1）\quad}
\newcommand{\choice}[1]{\par\noindent #1.\quad}
\newcommand{\blank}{\underline{\hspace{1.7cm}}}
\newcommand{\ocrglyph}[1]{\textcolor{red!70!black}{[识别字符 U+#1 待核]}}
\newenvironment{bankitem}[4]{\par\Needspace{5\baselineskip}\noindent
  {\bfseries #1}\par{\small\color{blue!55!black}#2}\par
  {\footnotesize\ttfamily\detokenize{#3}}\par
  {\footnotesize\color{red!65!black}#4}\par\nopagebreak}
  {\par\medskip\hrule\medskip}
\newenvironment{ocrdraft}{\begingroup\small\color{black!65}}{\par\endgroup}
\newcommand{\questioninput}[1]{\input{questions/#1.tex}}
\hypersetup{pdftitle={湘教版必修第一册教材题库：转写工作稿},pdfauthor={教学资料整理}}
'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bank',type=Path,required=True)
    ap.add_argument('--work',type=Path,required=True);args=ap.parse_args()
    bank=args.bank.resolve(); out=bank/'TeX题库';out.mkdir(exist_ok=True)
    for name in ['questions','chapters','figures']:(out/name).mkdir(exist_ok=True)
    data=json.loads((bank/'题库数据.json').read_text('utf-8'));rows=data['items']
    first=[r for r in rows if r['chapter']==1]
    assert len(first)==107
    assert {r['id'].split('C01-')[1] for r in first}==set(ENTRIES)
    # Only a required diagram is rasterized. All first-chapter statements are TeX.
    Image.open(args.work/'pages/036.png').crop((766,1163,1078,1379)).save(out/'figures/C01-RV07.png')
    manifest=[]; chapter_inputs={i:[] for i in range(1,7)}; checked_inputs=[];midterm=[]
    for r in rows:
        suffix=r['id'].split('C01-')[-1]; checked=r['chapter']==1
        body=ENTRIES[suffix] if checked else '\\begin{ocrdraft}\n'+ '\n\\par\n'.join(tex(line) for line in r['ocr_draft'].splitlines() if line.strip())+'\n\\end{ocrdraft}'
        status='已对照原页转写题干及公式；待教师复核；未制作答案' if checked else 'OCR未校对：公式与文字均可能有误；未完成数学TeX转写；禁止直接发给学生'
        statement_pages=r['printed_pages']
        if checked and suffix not in {'HW-P012-Y1412','HW-P023-Y1381','RV-P029-Y1552'}:
            statement_pages=r['printed_pages'][:1]
        location=f"第{r['chapter']}章 / {r['section']} {r['section_title']} / 教材 p."+'、'.join(map(str,statement_pages))+' / PDF 第'+'、'.join(str(p+7) for p in statement_pages)+'页'
        comments=['% !TeX root = ../教材题库_全部条目_转写工作稿.tex',
          '% Source: '+r['id'], '% '+location, '% '+status,
          '% 原题及相邻原解截图（核对用）：'+', '.join('../'+p['image'] for p in r['parts']),
          '% 本文件只在转写完成后作为题干使用；OCR 条目尚不是可靠题干。']
        title=r['title'].replace('（含紧邻说明）','') if checked else r['title']
        content='\n'.join(comments)+'\n'+r'\begin{bankitem}{'+tex(title)+'}{'+tex(location)+'}{'+r['id']+'}{'+tex(status)+'}\n'+body+'\n'+r'\end{bankitem}'+'\n'
        if checked:
            content=r'\par\noindent\begin{minipage}{\linewidth}'+'\n'+content+r'\end{minipage}\par\medskip'+'\n'
        (out/'questions'/f"{r['id']}.tex").write_text(content,'utf-8')
        inp=r'\questioninput{'+r['id']+'}'
        chapter_inputs[r['chapter']].append(inp)
        if checked:checked_inputs.append(inp)
        if r['midterm_scope']:midterm.append(inp)
        manifest.append({'id':r['id'],'章节':r['chapter'],'类型':r['type'],'原题号':r['original_label'],
           '教材页码':'、'.join(map(str,r['printed_pages'])),'PDF页序':'、'.join(map(str,r['pdf_pages'])),
           'TeX文件':f"questions/{r['id']}.tex",'转写状态':status,'配图状态':'单独保存教材原配图' if suffix=='RV-P029-Y1165' else ('本题干无必需原配图' if checked else '待核对图表与共用图'),
           '教师批准':False})
    (out/'排版设置.tex').write_text(PREAMBLE,'utf-8')
    chapters=[]
    for c,inputs in chapter_inputs.items():
        title=next(r['chapter_title'] for r in rows if r['chapter']==c)
        chapterfile=f'chapters/chapter{c:02}.tex'
        (out/chapterfile).write_text(r'\chapter{'+tex(title)+'}\n'+'\n'.join(inputs)+'\n','utf-8')
        chapters.append(r'\input{'+chapterfile+'}')
    intro=r'''\frontmatter
\begin{titlepage}\centering\vspace*{22mm}
{\Huge 湘教版高中数学\\[5mm]必修第一册教材题库\par}
\vspace{14mm}{\Large 题干与公式可编辑的转写工作稿\par}
\vspace{12mm}{\large 757 个已定位条目；第1章107个条目已对照原页转写\par}
\vspace{10mm}\begin{minipage}{0.88\textwidth}
\textbf{进度说明：}第1章题干及公式已转写为数学 TeX；第2至6章650个条目仅保留可编辑 OCR 草稿，尚未完成公式转写，不是校对完成的题库。原页中的真假命题、判断选项按原文保留，不表示其结论成立。
\par 本工作稿用于教师核查，不是学生卷，不附作答留白，不含独立答案。例题原解及相邻说明保存在旁边的原图题库中，不混入已转写题干。
\par 每个条目独立保存在 questions 目录，可通过 \texttt{\textbackslash questioninput\{题目ID\}} 引用。必需图形单独保存在 figures；未转写条目的图表尚待核对。
\par 757为主标签定位的题目或题组数，小问不拆分。页边提问框、阅读材料内的散见问句尚未逐项列入完整性审查；不据此声称全部教材设问已无遗漏。
\par 印刷页码与 PDF 页序不同：正文 PDF 页序=教材页码+7。源教材未修改；所有条目仍待教师复核后用于课堂。
\end{minipage}\vfill{\large 2026年10月}\end{titlepage}
\tableofcontents\mainmatter
'''
    def master(name,inputs,introduction):
        (out/name).write_text(r'\input{排版设置.tex}'+'\n'+r'\begin{document}'+'\n'+introduction+'\n'+'\n'.join(inputs)+'\n'+r'\end{document}'+'\n','utf-8')
    master('教材题库_全部条目_转写工作稿.tex',chapters,intro)
    master('第一章_可编辑题干.tex',[chapters[0]],r'\frontmatter\chapter*{第一章：题干及公式已转写}\noindent 共107个主标签条目，均已对照原页转写，待教师复核。只收题干，不含答案；来源与题号逐题保留。\par 原题中的判断命题可能为假，按教材原文保留。\mainmatter')
    master('期中范围_转写工作稿.tex',midterm,intro)
    with (out/'条目索引.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=manifest[0].keys());w.writeheader();w.writerows(manifest)
    pending=[r for r in manifest if 'OCR未校对' in r['转写状态']]
    with (out/'需复核题目.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=manifest[0].keys());w.writeheader();w.writerows(manifest)
    (out/'转写进度.json').write_text(json.dumps({'located_entries':len(rows),'source_image_checked_statements':len(checked_inputs),
       'ocr_only_entries':len(pending),'teacher_approved_entries':0,'all_textbook_questions_exhaustively_checked':False,
       'source_sha256':data['source_sha256'],'notes':'页边框及阅读内零散问句待查；107仅为题干转写核对，不是独立解答或教师批准'},ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'all':len(rows),'transcribed':len(checked_inputs),'pending':len(pending)},ensure_ascii=False))

if __name__=='__main__':main()
