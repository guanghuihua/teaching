"""Generate three printable student papers and separate scored teacher editions."""
from pathlib import Path
import json,csv,re
from collections import Counter
from midterm_papers_data import PAPERS

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'教学课件/必修一/期中考试/教材改编三套卷'
BANK=ROOT/'题目积累/教材题库/湘教版必修第一册'
ROWS=json.loads((BANK/'题库数据.json').read_text('utf-8'))['items']
POINTS=[5]*8+[6]*3+[5]*3+[15,15,17,17,13]
MODULES=['集合','逻辑','逻辑','基本不等式','函数概念','函数概念','函数性质','函数性质',
         '不等式性质','函数性质','函数性质','恒成立','函数概念','函数性质','集合','二次不等式','函数性质','幂函数','指数函数']
METHODS=['列举或数轴运算','检验双向推出','量词与不等号否定','基本不等式及取等条件','检查定义域与对应关系',
 '联立式子有意义的条件','奇偶性转换求值','对称轴与给定区间的位置','按符号逐项推理或反例',
 '配方、分段或作差判断','由定义逐项推理','配方转化为最值条件','依表、式或图逐层求值',
 '分段或配方确定值域、大小','数轴与端点检查','因式分解、比较两根大小并分类','对称延拓与函数性质推理',
 '指数运算、幂函数定义域、作差证明','底数取值、单调性、指数比较']
ERRORS=['混淆交并补或漏端点','把必要条件当成充分条件','改量词却漏改不等号或范围','下界未达到就当成最小值',
 '只比解析式，不比定义域','遗漏分母非零或根式端点','直接把负数代入正半轴表达式','忽略对称轴可在区间端点',
 '负数乘除不反向，或把非负当正','只看顶点，忽略定义域及端点','把分离区间的单调性合并或混淆奇偶性',
 '恒成立与有解混淆，严格与非严格混淆','外层求值时未重新选择对应关系','遗漏某段值域或最值取等位置',
 '开闭端点与参数等号误判','漏重根或根的次序分类','漏定义域对称性、跨零点或对称最值点',
 '负指数漏倒数、忽略实数定义域、把两个区间合成一个','底数小于1不反向、误将0计入值域或漏模型定义域']
LEVELS=['基础']*7+['中等']+['中等']*3+['基础','基础','中等','中等','中等','中等偏上','中等','中等']

STYLE=r'''% !TeX program = xelatex
\documentclass[UTF8,a4paper,11pt,fontset=windows]{ctexart}
\usepackage[left=18mm,right=18mm,top=16mm,bottom=17mm,headheight=14pt]{geometry}
\usepackage{amsmath,amssymb,array,booktabs,longtable,needspace,fancyhdr,xcolor,tikz}
\usepackage[hidelinks]{hyperref}
\setlength{\parindent}{0pt}\setlength{\parskip}{3pt}\linespread{1.1}
\setlength{\emergencystretch}{2em}\raggedbottom
\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}
\fancyfoot[C]{\small\PaperName\quad 第\thepage 页}
\newcommand{\R}{\mathbb R}
\newcommand{\blank}{\underline{\hspace{2.9cm}}}
\newcommand{\src}[1]{\par{\scriptsize\color{black!65}教材改编出处：#1。}\par}
\newcommand{\q}[2]{\par\Needspace{4\baselineskip}\textbf{#1.}\ #2}
\newcommand{\subq}[2]{\par\Needspace{2\baselineskip}（#1）#2}
\newcommand{\opts}[4]{\par\begin{tabular*}{\linewidth}{@{}p{.48\linewidth}@{\extracolsep{\fill}}p{.48\linewidth}@{}}A. #1&B. #2\\C. #3&D. #4\end{tabular*}\par}
\newcommand{\optsfour}[4]{\par\begin{tabular*}{\linewidth}{@{}p{.235\linewidth}@{\extracolsep{\fill}}p{.235\linewidth}p{.235\linewidth}p{.235\linewidth}@{}}A. #1&B. #2&C. #3&D. #4\end{tabular*}\par}
\newcommand{\parttitle}[1]{\par\Needspace{4\baselineskip}{\bfseries #1}\par}
\newcommand{\work}[1]{\par\vspace*{#1}}
\newcommand{\ans}[2]{\par\Needspace{4\baselineskip}\textbf{第#1题}\quad #2\par}
\newcommand{\readinggraph}{\begin{center}\begin{tikzpicture}[x=.65cm,y=.65cm,>=stealth,font=\small]
\draw[->](-.4,0)--(3.7,0)node[right]{$x$};\draw[->](0,-.35)--(0,2.65)node[above]{$y$};
\draw[thick](0,2)node[above right]{$A$}--(1,0)node[above left]{$B$}--(3,2)node[above right]{$C$};
\draw[dashed](0,2)--(3,2)--(3,0);\draw[dashed](2,0)--(2,1)--(0,1);
\node[below left]at(0,0){$O$};\foreach \x in {1,2,3}\node[below]at(\x,0){$\x$};
\foreach \y in {1,2}\node[left]at(0,\y){$\y$};\end{tikzpicture}\end{center}}
\renewcommand{\arraystretch}{1.2}
'''

