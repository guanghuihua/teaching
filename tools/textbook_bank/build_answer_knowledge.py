"""Build a non-destructive 368-item answer/knowledge companion and exam summary.

No OCR string becomes an answer. Editable answers and concept tags are curated in
answers_c01..04.txt and midterm_knowledge.py. Existing bank statements are read only.
"""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, re
from midterm_knowledge import KNOWLEDGE, GROUPS

ROOT=Path(__file__).resolve().parents[2]
BANK=ROOT/'题目积累/教材题库/湘教版必修第一册'
OUT=BANK/'答案与知识点'
CODE={'例题':'EX','练习':'PR','习题':'HW','复习题':'RV','思考':'TH','小结与复习':'SU','案例':'CA','数学实验':'LAB'}
# PDF page numbers, not printed pages. Locations are related answer GROUPS:
# old-version reordering means they are deliberately not claimed as exact item matches.
PRACTICE={4:[4],6:[4],8:[4],11:[4],16:[6],19:[6],21:[6],23:[6,7],
 34:[11],37:[11],40:[11],42:[11],47:[13],53:[14],55:[14],58:[14],
 67:[19],72:[19],76:[20],82:[22,23],84:[23],97:[30],100:[30],103:[30,31],108:[31],113:[31]}
GROUP_PAGES={(1,'习题1.1'):[4,5],(1,'习题1.2'):[7],(1,'复习题一'):[8,9],
 (2,'习题2.1'):[12,13],(2,'习题2.2'):[13,14],(2,'习题2.3'):[14,15],(2,'复习题二'):[15,16],
 (3,'习题3.1'):[20,21,22],(3,'习题3.2'):[23,24],(3,'复习题三'):[24,25,26,27],
 (4,'习题4.1'):[31],(4,'习题4.2'):[32]}

ANSWER_FIGURES={
 '1.HW.13.13':'C01-HW013-13','1.RV.30.17':'C01-RV030-17',
 '3.EX.71.5':'C03-EX071-5','3.PR.72.2':'C03-PR072-2','3.PR.72.3':'C03-PR072-3',
 '3.LAB.73.Y0145':'C03-LAB073','3.EX.75.7':'C03-EX075-7','3.EX.75.8':'C03-EX075-8',
 '3.PR.76.1':'C03-PR076-1','3.PR.76.3':'C03-PR076-3','3.HW.77.6':'C03-HW077-6',
 '3.HW.77.10':'C03-HW077-10','3.HW.78.16':'C03-HW078-16','3.HW.85.5':'C03-HW085-5-source',
 '3.RV.91.14':'C03-RV091-14','3.RV.91.15':'C03-RV091-15','3.RV.92.19':'C03-RV092-19',
 '4.PR.103.3':'C04-PR103-3','4.HW.104.8':'C04-HW104-8','4.EX.110.3':'C04-EX110-3',
 '4.EX.112.6':'C04-EX112-6','4.PR.113.1':'C04-PR113-1','4.HW.113.6':'C04-HW113-6',
 '4.HW.114.10':'C04-HW114-10','4.HW.114.15':'C04-HW114-15'}

