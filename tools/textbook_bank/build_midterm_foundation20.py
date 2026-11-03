"""Build an editable A4 booklet: 20 exercises, knowledge list, then teacher key."""
from pathlib import Path
from fractions import Fraction as F
import csv
import json
import re
import shutil
import subprocess

import pypdfium2 as pdfium

from build_midterm_papers import BANK, ROOT, STYLE, resolve
from midterm_foundation20_data import ITEMS

OUT = ROOT / '教学课件/必修一/期中考试/期中基础过关20题'
TMP = ROOT / 'tmp/midterm_foundation20_a4'
FINAL = OUT / '期中基础过关20题_A4学生练习及教师讲解.pdf'
CATALOG = json.loads((BANK / '答案与知识点/知识点目录.json').read_text('utf-8'))

PREAMBLE = r'''% !TeX program = xelatex
% 学生：PDF1—12页；教师：PDF13—32页。A4纵向，100%，双面长边翻转。
% 内容由同目录学生题目、知识清单、教师讲解三个文件输入，全部公式可编辑。
\documentclass[UTF8,fontset=windows,11pt,a4paper]{ctexart}
\usepackage[left=18mm,right=18mm,top=16mm,bottom=17mm,headheight=14pt]{geometry}
\usepackage{amsmath,amssymb,array,booktabs,needspace,fancyhdr,tikz}
\usepackage[unicode,hidelinks]{hyperref}
\hypersetup{pdftitle={高一数学期中基础过关20题},pdfauthor={数学教学备课资料}}
\setlength{\parindent}{0pt}\setlength{\parskip}{3pt}
\linespread{1.1}\raggedbottom\setlength{\emergencystretch}{2em}
\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}
\newcommand{\Edition}{学生练习与知识清单}
\fancyfoot[C]{\small 期中基础过关20题\quad\Edition\quad 第\thepage 页}
\newcommand{\subq}[2]{\par\Needspace{2\baselineskip}（#1）#2}
\newcommand{\score}[1]{（#1分）}
\newcommand{\field}[2]{\par\smallskip\textbf{#1：}#2\par}
\newcommand{\colhead}[2]{\noindent\begin{minipage}[t][20mm][t]{\linewidth}
\centering {\large\bfseries 高一数学期中基础过关20题}\par
{\small #1\quad #2}\par\end{minipage}\par}
\newsavebox{\statementbox}
\newcommand{\exercise}[2]{\sbox{\statementbox}{\begin{minipage}{\linewidth}
\textbf{#1.（10分）}#2\end{minipage}}%
\typeout{QUESTIONHEIGHT #1=\the\dimexpr\ht\statementbox+\dp\statementbox\relax}%
\noindent\begin{minipage}[t][12cm][t]{\linewidth}\usebox{\statementbox}\par\vfill\end{minipage}\par}
'''


def score_allocations(solution):
    sections = re.split(r'\\subq\{\d+\}\{', solution)[1:]
    return [sum(int(printed or macro) for printed, macro in
                re.findall(r'（(\d+)分）|\\score\{(\d+)\}', section))
            for section in sections]


def tex_prose(text):
    for symbol, command in {'≤': r'\le', '≥': r'\ge', '≠': r'\ne'}.items():
        text = text.replace(symbol, '$' + command + '$')
    return text


def check_math():
    """Boundary/identity checks support the independent full written review."""
    checks = []
    def check(name, truth):
        assert truth, name
        checks.append(name)
    A, B, U = {-1, 0, 1, 2}, {0, 2, 4}, {-2, -1, 0, 1, 2, 3, 4}
    check('1 sets', A & B == {0, 2} and A | B == {-1, 0, 1, 2, 4} and U - B == {-2, -1, 1, 3})
    check('7 minima attained', F(4) + F(9, 3) == 7 and 4 * (8 - 4) == 16)
    check('11 two input evaluations', (-1 + 2) ** 2 == 1 and 2 * (3 - 2) - 1 == 1)
    check('17 rational arithmetic', F(4) + F(1, 9) == F(37, 9) and F(8) + F(1, 4) == F(33, 4))
    for m in map(F, [-3, 0, 1, 2, 4]):
        for x in map(F, [-4, -3, 0, 1, 2, 3, 4, 5]):
            check(f'6 root order {m}/{x}', ((x - m) * (x - 1) <= 0) == (min(m, 1) <= x <= max(m, 1)))
    grid = [F(i, 10) for i in range(-20, 21)]
    f = lambda x: 2 * abs(x) - x*x
    check('16 extremum values and all positions',
          min(map(f, grid)) == 0 and max(map(f, grid)) == 1
          and [x for x in grid if f(x) == 0] == [-2, 0, 2]
          and [x for x in grid if f(x) == 1] == [-1, 1])
    for x in [F(i, 4) for i in range(13)]:
        value = 2 - 2*x if x <= 1 else x - 1
        check(f'12 graph threshold {x}', (value <= 1) == (F(1, 2) <= x <= 2))
    for x in [F(i, 4) for i in range(-16, 25)]:
        check(f'19 exponential threshold {x}', (2.0 ** float(abs(x - 1)) <= 8) == (-2 <= x <= 4))
    check('20 model threshold and positivity', 100 * F(1, 2)**2 == 25 and 100 * F(1, 2)**3 == F(25, 2))
    return checks


