"""Check paper structure and independently calculated boundary/parameter cases.

These checks support the recorded item-by-item mathematical review; sampled
identities do not substitute for the proofs printed in each teacher edition.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import math,re,json,csv
import pypdfium2 as pdfium
from midterm_papers_data import PAPERS
from build_midterm_papers import OUT,POINTS,MODULES,resolve,ROOT

def main():
    audit=[]
    def check(label,condition):
        assert condition,label
        audit.append(label)
    expected={
      'A':['B','A','D','C','B','A','C','D','AB','ABD','ABD',r'$(4,+\infty)$',r'$3$',r'$[4,+\infty)$'],
      'B':['C','B','A','D','C','B','A','D','AC','AB','BCD',r'$(-\infty,-1]$',r'$1$',r'$f(-2)<f(1)<f(3)$'],
      'C':['D','C','B','A','D','C','B','A','AB','BC','AB',r'$[-3,3]$',r'$1$',r'$[-1,3]$'],
      'D':['C','A','D','B','C','A','D','B','AC','ABD','AB',r'$[9,+\infty)$',r'$1$',r'$[-2,2]$']}
    check('A1 intersection',{1,2,3,5}&{2,4,5}=={2,5})
    check('B1 union',{0,1,3}|{1,2,3,4}=={0,1,2,3,4})
    check('A4 attained minimum',F(4)+F(9,3)==7)
    check('B4 attained minimum',3**2+3**2==18)
    check('C4 attained maximum',4*(8-4)==16)
    check('A7 odd evaluation',-(2**2+2*2)==-8)
    check('B7 even evaluation',3**2-4*3+1==-2)
    check('C7 odd evaluation',5+2*(-5)==-5)
    check('D1 complement intersection',{0,2,4}&({0,1,2,3,4,5}-{1,2,3})=={0,4})
    check('D4 attained minimum',2*F(4)+F(8,2)==12)
    check('D7 even evaluation',(2*2+1)-(1*1+1)==3)
    check('D13 translated argument',2*(3-2)-1==1)
    check('D18 exact power arithmetic',F(16)-F(1,4)==F(63,4))
    f={1:3,2:1,3:2};check('A13 table composition',f[f[2]]==3)
    f=lambda x:x+2 if x<=0 else x*x;check('B13 branch composition',f(f(-1))==1)
    f=lambda x:2-2*x if 0<=x<=1 else x-1;check('C13 graph composition',f(f(0))==1)
    check('Power arithmetic exact values',F(4)+F(1,9)==F(37,9) and F(8)+F(1,4)==F(33,4) and F(27)+F(1,5)==F(136,5))
    # Interior, root and exterior points, including the repeated-root parameter.
    for m in map(F,[-4,0,1,2,3,5]):
      for x in map(F,[-6,-4,-1,0,1,2,3,5,7]):
        for k,root,sign in [('A',F(1),'<'),('B',F(2),'>='),('C',F(3),'>')]:
          v=x*x-(m+root)*x+m*root
          actual=v<0 if sign=='<' else v>=0 if sign=='>=' else v>0
          lo,hi=sorted([m,root])
          predicted=(lo<x<hi) if k=='A' else (x<=lo or x>=hi) if k=='B' else (x<lo or x>hi)
          check(f'{k}16 m={m} x={x}',actual==predicted)
    for key,bound in [('A',2),('C',3)]:
      f=lambda x:(2*abs(x)-x*x) if key=='A' else (x*x-4*abs(x)+1)
      grid=[F(i,10) for i in range(-10*bound,10*bound+1)]
      vals=[f(x) for x in grid]
      check(key+'17 even identity',all(f(-x)==f(x) for x in grid))
      check(key+'17 extrema', (min(vals),max(vals))==((0,1) if key=='A' else (-3,1)))
      check(key+'17 all extremum points',[x for x in grid if f(x)==min(vals)]==([F(-2),F(0),F(2)] if key=='A' else [F(-2),F(2)]))
    f=lambda x:x*x+2*x if x>=0 else -x*x+2*x
    g=[F(i,5) for i in range(-30,31)]
    check('B17 global monotonicity including zero',all(f(a)<f(b) for a,b in zip(g,g[1:])))
    for x in [F(i,4) for i in range(-20,29)]:
      check(f'A19 x={x}',(F(1,3)**abs(x-2)>=F(1,27)-1e-12)==(-1<=x<=5))
      check(f'B19 x={x}',(2.0**float(abs(2*x+1))<=8+1e-12)==(-2<=x<=1))
    check('C19 measured value and threshold',100*F(1,2)**2==25 and 100*F(1,2)**3==F(25,2))
    for m in map(F,[-5,-3,-2,-1,0,4]):
      for x in map(F,[-6,-5,-3,-2,-1,0,1,4,6]):
        lo,hi=sorted([m,F(-2)])
        check(f'D16 m={m} x={x}',(x*x-(m-2)*x-2*m<=0)==(lo<=x<=hi))
    grid=[F(i,10) for i in range(-30,31)]
    f=lambda x:x*x-2*abs(x)+3
    check('D17 even identity',all(f(-x)==f(x) for x in grid))
    check('D17 all extremum points',min(map(f,grid))==2 and max(map(f,grid))==6 and [x for x in grid if f(x)==2]==[F(-1),F(1)] and [x for x in grid if f(x)==6]==[F(-3),F(3)])
    positive=[F(i,10) for i in range(10,31)]
    check('D17 increasing on [1,3]',all(f(a)<f(b) for a,b in zip(positive,positive[1:])))
    for t in map(F,[-4,-2,-1,0,1,3,4]):
      probes=set(map(F,[-5,-4,-3,-2,-1,0,1,2,3,4,5,6]))|{t,(t-1)/2,(t+3)/2}
      actual=all(((-1<=x<=3) or (t<x<=5))==(-1<=x<=5) for x in probes)
      check(f'D15 t={t}',actual==(-1<=t<=3))
    for x in grid:
      check(f'D19 x={x}',(2.0**float(x)-2<=6+1e-12)==(x<=3))
    # Mark allocation is checked independently of the printed solutions.
    parts={15:[9,6],16:[6,9],17:[4,5,8],18:[4,5,8],19:[3,6,4]}
    for n,allocation in parts.items():check(f'Question {n} scoring',sum(allocation)==POINTS[n-1])
    mapping={'集合':'集合与逻辑','逻辑':'集合与逻辑','基本不等式':'不等式','不等式性质':'不等式','恒成立':'不等式','二次不等式':'不等式','函数概念':'函数','函数性质':'函数','幂函数':'幂指数','指数函数':'幂指数'}
    counts=Counter()
    for tag,p in zip(MODULES,POINTS):counts[mapping[tag]]+=p
    check('module points',dict(counts)=={'集合与逻辑':30,'不等式':31,'函数':59,'幂指数':30})
    documents=[]
    for key,items in PAPERS.items():
      check(key+' objective keys',[i['answer'] for i in items[:14]]==expected[key])
      check(key+' question count and points',len(items)==19 and sum(POINTS)==150)
      for item in items:
        for spec in item['source'].split(';'):resolve(spec)
      folder=OUT/f'{key}卷'
      student=(folder/'main.tex').read_text('utf-8')
      check(key+' no teacher material in student source',not any(s in student for s in ['\\ans{','评分细则','\\textbf{答案','预计难度','易错点','\\src{','XJ-B1-']))
      check(key+' continuous question numbers',[int(x) for x in re.findall(r'\\q\{(\d+)\}',student)]==list(range(1,20)))
      check(key+' only five answer areas',student.count('\\work{')==5)
      for name in ['main','教师版']:
        log=(ROOT/f'tmp/midterm_three/{key}/{name}.log').read_text('utf-8',errors='replace')
        check(key+name+' clean compilation',not re.search(r'^!|Overfull|Underfull|Missing character|^LaTeX Warning|^Package .* Warning',log,re.M))
        filename=f'{key}卷_学生卷.pdf' if name=='main' else f'{key}卷_教师版.pdf'
        doc=pdfium.PdfDocument(str(folder/filename))
        check(key+name+' four A4 pages',len(doc)==4 and all(abs(doc[i].get_size()[0]-595)<2 and abs(doc[i].get_size()[1]-842)<2 for i in range(len(doc))))
        extracted='\n'.join(doc[i].get_textpage().get_text_range() for i in range(len(doc)))
        if name=='main':check(key+' student PDF has no answers or sources',not any(s in extracted for s in ['答案速查','评分细则','教材改编出处','教材来源','XJ-B1-']))
        else:
          for item in items:
            for spec in item['source'].split(';'):
              check(key+' teacher retains source '+spec,resolve(spec)['id'] in extracted)
        documents.append({'paper':key,'edition':name,'pages':len(doc),'pdf':str((folder/filename).relative_to(OUT))})
    report={'papers':len(PAPERS),'questions':sum(len(items) for items in PAPERS.values()),'points_per_paper':150,'module_points':dict(counts),'checks_passed':len(audit),
      'documents':documents,'student_source_labels':False,'teacher_source_labels':True,'mathematical_review':'76题逐题独立验算；选择题逐项判断，参数题分类、定义域与端点已检查；数值检查仅支持证明，不代替证明。',
      'limitations':'预计难度与易错点未经班级试测；未预设均分、达标率。',
      'teacher_approval_claimed':False}
    (OUT/'数学与排版核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({'checks':len(audit),'PDFs':len(documents),'pages_each':4,'items':sum(len(items) for items in PAPERS.values()),'points_each':150},ensure_ascii=False))

if __name__=='__main__':main()