def resolve(spec):
    c,code,p,n=spec.split();c,p,n=int(c),int(p),int(n)
    kind={'EX':'例题','HW':'习题','PR':'练习','RV':'复习题'}[code]
    found=[r for r in ROWS if r['chapter']==c and r['type']==kind and r['printed_pages'][0]==p and r['original_number']==(n or None)]
    assert len(found)==1,(spec,found)
    r=found[0];assert r['midterm_scope']
    statement=(BANK/'TeX题库/questions'/f"{r['id']}.tex").read_text('utf-8')
    assert 'ocrdraft' not in statement
    label=(f"例{n}" if code=='EX' else f"习题{r['section']}第{n}题" if code=='HW' else f"复习题第{n}题" if code=='RV' else f"练习第{n}题" if n else '页首练习')
    return dict(id=r['id'],brief=f'p.{p}，{label}',printed=p,pdf=p+7)

def front(key,teacher=False):
    return r'\input{排版设置.tex}'+'\n'+r'\newcommand{\PaperName}{'+key+'卷'+('参考答案与评分' if teacher else '')+'}\n'+r'\begin{document}'+'\n'+r'\begin{center}{\Large\bfseries 高一数学期中教材改编练习卷（'+key+r'）}\\[2mm]'+('参考答案、评分细则与教材出处' if teacher else r'湘教版必修第一册\quad 120分钟\quad 满分150分')+r'\end{center}'+'\n'

def student(key,items):
    s=front(key)+r'班级\underline{\hspace{2.4cm}}\quad 姓名\underline{\hspace{2.4cm}}\quad 学号\underline{\hspace{2.4cm}}'+'\n'
    for n,item in enumerate(items,1):
        if n in (9,16,18):s+='\n\\newpage\n'
        if n==1:s+=r'\parttitle{一、单项选择题（共8小题，每题5分，共40分）}每题只有一个正确选项。'+'\n'
        if n==9:s+=r'\parttitle{二、多项选择题（共3小题，每题6分，共18分）}每题有多项正确。全部选对得6分，部分选对且无错项得3分，含错项或未选得0分。'+'\n'
        if n==12:s+=r'\parttitle{三、填空题（共3小题，每题5分，共15分）}'+'\n'
        if n==15:s+=r'\parttitle{四、解答题（共5小题，共77分）}解答须写出文字说明、证明过程或演算步骤。'+'\n'
        if n<=14:s+=r'\par\noindent\begin{minipage}{\linewidth}'+'\n'
        s+=r'\q{'+str(n)+'}{'+(f'（{POINTS[n-1]}分）' if n>=15 else '')+item['text']+'}\n'
        if item['options']:
            macro='optsfour' if n in (1,4,7,8) else 'opts'
            s+='\\'+macro+''.join('{'+v+'}' for v in item['options'])+'\n'
        s+=r'\src{'+ '；'.join(r['brief'] for r in item['sources'])+'}\n'
        if n<=14:s+=r'\end{minipage}\par\smallskip'+'\n'
        else:s+=r'\work{'+({15:('3.0cm' if key=='C' else '4.0cm'),16:'6.7cm',17:'7.0cm',18:'6.6cm',19:'6.5cm'}[n])+'}\n'
    return s+r'\end{document}'+'\n'

