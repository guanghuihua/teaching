"""从唯一内容源生成学生卷、方法详解及分步Beamer的TeX文件。"""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
ITEMS = json.loads((ROOT / "十题内容.json").read_text(encoding="utf-8"))

COMMON = r"""\usepackage{amsmath,amssymb,newtxtext,newtxmath}
\usepackage{geometry,fancyhdr,needspace,enumitem,tabularx,booktabs}
\geometry{a4paper,left=1.8cm,right=1.8cm,top=1.65cm,bottom=1.65cm,headheight=15pt}
\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}
\fancyfoot[C]{\small\thepage}
\setlength{\parindent}{0pt}\setlength{\parskip}{0.35em}
\setlist[enumerate]{leftmargin=2em,itemsep=0.1em,topsep=0.2em}
\newcommand{\subq}[1]{\par\Needspace{2\baselineskip}（#1）}
\newcommand{\labeltext}[1]{\par\textbf{#1}\quad}
\setlength{\abovedisplayskip}{6pt}\setlength{\belowdisplayskip}{6pt}
"""

def write(name, content):
    (ROOT / name).write_text(content, encoding="utf-8")

def question(item, slide=False):
    text = item["question"]
    if slide:
        text = text.replace(r"\Needspace", r"\relax")
    return text

def student():
    out = [r"% !TeX program = xelatex", r"\documentclass[UTF8,zihao=-4]{ctexart}", COMMON,
           r"\fancyhead[L]{\small 高一数学期中复习}\fancyhead[R]{\small 考前重点十题}",
           r"\begin{document}",
           r"\begin{center}{\LARGE\bfseries 高一数学期中复习}\par\vspace{0.2cm}{\Large 考前重点十题}\end{center}",
           r"班级\underline{\hspace{2.3cm}}\quad 姓名\underline{\hspace{2.3cm}}\quad 得分\underline{\hspace{1.6cm}}\par",
           r"满分100分，建议用时100分钟。每题10分，须写明演算或证明过程。"]
    spaces = [4.7, 5.0, 4.6, 4.1, 5.7, 5.0, 5.4, 5.2, 5.1, 5.9]
    for i, item in enumerate(ITEMS):
        if i > 0 and i % 2 == 0:
            out += [r"\clearpage"]
        out += [r"\Needspace{7\baselineskip}",
                rf"\textbf{{{item['id']}.（10分）}}\quad " + question(item),
                r"\par{\footnotesize（" + item["student_source"] + r"）}",
                rf"\par\vspace*{{{spaces[i]}cm}}"]
    out += [r"\end{document}"]
    write("考前重点十题_学生卷.tex", "\n".join(out))

def teacher():
    out = [r"% !TeX program = xelatex", r"\documentclass[UTF8,zihao=-4]{ctexart}", COMMON,
           r"\linespread{1.05}", r"\fancyhead[L]{\small 高一数学期中复习}\fancyhead[R]{\small 详解与方法}",
           r"\begin{document}"]
    for i, item in enumerate(ITEMS):
        if i:
            out += [r"\clearpage"]
        out += [rf"{{\Large\bfseries 第{item['id']}题\quad {item['title']}}}",
                r"\par\textbf{题目（10分）}\quad " + question(item),
                r"\par{\footnotesize 来源：" + item["source"] + r"}",
                r"\labeltext{目标与难度}" + item["target"] + "难度：" + item["difficulty"] + "。",
                r"\labeltext{同类题解题步骤}\begin{enumerate}"]
        out += [r"\item " + step for step in item["steps"]]
        out += [r"\end{enumerate}", r"\labeltext{规范解答}"]
        for index, section in enumerate(item["solution"]):
            if index:
                out += [r"\par\Needspace{3\baselineskip}"]
            out += [r"\textbf{" + section["heading"] + r"}\quad"]
            out += section["blocks"]
        out += [r"\labeltext{易错提醒}" + item["error"],
                r"\labeltext{建议评分}" + item["scoring"],
                r"\labeltext{达标检查}" + item["assessment"]]
    out += [r"\end{document}"]
    write("考前重点十题_详解与方法.tex", "\n".join(out))

