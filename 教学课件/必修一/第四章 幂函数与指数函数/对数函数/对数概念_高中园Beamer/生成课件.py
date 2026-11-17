"""从共享题库和课堂选题生成TeX。须在仓库中运行，生成后使用XeLaTeX编译。"""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'AGENTS.md').is_file())
BANK=ROOT/'04_题库积累/对数的概念/对数概念_题库.json'
rows=json.loads(BANK.read_text(encoding='utf8'));byid={x['id']:x for x in rows}
plan=json.loads((HERE/'课堂选题.json').read_text(encoding='utf8'))
assert len(byid)==len(rows)==79
selected=plan['guided']+plan['final_practice']
assert len(set(selected))==8 and all('三维设计' in byid[i]['source'] for i in selected)
assert plan['exploration_minutes']+plan['independent_minutes']+plan['feedback_minutes']+plan['summary_minutes']==40
HEADER=r'''% !TeX program = xelatex
% 由生成课件.py生成；改题目请改共享题库，改选题请改课堂选题.json。
\documentclass[aspectratio=169,10pt]{beamer}
\usepackage[UTF8,fontset=fandol]{ctex}
\IfFontExistsTF{Microsoft YaHei}{\setCJKsansfont{Microsoft YaHei}}{}
\usetheme{GaoZhongYuan}
\usepackage{booktabs}
\setlength{\parskip}{.6em}
\newcommand{\ans}[1]{{\color{red!70!black}#1}}
\author{深圳中学高中园}\date{}
'''
def frame(title,body):return '\\begin{frame}[t]{'+title+'}\n'+body+'\n\\end{frame}\n'
def practice(title,item):return '% 题库编号：'+item['id']+'\n\\begin{campuspractice}{'+title+'}\n'+item['question_tex']+'\n\\end{campuspractice}\n'
def solution(title,item):return '\\ifdefined\\TeacherEdition\n'+frame(title,item['answer_tex'])+'\\fi\n'
parts=[HEADER,r'\title{4.3.1 对数的概念}',r'\begin{document}\campusmaketitle',
'% 0—3分钟',frame('情境：未知的指数',r'''\[2^x=4\Rightarrow x=2,\qquad2^x=8\Rightarrow x=3.\]
\[2^x=10\quad\Rightarrow\quad x=\ ?\]
这里已知底数和幂，需要求指数。能否用一个符号准确表示它？'''),
'% 3—10分钟',frame('对数的定义',r'''当 $a>0$ 且 $a\ne1$，$N>0$ 时，
\[\boxed{a^x=N\quad\Longleftrightarrow\quad x=\log_aN}.\]
$a$ 是底数，$N$ 是真数，$\log_aN$ 表示指数，是一个数。
\[2^x=10\Longleftrightarrow x=\log_210.\]
指数式和对数式表达的是同一个数量关系。'''),
frame('定义的条件',r'''\[\boxed{a>0,\quad a\ne1,\quad N>0}.\]
\begin{itemize}
\item 若 $a=1$，$1^x=1$ 不能唯一确定指数。
\item 负底数或零底数不能对所有实指数定义幂。
\item 正底数的幂始终为正，真数必须大于0。
\end{itemize}
$\log_2\frac12=-1$，说明对数的值可以为负。

说一说：真数为正，是否意味着对数的值也必须为正？'''),
'% 10—16分钟']
for label,id in zip(['例题：指数式化为对数式','即时检查：指数式化为对数式'],plan['guided'][:2]):
 item=byid[id];parts.extend([practice(label,item),solution(label+'：参考',item)])
parts += ['% 16—21分钟',frame('两种常见记号',r'''\[\lg N=\log_{10}N,\qquad\ln N=\log_eN.\]
$e=2.71828\ldots$，是一个无理数。
\[\lg100=2,\qquad\ln e=1.\]
记号虽不同，求指数的含义与底数、真数条件相同。'''),
frame('由定义得到的性质',r'''当 $a>0$ 且 $a\ne1$ 时，
\[\log_a1=0,\qquad\log_aa=1.\]
\[\boxed{a^{\log_aN}=N\ (N>0)},\qquad\boxed{\log_a(a^x)=x}.\]
前式把对数作为指数，后式对幂取对数。

请用指数式解释：为什么 $\log_a1=0$？'''),'% 21—27分钟']
for label,id in zip(['例题：恒等式与负指数','即时检查：由对数求未知量'],plan['guided'][2:]):
 item=byid[id];parts.extend([practice(label,item),solution(label+'：参考',item)])
parts += ['% 27—33分钟：连续独立完成4题，不在中间显示解答。']
for n,id in enumerate(plan['final_practice'],1):parts.append(practice('当堂练习'+str(n),byid[id]))
parts += ['% 33—37分钟：教师依据板演和巡视组织反馈。',r'\ifdefined\TeacherEdition',frame('当堂练习：反馈与纠错',r'''\begin{enumerate}
\item $\lg0.01=x$：$x=-2$。
\item $\log_7(x+2)=2$：$x=47$。
\item $\log_a(1-2a)$：$0<a<\frac12$。
\item $\log_5(x^2)=2$：$x=\pm5$。
\end{enumerate}
请说明第3题的三个条件，以及第4题负根为何保留。'''),r'\fi',
'% 37—40分钟',r'''\begin{campussummary}
\begin{itemize}
\item 对数求的是什么？$a^x=N\Longleftrightarrow x=\log_aN$。
\item 哪三个条件？$a>0$、$a\ne1$、$N>0$。
\item 两个恒等式各在什么条件下使用？
\item 求出结果后，把解代回原式检查。
\end{itemize}
请用自己的话解释：$\log_5(x^2)=2$ 中为何可取负数 $x$？
\end{campussummary}''',r'\campusclosing[谢谢]\end{document}']
(HERE/'对数概念_原白板版.tex').write_text('\n'.join(parts)+'\n',encoding='utf8')
full=[HEADER,r'\title{对数的概念：全量备课题库}',r'\begin{document}\campusmaketitle']
for item in rows:
 full += [practice('题库 '+item['id'],item),solution(item['id']+'：参考解答',item)]
full += [frame('数学文化与拓展材料',r'以下材料供备课选用，不计入40分钟主课。'),r'\input{数学文化附录.tex}',r'\campusclosing[谢谢]\end{document}']
(HERE/'对数概念_全量题库.tex').write_text('\n'.join(full)+'\n',encoding='utf8')
print('Generated 40-minute lesson and 79-record full bank.')