ISSUES={
 '1.PR.4.1':('版本小问变化','答案册PDF4有五小问；现教材四小问，按原题的对象和符号作答。'),
 '1.PR.16.3':('版本小问变化','答案册PDF6只写“假命题”；现题要求写逆命题，逆命题为真，不能照抄。'),
 '1.HW.13.15':('版本条件变化','答案册PDF5中的B含负奇数；现教材k∈[0,3)，B={1,3,5}，补集相应变化。'),
 '1.HW.23.2':('版本题干变化','答案册PDF7第2题第3问为xy≠0的否定；现教材问二次函数与x轴的交点。'),
 '1.HW.23.3':('版本题号变化','现教材有独立的充分条件三问，答案册同组题号不能逐号对套。'),
 '1.HW.24.8':('逻辑强度提醒','题设只推出充分或必要，不能无依据增加“不必要”或“不充分”。'),
 '2.PR.53.1':('版本题组变化','答案册PDF14的p.53只列另一组六个不等式；现教材先问函数正负，再列六个不等式，须逐式求解。'),
 '2.PR.58.2':('原题条件不足','乙必超速；甲仅可推出v>30，要断言甲未超速需给出刹车距离上界。保持原题，不静默补条件。'),
 '2.HW.59.6':('整数限制提醒','提价参数为正整数，答案用70至180元且10元一档，不能仅给连续区间。'),
 '2.RV.62.10':('多选设问变化','现教材为多选，A、D均真；答案册PDF16只列A，不能照抄单选答案。'),
 '2.RV.62.13':('题给近似口径','按题给√21≈4.58代入，长边约30.5米，与答案册PDF16一致；用精确根值再舍入则为30.6米。保留精确式并注明口径，不把近似输入差异当成答案册笔误。'),
 '3.PR.67.1':('版本插题变化','答案册PDF19从定义域题开始，现教材先有判断对应是否为函数的一题，其余题号顺延。'),
 '3.PR.72.2':('读图估计非唯一','表内数据不能唯一确定中间函数值；保留答案册平滑曲线估计25、140，并给线性插值28、132及方法，均不当作精确值。'),
 '3.PR.72.3':('答案册方向笔误','答案册PDF19第3题第2问写f(x1)>f(x2)；在x1<x2<1时二次函数递增，正确为f(x1)<f(x2)。'),
 '3.HW.78.15':('定义域核验','三角形面积函数须排除A、O、P共线的路程0、8、16，不能把退化三角形包括进原问题。'),
 '3.HW.78.16':('特殊定义提醒','本题sign为0/1阶跃函数，按其定义组织表达式；原题200处需检验，不能直接用常见的-1/0/1符号函数。'),
 '3.PR.84.2':('版本插题变化','现教材增加多项式奇偶条件，答案册PDF23同组后面乘积、奇延拓题号与现题不同。'),
 '3.RV.91.12':('多选设问变化','现教材需写ABD，答案册PDF25按三个证明小问给解，须转换为逐项判断。'),
 '4.PR.113.1':('底数变化','答案册PDF31标p.112并作3^x图象；现教材p.113为5^x和5^(-x)，对称关系相同，作图点值必须更新。'),
 '4.HW.113.3':('近似值差异','16×0.9^9=6.198727824万元，通常保留两位小数为6.20；答案册PDF32写约6.19，现采用精确值舍入。'),
}

PREAMBLE=r'''% !TeX program = xelatex
\documentclass[UTF8,a4paper,zihao=-4,fontset=windows]{ctexart}
\usepackage[margin=21mm,headheight=15pt]{geometry}
\usepackage{amsmath,amssymb,graphicx,xcolor,needspace,longtable,booktabs,fancyhdr}
\usepackage[unicode,hidelinks]{hyperref}
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}
\setlength{\emergencystretch}{4em}
\linespread{1.13}\raggedbottom\raggedright
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{湘教版必修第一册：期中教师资料}
\fancyhead[R]{答案与知识点}\fancyfoot[C]{\thepage}
\graphicspath{{../TeX题库/}}
\newcommand{\subq}[1]{\par\Needspace{2\baselineskip}\noindent（#1）\quad}
\newcommand{\choice}[1]{\par\noindent #1.\quad}
\newcommand{\blank}{\underline{\hspace{1.3cm}}}
\newcommand{\bankfig}[2]{\begin{center}\includegraphics[width=#2\linewidth]{../TeX题库/figures/#1.png}\end{center}}
\newcommand{\itemhead}[2]{\par\Needspace{8\baselineskip}\medskip\hrule\smallskip\textbf{#1}\par{\footnotesize\ttfamily #2}\par}
\newcommand{\field}[2]{\par\textbf{#1：}#2\par}
\hypersetup{pdfauthor={教学资料整理}}
'''

def plain(s):
    escapes={'&':r'\&','%':r'\%','_':r'\_','#':r'\#','{':r'\{','}':r'\}',
             '^':r'\textasciicircum{}','$':r'\$','\\':r'\textbackslash{}',
             '∈':r'\ensuremath{\in}','≠':r'\ensuremath{\ne}','≈':r'\ensuremath{\approx}'}
    return ''.join(escapes.get(c,c) for c in str(s))

def shortkey(r):
    n=r['original_number']
    return f"{r['chapter']}.{CODE[r['type']]}.{r['printed_pages'][0]}.{n if n is not None else r['id'].split('-')[-1]}"

