"""Recheck the eight editions and impose A4 pages at 100% on A3 landscape.

Run from the teaching repository with the project's Python runtime. Temporary
compilation and rendering stay in ignored tmp/. Existing paper PDFs are read
only: any mismatch between editable TeX, data and delivered PDF stops the build.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import csv
import hashlib
import json
import re
import shutil
import subprocess

import pymupdf as fitz

from build_midterm_papers import OUT, POINTS, ROOT, STYLE, resolve, student, teacher
from midterm_papers_data import PAPERS

DEST = OUT / 'A3合订打印版'
BUILD = ROOT / 'tmp/midterm_three'
FINAL = DEST / '高一数学期中练习四套卷_A3合订_学生卷及教师答案.pdf'
XELATEX = shutil.which('xelatex') or r'D:\texlive\2025\bin\windows\xelatex.exe'
PARTS = {15: [9, 6], 16: [6, 9], 17: [4, 5, 8], 18: [4, 5, 8], 19: [3, 6, 4]}

# Notes record the independent mathematical review, not numerical test output.
# All choices were judged individually; these identify the decisive conditions.
NOTES = {
    'A': [
        '交集为{2,5}；逐项排除并集、差集选项。',
        'x=1推出x²=1；反向用x=-1否定。',
        '全称改存在，范围不变；>0否定为≤0。',
        '令t=x-1>0，1+t+9/t≥7；x=4取等。',
        'B的定义域与对应关系均相同；A漏-1，C对应不同，D漏负数。',
        '同时满足x≤3和x≠1；3可取。',
        '先算f(2)=8，再由奇性得f(-2)=-8；条件相容。',
        '对称轴x=a须在3的右侧或重合，a≥3；端点可取。',
        '正数倒数反向、平方保序；C比值方向错，D在c=0失效。',
        '配方，核对顶点和两端点；最小-1、最大3，在[1,3]递增。',
        '仅正半轴递增不能跨0比较；正半轴x-3的奇延拓否定C。',
        '最小值m-4须严格大于0，故m>4，不能含4。',
        '两次查表：2→1→3。',
        '分x<-2、-2≤x≤2、x>2讨论；值域[4,+∞)。',
        '交并补端点正确；t=1时连接点仍由A覆盖，故t≤1。',
        '第1问两根-2、3，外侧含根；第2问根m、1，重根时无解。',
        '偶延拓为-2x-x²；最大1在±1，最小0在-2、0、2；g=f/2可实现。',
        '37/9；指数-2，域R\\{0}，偶；左右两段分别增、减，正半轴作差证明。',
        '底数1/3；左增右减，值域(0,1]；比较指数反向，解集[-1,5]。',
    ],
    'B': [
        '并集为{0,1,2,3,4}，重复元素只记一次。',
        'x=3推出x²=9，逆向反例x=-3；必要不充分。',
        '存在实数x使x²<x；原命题真假不改变否定形式。',
        'a²+b²≥2ab=18；a=b=3可达。',
        'x²在定义域内处处唯一有像且像属于B；不要求取遍B。',
        'x≥-1且x≠2；-2已在根式范围外；-1可取。',
        '偶性转到3，9-12+1=-2。',
        '向下抛物线的轴a≤2，等号时仍严格递减。',
        '两负数倒数大小反向；除负数反向；平方及相反数选项错误。',
        '最小4在2；作差证(0,2]递减；f(1)=f(4)=5。',
        '加法关系推出f(0)=0、奇性、f(1)=3、f(6)=18；不假定全实数上线性。',
        '最大值k+1≤0，故k≤-1，端点可取。',
        '先第一段f(-1)=1，再第二段f(1)=1。',
        '递增区间含0且f(0)=0，故f(-2)<0<f(1)<f(3)。',
        '交集[1,5)，补集含5；空交条件t≥5，等号成立。',
        '第1问(-1,4)；第2问根m、2，外侧含根，m=2时全R。',
        '负半轴-x²+2x；正、负、跨0三类分别证明，覆盖零点端界。',
        '33/4；指数1/3，域R，奇，全R增；立方差证明正半轴，奇性及符号补足其余。',
        '底数2；分界-1/2，左减右增，值域[1,+∞)；解集[-2,1]。',
    ],
    'C': [
        '先对(1,5]取补再交[-1,3)，结果[-1,1]，1须保留。',
        'x²≤4与|x|≤2都等价于-2≤x≤2；充要。',
        '存在x∈[1,+∞)使x²<1；范围保持不变，≥改<。',
        'x(8-x)≤16，根式≤4，x=4在开区间内。',
        'D展开后同域同对应；其余三组定义域或对应不同。',
        'x≥1且x≠3，1可取。',
        'f(-2)=-5，5+2(-5)=-5。',
        '顶点2在区间外，全段递减，最小f(1)=1。',
        '乘负数反向、同加保序；平方再乘负数须反向，比值>1。',
        '定义域[-1,3]不对称，不是偶函数；最小0、最大2；非全段递减。',
        '奇性及含0的正半轴严格递增推出AB；f(-2)<0<f(1)，非偶。',
        '最小9-m²≥0，故-3≤m≤3；两端均可取。',
        '图点A(0,2)、B(1,0)、C(3,2)及辅助线正确；f(0)=2，f(2)=1。',
        '顶点1值-1，左端-1值3，右端2值0，值域[-1,3]。',
        '交[-1,2]、并(-3,+∞)，补含-3；A⊆B等价于t≤-3，开端点仍可取等。',
        '第1问[-1,2]；第2问根m、3，外侧不含根，重根时R\\{3}。',
        '偶延拓x²+4x+1；最小-3在±2，最大1仅0；g=f/2可实现。',
        '136/5；指数3/2，域[0,+∞)，非奇非偶；作差第二因子严格正，含0递增。',
        'a=1/2，t≥0；值域(0,100]，任意有限时间不为0；不少于12.5得[0,3]。',
    ],
    'D': [
        '全集内补B为{0,4,5}，与A交为{0,4}。',
        'x>2推出x>0；x=1反驳逆向，充分不必要。',
        '存在x∈[-1,1]使x²>1；量词范围保留，≤改>。',
        't=x-2>0，4+2t+8/t≥12；x=4取等。',
        '实数立方根(x⁹)=x³；其余对应不同、0无定义或定义域不同。',
        'x≤2且x≠±1；三个区间端点正确，2可取。',
        '偶性给f(-2)=5，f(1)=2，差3；条件可实现。',
        '轴-a-1≤1，故a≥-2；边界仍递增。',
        '乘除负数反向，故AC；同减保序；平方无固定方向，取1、2反驳D。',
        '顶点1最大4；端点-1最小0；值域[0,4]，非全段增。',
        '偶性转到正半轴比较；f(3)<f(1)，f(1)>f(2)，f(0)>f(1)。',
        '配方最小k-9≥0，故k≥9，边界可取。',
        '令自变量x=1使x+2=3，结果1。',
        '三个区间分段为-2、2x-4、2，端点都可取；值域[-2,2]。',
        '交(1,3]、并[-1,5]，补不含两端；恰覆盖要求-1≤t≤3，端点可取。',
        '第1问(-3/2,1)；第2问根m、-2，两根间含根；重根时单点{-2}。',
        '偶延拓x²+2x+3；[1,3]作差严格正；最小2在±1、最大6在±3；g=f/2相容。',
        '63/4；指数-1/2，域(0,+∞)，非奇非偶；作差证明严格递减，0不可取。',
        'a=2，h=2ˣ-2，递增，值域(-2,+∞)，唯一零点1；不等式解x≤3。',
    ],
}


def normalized(text):
    return re.sub(r'\s+', '', text)


def compile_twice(folder, name, output):
    output.mkdir(parents=True, exist_ok=True)
    for run in range(1, 3):
        p = subprocess.run(
            [XELATEX, '-interaction=nonstopmode', '-halt-on-error',
             f'-output-directory={output}', name + '.tex'],
            cwd=folder, capture_output=True, timeout=120,
        )
        (output / f'{name}-run{run}.txt').write_bytes(p.stdout + p.stderr)
        assert p.returncode == 0, f'Compilation failed: {folder}/{name}'
    log = (output / f'{name}.log').read_text('utf-8', errors='replace')
    assert not re.search(
        r'^!|Overfull|Underfull|Missing character|^LaTeX Warning|^Package .* Warning',
        log, re.M,
    ), f'Compilation warnings: {folder}/{name}'
    return output / f'{name}.pdf'


def audit_source(key):
    items = PAPERS[key]
    folder = OUT / f'{key}卷'
    assert len(items) == len(NOTES[key]) == 19
    assert (folder / '排版设置.tex').read_text('utf-8') == STYLE
    rows = []
    for n, item in enumerate(items, 1):
        item['sources'] = [resolve(s) for s in item['source'].split(';')]
        allocations = []
        if n >= 15:
            sections = re.split(r'\\subq\{\d+\}\{', item['solution'])[1:]
            # Each occurrence of 各1分/各2分 in these papers refers to two
            # explicitly listed conclusions, verified in the mathematical review.
            allocations = [sum(int(value) * (2 if each else 1)
                               for each, value in re.findall(r'（(各?)(\d+)分）', section))
                           for section in sections]
            assert allocations == PARTS[n], (key, n, allocations)
            assert sum(allocations) == POINTS[n - 1]
            assert len(sections) == item['text'].count('\\subq{')
        elif n <= 11:
            assert len(item['options']) == 4
            assert set(item['answer']) <= set('ABCD')
            assert len(item['answer']) == 1 if n <= 8 else len(item['answer']) in (2, 3)
        rows.append({
            '卷别': key, '题号': n, '分值': POINTS[n - 1],
            '客观题答案': item['answer'] if n <= 14 else '见教师版完整解析',
            '分小问得分': '+'.join(map(str, allocations)),
            '独立复核要点': NOTES[key][n - 1],
            '母题ID': ';'.join(s['id'] for s in item['sources']),
            '教材印刷页': ';'.join(str(s['printed']) for s in item['sources']),
            '复核结论': '本次独立复核未发现数学错误',
        })
    assert (folder / 'main.tex').read_text('utf-8') == student(key, items)
    assert (folder / '教师版.tex').read_text('utf-8') == teacher(key, items)
    return rows


def audit_rebuilt(key, edition):
    folder = OUT / f'{key}卷'
    rebuilt = compile_twice(folder, edition, BUILD / key)
    filename = f'{key}卷_' + ('学生卷.pdf' if edition == 'main' else '教师版.pdf')
    final = folder / filename
    with fitz.open(rebuilt) as a, fitz.open(final) as b:
        assert len(a) == len(b) == 4
        for p, q in zip(a, b):
            assert abs(p.rect.width - 210 / 25.4 * 72) < .02
            assert abs(p.rect.height - 297 / 25.4 * 72) < .02
            assert normalized(p.get_text()) == normalized(q.get_text()), (key, edition)
            # Compare rendered pages, including graph and formula placement.
            assert p.get_pixmap().samples == q.get_pixmap().samples, (key, edition, p.number)
    return {'paper': key, 'edition': edition, 'pages': 4,
            'source_pdf_sha256': hashlib.sha256(final.read_bytes()).hexdigest()}


def verify_imposition(pdf):
    sections = []
    with fitz.open(pdf) as doc:
        assert len(doc) == 16
        assert len(doc.get_toc()) == 8
        for section_index, (edition, key) in enumerate(
                (edition, key) for edition in ('学生卷', '教师版') for key in 'ABCD'):
            with fitz.open(OUT / f'{key}卷' / f'{key}卷_{edition}.pdf') as original:
                for logical, source_page in enumerate(original):
                    physical = section_index * 2 + logical // 2
                    target = doc[physical]
                    assert abs(target.rect.width - 420 / 25.4 * 72) < .02
                    assert abs(target.rect.height - 297 / 25.4 * 72) < .02
                    side = logical % 2
                    clip = fitz.Rect(side * target.rect.width / 2, 0,
                                     (side + 1) * target.rect.width / 2, target.rect.height)
                    assert normalized(target.get_text(clip=clip)) == normalized(source_page.get_text())
                    # Font sizes are preserved rather than reduced to fit A3.
                    sizes = lambda spans: sorted(round(s['size'], 3)
                        for b in spans['blocks'] if 'lines' in b
                        for line in b['lines'] for s in line['spans'])
                    assert sizes(target.get_text('dict', clip=clip)) == sizes(source_page.get_text('dict'))
            sections.append({'edition': edition, 'paper': key,
                             'physical_pages': [section_index * 2 + 1, section_index * 2 + 2]})
        for page in doc.pages(0, 8):
            text = page.get_text()
            assert not any(s in text for s in ('答案速查', '评分细则', '教材改编出处', 'XJ-B1-'))
        for section_index, key in enumerate('ABCD', 4):
            text = ''.join(doc[p].get_text() for p in range(section_index * 2, section_index * 2 + 2))
            for item in PAPERS[key]:
                for source in item['sources']:
                    assert source['id'] in text
        render = BUILD / 'a3_render'
        render.mkdir(exist_ok=True)
        for i, page in enumerate(doc):
            page.get_pixmap(matrix=fitz.Matrix(1.25, 1.25)).save(str(render / f'page-{i + 1:02d}.png'))
    return sections


def main():
    rows = [row for key in 'ABCD' for row in audit_source(key)]
    jobs = [(key, edition) for key in 'ABCD' for edition in ('main', '教师版')]
    with ThreadPoolExecutor(max_workers=4) as pool:
        documents = list(pool.map(lambda job: audit_rebuilt(*job), jobs))
    # Existing independent arithmetic/parameter tests, using fresh compile logs.
    subprocess.run([__import__('sys').executable, str(Path(__file__).with_name('verify_midterm_papers.py'))],
                   cwd=ROOT, check=True)
    rebuilt = compile_twice(DEST, 'main', BUILD / 'a3_combined')
    sections = verify_imposition(rebuilt)
    shutil.copyfile(rebuilt, FINAL)
    # Reopen the actual deliverable, not only the temporary build.
    assert verify_imposition(FINAL) == sections
    with (DEST / '逐题复核记录.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    report = {
        'review_date': '2026-10-25', 'question_count': 76,
        'mathematics': '逐题重算并核对选项、量词、定义域、取等条件、全部端点和证明分类；未发现需订正的数学错误。',
        'scoring': '20道解答题按实际打印的分步评分逐小问求和，含各1分/各2分；每卷150分。',
        'source_consistency': '数据与TeX逐字一致，八份源文件各编译两遍；新编译32页与既有正式PDF逐页文本及像素一致。',
        'imposition': 'A3横向420×297mm；每页左右各一张A4原尺寸，32逻辑页合16物理页；字号不缩小。',
        'student_sources_visible': False, 'teacher_sources_retained': True,
        'paper_dimensions_mm': [420, 297], 'physical_pages': 16,
        'duplex_sheets': 8, 'print_scale': '100%', 'duplex_flip': 'short-edge',
        'sections': sections, 'inputs': documents,
        'output_sha256': hashlib.sha256(FINAL.read_bytes()).hexdigest(),
        'visual_review': '见打印说明中的逐页复核记录；渲染图保存在忽略目录tmp/midterm_three/a3_render。',
        'limitations': '未进行真实打印机试印；不代替教师最终审定，未声称获得教师签核。',
    }
    (DEST / '合订复核记录.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print(json.dumps({'questions': len(rows), 'source_documents': len(documents),
                      'combined_pages': 16, 'pdf': str(FINAL)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