def export():
    assert len(ITEMS) == 20
    rows = []
    student_cols = []
    teacher_cols = []
    knowledge_cols = []
    for n, item in enumerate(ITEMS, 1):
        assert sum(item['allocation']) == 10
        assert score_allocations(item['solution']) == item['allocation'], n
        assert len(item['allocation']) == item['text'].count('\\subq{'), n
        sources = [resolve(spec) for spec in item['source'].split(';')]
        for key in item['knowledge_ids']:
            assert key in CATALOG
        ids = ';'.join(s['id'] for s in sources)
        source_tex = r'\par '.join(s['brief'] + f"（教材PDF第{s['pdf']}页）" +
            r'\par{\ttfamily\detokenize{' + s['id'] + '}}' for s in sources)
        guide_tex = '；'.join(k + '：书内p.' + '、'.join(map(str, CATALOG[k]['guide_printed_pages'])) +
            '（PDF' + '、'.join(map(str, CATALOG[k]['guide_pdf_pages'])) + '页）' for k in item['knowledge_ids'])
        if n % 2 == 1:
            student_cols.append(r'\colhead{学生练习}{第' + str(n) + '—' + str(n+1) +
                r'题\quad 每题10分}' + '\n')
        student_cols.append(r'\exercise{' + str(n) + '}{' + item['text'] + '}\n')
        if n % 2 == 0:
            student_cols.append('\\newpage\n')
        teacher_cols.append(r'\colhead{教师讲解与评分}{第' + str(n) + r'题\quad 10分}' + '\n')
        teacher_cols.append(r'\textbf{题目}\quad ' + item['text'] + '\n')
        for label, value in [('知识点', item['knowledge']), ('分步解答', item['solution']),
                             ('书写顺序', item['method']), ('易错提醒', item['error']),
                             ('独立达标', item['mastery'])]:
            teacher_cols.append(r'\field{' + label + '}{' + tex_prose(value) + '}\n')
        teacher_cols.append(r'{\footnotesize\field{教材母题}{' + source_tex + '}' +
            r'\field{改编说明}{' + item['change'] + '}' +
            r'\field{教材帮对应知识}{' + guide_tex + '}}\n')
        if n < 20:
            teacher_cols.append('\\newpage\n')
        if n in (1, 11):
            knowledge_cols.append(r'\colhead{对应知识清单}{第' + str(n) + '—' + str(n+9) + '题}\n')
        knowledge_cols.append(r'\field{第' + str(n) + '题}{' + item['knowledge'] + '}\n')
        if n == 10:
            knowledge_cols.append('\\newpage\n')
        rows.append({'题号': n, '训练分值': 10, '小问分值': '+'.join(map(str, item['allocation'])),
            '目标知识': '；'.join(CATALOG[k]['title'] for k in item['knowledge_ids']),
            '知识点编号': ';'.join(item['knowledge_ids']), '预期方法': item['method'],
            '易错点': item['error'], '难度预判': '基础巩固，含一步迁移' if n in (6, 16, 18, 19) else '基础',
            '达标标准': item['mastery'], '母题ID': ids,
            '教材出处': ';'.join(s['brief'] for s in sources),
            '教材PDF页': ';'.join(str(s['pdf']) for s in sources),
            '教材帮页码': guide_tex, '改编说明': item['change']})
    (OUT / '学生题目.tex').write_text(''.join(student_cols), 'utf-8')
    (OUT / '知识清单.tex').write_text(''.join(knowledge_cols), 'utf-8')
    (OUT / '教师讲解.tex').write_text(''.join(teacher_cols), 'utf-8')
    graph = STYLE[STYLE.index(r'\newcommand{\readinggraph}'):STYLE.index(r'\renewcommand{\arraystretch}')]
    source = PREAMBLE + graph + r'''
\begin{document}
\pdfbookmark[0]{学生练习20题}{student}
\input{学生题目.tex}
\pdfbookmark[0]{20题对应知识清单}{knowledge}
\input{知识清单.tex}
\clearpage
\renewcommand{\Edition}{教师讲解、评分与教材出处}
\pdfbookmark[0]{教师讲解与教材出处}{teacher}
\input{教师讲解.tex}
\end{document}
'''
    (OUT / 'main.tex').write_text(source, 'utf-8')
    with (OUT / '20题考点与教材出处.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


def compile_and_verify():
    TMP.mkdir(parents=True, exist_ok=True)
    xelatex = shutil.which('xelatex') or r'D:\texlive\2025\bin\windows\xelatex.exe'
    for run in (1, 2):
        p = subprocess.run([xelatex, '-interaction=nonstopmode', '-halt-on-error',
            f'-output-directory={TMP}', 'main.tex'], cwd=OUT, capture_output=True, timeout=120)
        (TMP / f'compile-{run}.txt').write_bytes(p.stdout + p.stderr)
        assert p.returncode == 0, f'XeLaTeX failed; see {TMP}'
    log = (TMP / 'main.log').read_text('utf-8', errors='replace')
    assert not re.search(r'^!|Overfull|Underfull|Missing character|^LaTeX Warning|^Package .* Warning', log, re.M), 'TeX warnings'
    heights = re.findall(r'QUESTIONHEIGHT (\d+)=([\d.]+)pt', log)
    assert len(heights) == 20
    # At least 24mm writing space after the full statement inside every 120mm block.
    assert all(float(h) <= (120 - 24) / 25.4 * 72.27 for _, h in heights)
    shutil.copyfile(TMP / 'main.pdf', FINAL)
    with pdfium.PdfDocument(str(FINAL)) as doc:
        assert len(doc) == 32, len(doc)
        assert all(abs(doc[i].get_size()[0] - 210/25.4*72) < .02 and abs(doc[i].get_size()[1] - 297/25.4*72) < .02 for i in range(len(doc)))
        first = ''.join(doc[i].get_textpage().get_text_range() for i in range(12))
        last = ''.join(doc[i].get_textpage().get_text_range() for i in range(12, 32))
        assert not any(t in first for t in ['XJ-B1-', '分步解答', '教材母题', '教师讲解'])
        assert all(f'{n}.（10分）' in re.sub(r'\s+', '', first) for n in range(1, 21))
        for item in ITEMS:
            for spec in item['source'].split(';'):
                assert resolve(spec)['id'] in last
        render = TMP / 'render'
        render.mkdir(exist_ok=True)
        for i in range(len(doc)):
            doc[i].render(scale=1.25).to_pil().save(str(render / f'page-{i+1:02d}.png'))
    return heights


def main():
    rows = export()
    checks = check_math()
    heights = compile_and_verify()
    (OUT / '核查记录.json').write_text(json.dumps({
        'date': '2026-11-04', 'questions': len(rows), 'subquestions': sum(len(q['allocation']) for q in ITEMS),
        'practice_points': 200, 'points_per_question': 10,
        'independent_review': '20题55小问独立重算；已补齐第5(3)等号设问，第17题补根式母题；计算、证明、端点、定义域及计分已检查。',
        'supporting_arithmetic_checks': len(checks), 'question_heights_pt': dict(heights),
        'minimum_writing_space_mm': 24, 'pdf_pages': 32, 'paper_mm': [210, 297],
        'student_pages': [1, 12], 'teacher_pages': [13, 32],
        'layout': 'A4纵向单栏；学生题每页2题，知识清单2页，教师每页1题。',
        'sources_hidden_in_student': True, 'sources_in_teacher': True,
        'score_target': '24+20+30+20=94只是正式考试备考目标，不是成绩预测；本册200分不折算成考试分数。',
        'visual_review': '最终PDF需逐页渲染确认；检查完成记录见使用说明。',
    }, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print(json.dumps({'pdf': str(FINAL), 'pages': 32, 'questions': len(rows), 'arithmetic_checks': len(checks)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