def teacher(key,items):
    s=front(key,True)+r'单选、填空每题5分；多选全对6分，部分选对且无错项3分，含错项或未选0分。以下评分为本练习卷统一约定；解答题其他正确解法按相应步骤给分。'+'\n'
    s+=r'\parttitle{答案速查}\begin{center}\begin{tabular}{c|cccccccc}\toprule 题号&1&2&3&4&5&6&7&8\\答案&'+'&'.join(i['answer'] for i in items[:8])+r'\\\bottomrule\end{tabular}\par\smallskip\begin{tabular}{c|cccccc}\toprule 题号&9&10&11&12&13&14\\答案&'+'&'.join(i['answer'] for i in items[8:14])+r'\\\bottomrule\end{tabular}\end{center}'+'\n'
    s+=r'\parttitle{单项选择题解析}'+'\n'
    for n,item in enumerate(items,1):
        if n==15:s+='\n\\newpage\n'
        if n==9:s+=r'\parttitle{多项选择题与填空题解析}'+'\n'
        if n==15:s+=r'\parttitle{解答题解析与分步评分}'+'\n'
        s+=r'\ans{'+str(n)+'}{'+(r'\textbf{'+item['answer']+'}。' if n<=14 else f'（{POINTS[n-1]}分）')+item['solution']+'}\n'
        if n>=15:s+=r'\src{'+'；'.join(r['brief'] for r in item['sources'])+'}\n'
    s+='\n\\newpage\n'+r'\parttitle{命题结构与教材改编记录}'+'\n'
    s+=r'''本卷只使用教材第1至3章及第4章4.1至4.2的例题、习题和练习作为母题。集合与逻辑30分，不等式31分，函数概念与性质59分，幂函数与指数函数30分；合计150分。
\par 主考点归类：集合1、15题共20分，逻辑2、3题共10分；基本不等式4题5分、不等式性质9题6分、恒成立12题5分、二次不等式16题15分；函数概念5、6、13题共15分，函数性质7、8、10、11、14、17题共44分；幂函数18题17分、指数函数19题13分。综合题允许知识交叉，归类用于统计，不将同一分数重复计入。
\par 教材页码指印刷页，正文PDF页序为印刷页加7。下列ID均可在教材题库中检索，改编题的答案已另行重算，不能直接套用母题答案。
'''
    s+=r'\par 未特别注明的改编均为更换数据与设问、保留教材母题的概念结构。逐题目标、预期方法、易错点及评价方式另见随附“命题细目与教材出处.csv”。'+'\n'
    s+=r'\small\begin{longtable}{@{}p{.045\linewidth}p{.925\linewidth}@{}}\toprule 题号&教材母题与改编说明\\\midrule\endhead'+'\n'
    for n,item in enumerate(items,1):
        s+=str(n)+' & '+'；'.join(r['brief']+f"（PDF第{r['pdf']}页）" for r in item['sources'])+r'\newline{\scriptsize\ttfamily\detokenize{'+ ' / '.join(r['id'] for r in item['sources'])+'}}'
        if not item['change'].startswith('变更数据与设问'):s+=r'\newline 改编：'+item['change']
        s+=r'\\[3pt]'+'\n'
    s+=r'\bottomrule\end{longtable}\normalsize'+'\n'
    s+=r'\par\textbf{评价与复习建议：}客观题逐项判断，填空题核对端点和可取性；解答题按列式、推理、分类完整性及结论评分。第17、18题重点观察能否从定义出发说明理由。上述难度与错误仅为教学预判，未经过班级试测，不预设均分或达标率。'+'\n'+r'\end{document}'+'\n'
    return s

def main():
    OUT.mkdir(exist_ok=True)
    (OUT/'排版设置.tex').write_text(STYLE,'utf-8')
    manifest=[]
    for key,items in PAPERS.items():
        assert len(items)==19
        for n,item in enumerate(items,1):
            assert item['text'].count('$')%2==0,(key,n)
            if n<=8:assert len(item['options'])==4 and len(item['answer'])==1
            if 9<=n<=11:assert len(item['options'])==4 and 1<len(item['answer'])<4
            item['sources']=[resolve(p) for p in item['source'].split(';')]
            manifest.append({'卷别':key,'题号':n,'题型':'单选' if n<=8 else '多选' if n<=11 else '填空' if n<=14 else '解答',
              '分值':POINTS[n-1],'主考点':MODULES[n-1],'母题ID':';'.join(r['id'] for r in item['sources']),
              '教材出处':';'.join(r['brief'] for r in item['sources']),'改编说明':item['change'],'预期方法':METHODS[n-1],
              '易错点':ERRORS[n-1],'预计难度':LEVELS[n-1],'评价方式':'答案与端点核对' if n<=14 else '按教师版分步评分'})
        folder=OUT/f'{key}卷';folder.mkdir(exist_ok=True)
        (folder/'排版设置.tex').write_text(STYLE,'utf-8')
        (folder/'main.tex').write_text(student(key,items),'utf-8')
        (folder/'教师版.tex').write_text(teacher(key,items),'utf-8')
    with (OUT/'命题细目与教材出处.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=manifest[0].keys());w.writeheader();w.writerows(manifest)
    assert sum(POINTS)==150
    print('Generated 3 student papers, 3 teacher editions, 57 source mappings; 150 points each.')

if __name__=='__main__':main()