def read_answers():
    rows={}
    for c in range(1,5):
        for line in Path(__file__).with_name(f'answers_c0{c}.txt').read_text('utf-8').splitlines():
            if not line or line.startswith('#'):continue
            k,tags,answer=line.split('|',2)
            assert k not in rows,k
            tags=tags.split(',');assert all(t in KNOWLEDGE for t in tags),k
            rows[k]=(tags,answer)
    return rows

def statement(r):
    p=BANK/'TeX题库/questions'/f"{r['id']}.tex"
    s=p.read_text('utf-8').split(r'\begin{bankitem}',1)[1]
    return s[s.index('\n')+1:].split(r'\end{bankitem}',1)[0].strip()

def pages_text(pages):return '、'.join(map(str,pages))

def main():
    OUT.mkdir(exist_ok=True);(OUT/'answers').mkdir(exist_ok=True)
    source=json.loads((BANK/'题库数据.json').read_text('utf-8'))
    bank=[r for r in source['items'] if r['midterm_scope']]
    curated=read_answers();assert len(curated)==len(bank)==368
    assert {shortkey(r) for r in bank}==set(curated)
    manifest=[];chapters={c:[] for c in range(1,5)};md=[]
    for r in bank:
        k=shortkey(r);tags,answer=curated[k];kp=KNOWLEDGE[tags[0]]
        ref=PRACTICE[r['printed_pages'][0]] if r['type']=='练习' else GROUP_PAGES.get((r['chapter'],r['group']),[])
        printed=r['printed_pages'][0]
        location=f"湘教版教材p.{printed} / PDF第{printed+7}页 / {r['group']} / {r['original_label']}"
        if ref:
            origin='答案册相关题组：PDF第'+pages_text(ref)+'页（册内页'+pages_text([n-1 for n in ref])+'）；按当前题库原题逐项重算，不按旧版题号机械对套。'
            basis='参照答案册相关题组；按现教材重算'
        elif r['type']=='例题':
            origin=f'例题原解位置：湘教版教材p.{printed}及题库原图；独立编写可编辑参考解答。答案册此部分主要收练习、习题，不伪造例题答案册位置。'
            basis='教材例题原解参照；独立重算'
        else:
            origin='答案册未提供本栏目的独立对应答案；依据原题、教材概念补写参考回应。开放性总结不设唯一数值答案。'
            basis='教材概念依据；补写参考回应'
        related='；'.join(t+' '+KNOWLEDGE[t]['title']+'（教材帮p.'+pages_text(KNOWLEDGE[t]['guide_printed_pages'])+' / PDF'+pages_text(KNOWLEDGE[t]['guide_pdf_pages'])+'）' for t in tags)
        issue=ISSUES.get(k)
        title=f"{r['group']} · {r['original_label']}（教材p.{printed}）"
        # The original student-facing statement files are read, never rewritten.
        tex=r'\itemhead{'+plain(title)+'}{'+r['id']+'}\n'+r'\label{'+r['id']+'}\n'
        tex+=r'{\footnotesize '+plain(location)+'}\n'+r'\field{原题}{'+statement(r)+'}\n'
        tex+=r'\field{参考答案}{'+answer+'}\n'
        if k in ANSWER_FIGURES:
            figure='figures/'+ANSWER_FIGURES[k]+'.png';assert (OUT/figure).exists(),figure
            tex+=r'\begin{center}\includegraphics[width=.84\linewidth,height=.38\textheight,keepaspectratio]{'+figure+'}'+r'\end{center}'+'\n'
            if k=='3.HW.85.5':tex+=r'{\footnotesize 补图来源：所给答案册PDF第24页（册内23页），已核对对应关系。}\par'+'\n'
            if k=='3.PR.72.2':tex+='图为相邻数据的线性插值示例，非唯一的真实库容曲线。\\par\n'
        if issue:tex+=r'\field{核对说明}{'+plain(issue[0]+'：'+issue[1])+'}\n'
        tex+=r'{\small '+r'\field{关联知识}{'+plain(related)+'}\n'
        tex+=r'\field{方法与易错点}{'+kp['method'].replace('%',r'\%')+' 易错：'+kp['likely_error'].replace('%',r'\%')+'}\n'
        tex+=r'\field{答案依据}{'+plain(origin)+'}}\n'
        (OUT/'answers'/f"{r['id']}.tex").write_text(tex,'utf-8')
        chapters[r['chapter']].append(r'\input{answers/'+r['id']+'.tex}')
        difficulty='综合（备课预判）' if r['type'] in ['习题','复习题'] and (len(tags)>1 or len(answer)>220) else '基础至中等（备课预判）'
        record=dict(id=r['id'],key=k,chapter=r['chapter'],group=r['group'],original_number=r['original_label'],
         textbook_printed_page=printed,textbook_pdf_page=printed+7,statement_tex='../TeX题库/questions/'+r['id']+'.tex',
         answer_tex='answers/'+r['id']+'.tex',answer=answer,answer_basis=basis,answer_reference_pdf_pages=ref,
         answer_figure='figures/'+ANSWER_FIGURES[k]+'.png' if k in ANSWER_FIGURES else '',
         answer_reference_relation='相关题组参考；非逐号匹配' if ref else '不适用',
         knowledge_ids=tags,knowledge=related,target_concept='；'.join(KNOWLEDGE[t]['title'] for t in tags),
         expected_method=kp['method'],likely_error=kp['likely_error'],expected_difficulty=difficulty,assessment=kp['assessment'],
         issue_type=issue[0] if issue else '',issue_note=issue[1] if issue else '',
         answer_status='已编写并验算的教师参考答案；未获教师签核',teacher_approved=False,
         classroom_use='原题条件不足，组卷前需教师补条件' if k=='2.PR.58.2' else '教师复核后使用')
        manifest.append(record)
        md.extend([f"### {title}",f"`{r['id']}`",'',f"原题：[可编辑题干]({record['statement_tex']})；教材印刷p.{printed} / PDF第{printed+7}页。",'',
          '**参考答案：** '+answer,'','**相关知识点：** '+related,'','**预期方法：** '+kp['method'],'','**易错点：** '+kp['likely_error'],'',
          '**答案依据：** '+origin,''])
        if issue:md.extend(['**核对说明：** '+issue[0]+'；'+issue[1],''])
    (OUT/'逐题答案与知识点.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
    fields=['id','key','chapter','group','original_number','textbook_printed_page','textbook_pdf_page','answer','answer_basis','answer_reference_pdf_pages','answer_reference_relation','knowledge_ids','knowledge','target_concept','expected_method','likely_error','expected_difficulty','assessment','issue_type','issue_note','answer_status','teacher_approved','classroom_use','answer_tex','statement_tex','answer_figure']
    with (OUT/'逐题答案与知识点.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in manifest:w.writerow({k:(';'.join(map(str,r[k])) if isinstance(r[k],list) else r[k]) for k in fields})
    md_intro=['# 期中教材题库逐题答案与知识点','',
     '范围：湘教版必修第一册第1—3章及4.1—4.2（教材至114页），368个主标签条目或题组，小问不拆分。原题与学生卷未修改，答案单独保存在教师配套资料。',
     '', '答案为参照原书重新编写的可编辑参考答案；答案册旧版题号并非一一对应。思考、小结、案例及实验另写参考回应；未冒充答案册原解。',
     '', '每个知识标签均对应[期中知识点总表](期中知识点总表.md)；《教材帮》按内容映射，不按其章号移植。PDF页序为书内页码加9，答案册PDF页序为册内页码加1。',
     '', '所有条目仍待教师签核；原题条件不足或非唯一估计等记录见[版本差异与复核记录](版本差异与复核记录.csv)。', '']
    (OUT/'逐题答案与知识点.md').write_text('\n'.join(md_intro+md),'utf-8')
    with (OUT/'版本差异与复核记录.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','key','issue_type','issue_note','classroom_use']);w.writeheader()
        for r in manifest:
            if r['issue_type']:w.writerow({k:r[k] for k in w.fieldnames})
    with (OUT/'review-items.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','key','reason','status']);w.writeheader()
        for k in ['2.PR.58.2','3.PR.72.2']:
            r=next(r for r in manifest if r['key']==k)
            w.writerow(dict(id=r['id'],key=k,reason=r['issue_note'],status='教师需确认条件或估计口径；不作为唯一标准答案直接发放'))
    # Deliberately separate this teacher companion from the existing open bank project.
    (OUT/'排版设置.tex').write_text(PREAMBLE,'utf-8')
    intro=r'''\input{排版设置.tex}
\begin{document}
\begin{center}{\LARGE 期中教材题库：答案与知识点}\par\medskip
{\large 湘教版必修第一册第1—3章、4.1—4.2}\end{center}
本册为教师配套资料，共368个主标签条目（第1章107、第2章104、第3章92、第4章期中部分65）。题干、答案与数学公式均可编辑，必要原配图单独引用。学生卷及原题库未改动。
\par 252个练习、习题和复习题参照所给答案册的相关题组重新计算；70个例题参考教材原解；其余46个思考、小结、案例、实验补写参考回应。答案册有旧版小问及题号变化，不将相关题组伪装成逐题完全匹配。证明题给出关键推理，作图题给出解析式、关键点或明确作图规则；另附25幅答案图，其中24幅按数学关系绘制，1幅为已核对的答案册补图。
\par 知识点依所给《教材帮》的实际内容匹配，其章节与湘教版不同（例如幂函数位于教材帮第3章），不可直接按章号对套。每条给出书内页码及PDF页序；知识总表另册按本次考试范围整理。
\par 本册是编写并验算的教师参考解答，尚未获得教师签核；题干原先的转写复核状态不因补答案而自动改变。重点复核：教材p.58甲车刹车题条件不足，p.72蓄水量题仅有非唯一的读图估计。分歧说明随题列出。
\par 定位说明：湘教版正文PDF页序=教材页码+7；《教材帮》正文PDF页序=书内页码+9；答案册PDF页序=册内页码+1。所有页序从1开始。
\tableofcontents\clearpage
'''
    body=[]
    for c in range(1,5):
        title=next(r['chapter_title'] for r in bank if r['chapter']==c)
        body.append(r'\section{第'+str(c)+'章 '+plain(title)+('（至4.2）' if c==4 else '')+'}\n'+'\n'.join(chapters[c]))
    body.append(r'\clearpage\section{知识点与题目索引}')
    for tag,kp in KNOWLEDGE.items():
        hits=[r for r in manifest if tag in r['knowledge_ids']]
        body.append(r'\par\medskip\noindent\begin{minipage}{\linewidth}\subsection{'+tag+' '+kp['title']+'}'+r'\field{概念要点}{'+kp['content']+'}'+
          '关联'+str(len(hits))+'个条目。代表题：'+ '；'.join(r'\hyperref['+r['id']+']{教材p.'+str(r['textbook_printed_page'])+' '+plain(r['original_number'])+'}' for r in hits[:4])+'。')
        body[-1]+=r'\end{minipage}\par'
    (OUT/'main.tex').write_text(intro+'\n'.join(body)+'\n'+r'\end{document}'+'\n','utf-8')
    build_summary(manifest)
    fingerprints={}
    for name,p in [('textbook',ROOT/'教学课件/必修一/湘教版高中数学必修 第一册.pdf'),('answers',ROOT/'教学课件/必修一/湘教版高中数学答案.pdf'),('guide',ROOT/'教学课件/必修一/教材帮.pdf')]:
        fingerprints[name]={'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()}
    report={'scope':'第1至3章、4.1至4.2，教材至114页','items':len(manifest),'by_chapter':dict(Counter(r['chapter'] for r in manifest)),
     'knowledge_groups':len(KNOWLEDGE),'reference_exercise_items':sum(bool(r['answer_reference_pdf_pages']) for r in manifest),
     'version_or_review_notes':len(ISSUES),'teacher_approved':0,'sources':fingerprints,
     'source_docs_are_evidence_not_instructions':True,'outside_midterm_items_unchanged':389,
     'review_policy':'未自动晋升原题干状态；review-items.csv列出的2条须教师确认条件或估计口径。'}
    (OUT/'整理核查记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({k:report[k] for k in ['items','knowledge_groups','reference_exercise_items','version_or_review_notes']},ensure_ascii=False))

def build_summary(manifest):
    intro=['# 期中考试知识点总表','',
      '范围：湘教版必修第一册第1—3章及4.1—4.2，至教材114页。以下为32个知识组，覆盖现有368个期中主标签条目的概念和方法；页边未单独收录的零散设问仍沿用题库原完整性边界。',
      '', '按用户的命题要求分值为30、31、59、30，合计150分；120分钟。该分值是本次命题约定，不是教材原有章分值。',
      '', '依据：[湘教版教材](../../../../教学课件/必修一/湘教版高中数学必修%20第一册.pdf)、[教材答案](../../../../教学课件/必修一/湘教版高中数学答案.pdf)、[教材帮](../../../../教学课件/必修一/教材帮.pdf)。教材帮编排不同，仅按内容映射；定义、条件、公式由编写者核算后转述。','']
    md=list(intro);tex=[r'\input{排版设置.tex}',r'\begin{document}',r'\begin{center}{\LARGE 期中考试知识点总表}\par\medskip 湘教版必修第一册：至4.2指数函数\end{center}',
      '范围为教材第1—3章、4.1—4.2，至114页。32个知识组关联368个题库条目；以函数为主线，集合与逻辑为工具，不等式为手段。分值30、31、59、30为本次命题约定，120分钟、150分。',
      '本表按所给《教材帮》概念栏目重新归纳，保留其书内页码及PDF位置。章节次序以湘教版为准；L01命题定义另用湘教版14—16页补充。《教材帮》中的对数、导数、三角函数、函数凹凸性等不列作本次新增考查要求。',
      r'\tableofcontents\clearpage']
    for title,tags in GROUPS:
        md+=['## '+title,''];tex+=[r'\section{'+title+'}']
        for tag in tags:
            k=KNOWLEDGE[tag];hits=[r for r in manifest if tag in r['knowledge_ids']]
            ref='《教材帮》书内p.'+pages_text(k['guide_printed_pages'])+'；PDF第'+pages_text(k['guide_pdf_pages'])+'页'
            examples='；'.join('教材p.'+str(r['textbook_printed_page'])+' '+r['group']+' '+r['original_number'] for r in hits[:3])
            md+=['### '+tag+' '+k['title'],'',k['content'],'','- 预期方法：'+k['method'],'- 常见错误：'+k['likely_error'],'- 达标证据：'+k['assessment'],'- 来源：'+ref,'- 关联'+str(len(hits))+'题；例如：'+examples,'']
            tex += [r'\par\medskip\noindent\begin{minipage}{\linewidth}\subsection{'+tag+' '+k['title']+'}',k['content'],
             r'\field{预期方法}{'+k['method'].replace('%',r'\%')+'}',r'\field{常见错误}{'+k['likely_error'].replace('%',r'\%')+'}',
             r'\field{达标证据}{'+k['assessment']+'}',r'{\small '+plain(ref+'。关联'+str(len(hits))+'题；例如：'+examples)+r'}\par\end{minipage}\par']
    end=r'''复习顺序建议：先核查集合元素、论域、定义域这些对象条件；再练表示法互换和函数求值；继而用任意两点作差证明单调性，用定义域对称与恒等式判奇偶；最后以配方、基本不等式和指数单调性处理最值、参数与模型。每道题核对“条件—结论—方法—端点”四项。
本次不新加对数及其运算、对数函数、导数、三角函数。教材原题里出现三角形或扇形等初中几何背景，可调用题给公式和初中几何，不据此扩张考查范围。指数模型中的 $\mathrm e$ 可按给定正常数与幂运算处理，不必引入对数。
教师复核时优先查：p.58甲车是否超速的条件不足；p.72插值与平滑读图的非唯一性；整数产量和价格档位；分母禁点；重根与降次；严格不等号；奇偶定义域；离散指数模型的起始时刻。'''
    md+=['## 复习顺序与范围边界','',end,''];tex += [r'\par\medskip\noindent\begin{minipage}{\linewidth}\section{复习顺序与范围边界}',end,r'\end{minipage}',r'\end{document}']
    (OUT/'期中知识点总表.md').write_text('\n'.join(md),'utf-8')
    (OUT/'期中知识点总表.tex').write_text('\n'.join(tex)+'\n','utf-8')
    (OUT/'知识点目录.json').write_text(json.dumps(KNOWLEDGE,ensure_ascii=False,indent=2),'utf-8')

if __name__=='__main__':main()