def slide_text(text):
    # 长行公式在投影中改为多行，数学内容与唯一内容源保持一致。
    text = text.replace(
        r"\[\complement_{\mathbb R}A=(-\infty,3)\cup[7,+\infty),\qquad \complement_{\mathbb R}B=(-\infty,2]\cup[10,+\infty).\]",
        r"\[\begin{aligned}\complement_{\mathbb R}A&=(-\infty,3)\cup[7,+\infty),\\\complement_{\mathbb R}B&=(-\infty,2]\cup[10,+\infty).\end{aligned}\]")
    text = text.replace(
        r"\[\left(\frac12\right)^{-1}=2,\quad(-2)^{-3}=\frac1{(-2)^3}=-\frac18,\quad\left(\frac14\right)^0=1,\quad9^{\frac12}=3.\]",
        r"\[\begin{gathered}\left(\frac12\right)^{-1}=2,\qquad(-2)^{-3}=\frac1{(-2)^3}=-\frac18,\\\left(\frac14\right)^0=1,\qquad9^{\frac12}=3.\end{gathered}\]")
    return text

def frame(title, blocks, pause_after=None):
    result = [r"\begin{frame}[t]", r"\PageHeading{" + title + "}"]
    for i, block in enumerate(blocks):
        result += [slide_text(block), r"\par"]
        if pause_after is not None and i == pause_after:
            result += [r"\pause"]
    return "\n".join(result + [r"\end{frame}"])

def beamer():
    # 本目录的Beamer文件先由仓库习题课模板复制而来，沿用其版式与字体。
    out = [r"% !TeX program = xelatex", r"% 基于 教学课件/习题课模板/习题课模板.tex 复制并填充。",
           r"\documentclass[UTF8,10pt,aspectratio=169]{ctexbeamer}",
           r"\usepackage{amsmath,amssymb,tikz}", r"\usepackage{newtxtext,newtxmath}",
           r"\usetheme{default}\usecolortheme{default}\usefonttheme{serif}",
           r"\setbeamertemplate{navigation symbols}{}\setbeamertemplate{footline}[frame number]",
           r"\setbeamersize{text margin left=0.7cm,text margin right=0.7cm}",
           r"\newcommand{\LessonTitle}{高一数学期中复习}",
           r"\newcommand{\LessonSubtitle}{考前重点十题}",
           r"\newcommand{\LessonInfo}{规范书写与题型方法}",
           r"\newcommand{\PageHeading}[1]{\begin{center}{\Large\bfseries #1}\end{center}\vspace{0.12cm}}",
           r"\newcommand{\subq}[1]{\par\vspace{0.15cm}（#1）}",
           r"\setlength{\abovedisplayskip}{5pt}\setlength{\belowdisplayskip}{5pt}",
           r"\begin{document}",
           frame(r"\LessonTitle", [r"\begin{center}\vspace{0.7cm}{\LARGE\bfseries\LessonSubtitle}\par\vspace{0.6cm}{\large\LessonInfo}\end{center}",
               r"\vspace{0.5cm}先独立作答，再核对推理依据与条件。"]),
           frame("复习范围", [r"第1题：集合的交并补运算。\par 第2、3题：二次不等式与分式不等式。\par 第4题：指数幂运算。",
               r"第5、6题：单调性与奇偶性的定义证明。\par 第7、8题：函数性质的应用与解析式。\par 第9、10题：基本不等式与最值。",
               r"\vspace{0.25cm}自查重点：范围、等价条件、端点和等号取得。"])]
    for item in ITEMS:
        n = item["id"]
        out += ["% " + item["source"], "% 目标：" + item["target"] + " 难度：" + item["difficulty"],
                "% 预期方法：" + "；".join(item["steps"]), "% 易错：" + item["error"], "% 评价：" + item["assessment"],
                frame(f"第{n}题\\quad {item['title']}", [question(item, True), r"\vfill{\footnotesize 来源：" + item["student_source"] + r"。}"])]
        for index, section in enumerate(item["solution"]):
            out += [frame(f"第{n}题详解\\quad {section['heading']}", section["blocks"], pause_after=0)]
        steps = r"\begin{enumerate}" + "\n".join(r"\item " + t for t in item["steps"]) + r"\end{enumerate}"
        out += [frame(f"第{n}题\\quad 同类题解题步骤", [steps, r"\vspace{0.25cm}\textbf{易错提醒}\quad " + item["error"]], pause_after=0)]
    out += [frame("答题检查", [r"集合、不等式：端点是否取到？分母是否非零？",
            r"函数：自变量是否在定义域？是否在同一单调区间？证明是否覆盖任意点？",
            r"最值：正性与定值结构是否成立？等号条件能否与原约束同时满足？"], pause_after=0),
            r"\end{document}"]
    write("考前重点十题_Beamer.tex", "\n".join(out))
    write("考前重点十题_Beamer讲义.tex", r"% !TeX program = xelatex" + "\n" + r"\PassOptionsToClass{handout}{ctexbeamer}" + "\n" + r"\input{考前重点十题_Beamer.tex}" + "\n")

student()
teacher()
beamer()
print("已生成4份TeX；内容源：十题内容.json。")
