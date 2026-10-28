"""Structural checks plus independently calculated algebra and boundary cases.

Sampling supports the written proofs; it is not a proof or teacher sign-off.
"""
from pathlib import Path
from collections import Counter
import csv, hashlib, json, re
import sympy as s
import pymupdf
from build_answer_knowledge import ROOT, BANK, OUT, KNOWLEDGE, shortkey, read_answers

def main():
    checks=[]
    def check(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(name)
    rows=json.loads((OUT/'逐题答案与知识点.json').read_text('utf-8'))
    bank=json.loads((BANK/'题库数据.json').read_text('utf-8'))['items']
    expected={r['id'] for r in bank if r['midterm_scope']}
    check('368 unique current-source IDs',len(rows)==len({r['id'] for r in rows})==368 and {r['id'] for r in rows}==expected)
    check('chapter counts',Counter(r['chapter'] for r in rows)=={1:107,2:104,3:92,4:65})
    check('32 knowledge groups',len(KNOWLEDGE)==32)
    check('252 related answer groups',sum(bool(r['answer_reference_pdf_pages']) for r in rows)==252)
    check('no invented teacher approval',not any(r['teacher_approved'] for r in rows))
    for r in rows:
        check(r['id']+' complete fields',bool(r['answer']) and bool(r['knowledge_ids']) and bool(r['expected_method']) and bool(r['likely_error']) and bool(r['assessment']))
        check(r['id']+' linked sources',(OUT/r['statement_tex']).exists() and (OUT/r['answer_tex']).exists())
        check(r['id']+' no control characters',not any(ord(c)<32 and c not in '\n\t' for c in r['answer']))
        check(r['id']+' known concepts',all(k in KNOWLEDGE for k in r['knowledge_ids']))
        check(r['id']+' editable answer delimiters',r['answer'].count('$')%2==0)
        if r['answer_figure']:check(r['id']+' answer figure',(OUT/r['answer_figure']).is_file())
    check('25 separately saved answer figures',len(list((OUT/'figures').glob('*.png')))==25)
    check('all 32 concepts used',set(KNOWLEDGE)==set(k for r in rows for k in r['knowledge_ids']))
    x,a,b,c,d,m=s.symbols('x a b c d m',real=True)
    def identity(name,lhs,rhs=0):check(name,s.simplify(lhs-rhs)==0)
    identity('2.HW.43.1 difference',(2*a+1)*(a-3)-((a-6)*(2*a+7)+45),-6)
    identity('2.PR.34.1 first difference',(x+1)*(x-3)-(x+2)*(x-4),5)
    identity('2.PR.34.1 second difference',(x*x-1)**2-(x**4-x*x+1),-x*x)
    identity('2.PR.34.1 third difference',x*x+a*a+1-2*(x+a-1),(x-1)**2+(a-1)**2+1)
    identity('2.PR.34.2 rational difference',a/(a-1)-b/(b-1),(b-a)/((a-1)*(b-1)))
    identity('2.PR.40.2 squares',a*a+b*b+c*c-a*b-b*c-a*c,((a-b)**2+(b-c)**2+(c-a)**2)/2)
    identity('2.RV.61.1 fourth proof',(x*x-6*x+5)/(x*x+2*x+1)+s.Rational(1,3),4*(x-2)**2/(3*(x+1)**2))
    identity('2.RV.61.3 second proof',a*(b*b+c*c)+b*(c*c+a*a)+c*(a*a+b*b)-6*a*b*c,a*(b-c)**2+b*(c-a)**2+c*(a-b)**2)
    identity('2.RV.63.16 first proof',a**3+b**3-a*b*b-a*a*b,(a-b)**2*(a+b))
    identity('2.RV.63.16 second proof',a**4+b**4-a*b**3-a**3*b,(a-b)**2*(a*a+a*b+b*b))
    identity('2.EX.57.9 complete square',90000*(5+1/x-3/x**2),457500-270000*(1/x-s.Rational(1,6))**2)
    identity('2.EX.56.8 loaded braking boundary',s.Rational(5,162)*18**2+s.Rational(5,18)*18,15)
    identity('2.HW.59.9 fee threshold',s.factor((80*x*(8-s.Rational(62,100)*x)/(100-x)-16)*(100-x)),s.Rational(-8,5)*(31*x*x-410*x+1000))
    # Exact solution sets calculated from original inequalities, not from answer text.
    sets=[('2.EX.52.1',2*x*x-x-3>=0,s.Union(s.Interval(-s.oo,-1),s.Interval(s.Rational(3,2),s.oo))),
      ('2.EX.52.2',4*x*x-4*x+1>0,s.S.Reals-s.FiniteSet(s.Rational(1,2))),
      ('2.EX.53.3',-x*x+4*x-5>0,s.S.EmptySet),
      ('2.PR.53.2 first',x*(x-2)>0,s.Union(s.Interval.open(-s.oo,0),s.Interval.open(2,s.oo))),
      ('2.PR.53.2 last',16-24*x<=-9*x*x,s.FiniteSet(s.Rational(4,3))),
      ('2.PR.55.1 second',(x+1)/(3*x-2)>=2,s.Interval(s.Rational(2,3),1,left_open=True)),
      ('2.HW.59.5 first',1/x>4,s.Interval.open(0,s.Rational(1,4))),
      ('2.HW.59.5 second',1/(2-x)<=3,s.Union(s.Interval(-s.oo,s.Rational(5,3)),s.Interval.open(2,s.oo))),
      ('2.RV.61.5 fourth',s.And(-1<2*x*x-x-2,2*x*x-x-2<1),s.Union(s.Interval.open(-1,s.Rational(-1,2)),s.Interval.open(1,s.Rational(3,2))))]
    for name,rel,result in sets:
        got=s.reduce_inequalities(list(rel.args),x).as_set() if isinstance(rel,s.And) else s.solve_univariate_inequality(rel,x,relational=False)
        check(name+' exact solution',got==result)
    # Enumerations and independent arithmetic.
    check('1.HW.13.10 nine ordered pairs',sum(1 for i in range(5) for j in range(5) if i+j in range(5) and i-j in range(5))==9)
    check('1.HW.13.15 actual current B',{2*k+1 for k in range(3)}=={1,3,5})
    check('3.HW.77.3 exact sum',sum(s.Rational(t,t+1) for t in [1,2,3])+s.Rational(1,3)+s.Rational(1,4)==s.Rational(5,2))
    identity('3.PR.72.1 actual area',(x+6)*(432/x+8),8*x+480+2592/x)
    identity('3.EX.69.4 actual dam area',(30+30+4*x)*x/2,2*x*x+30*x)
    check('3.EX.74.6 charges reconstruct 330',sum([(114+93)/1.5,(75+93)/1.5,45.6/.57])==330)
    identity('3.HW.77.6 vertex form',3*x*x-5*x+2,3*(x-s.Rational(5,6))**2-s.Rational(1,12))
    check('2.RV.62.13 rounding convention',round(float(20*s.sqrt(21)/3),1)==30.6 and round(20*4.58/3,1)==30.5)
    check('4.HW.113.3 price rounding',round(16*.9**9,2)==6.20)
    identity('4.EX.96.2 negative fractional exponent',(s.Rational(125,64))**s.Rational(-2,3),s.Rational(16,25))
    identity('4.PR.97.3 exponent sum',s.Rational(4,5)+s.Rational(3,4)-s.Rational(7,5),s.Rational(3,20))
    identity('4.HW.104.5 exact arithmetic',-s.Rational(2,3)+s.Rational(11,3)-3/(16**s.Rational(-3,4))+2,-19)
    check('4.EX.108.2 correct six-decimal approximation',round(.568**12,6)==.001128)
    check('4.HW.114.10 negative root bracket',(2**(-.767)-(-.767)**2)*(2**(-.766)-(-.766)**2)<0)
    check('4.HW.114.10 known exact intersections',all((2**x-x*x).subs(x,r)==0 for r in [2,4]))
    # Boundary-heavy parameter questions; these samples supplement the written proofs.
    grid=[s.Rational(i,4) for i in range(-24,25)]
    for av in [-4,-3,-2,-1,0,1,2,3,4]:
        for xx in grid:
            identity(f'2.HW.59.8 factor m={av} x={xx}',(x*x-(2*m+1)*x+m*m+m).subs({m:av,x:xx}),((x-m)*(x-m-1)).subs({m:av,x:xx}))
    for mv in [-2,0,7,s.Rational(799,100),8,9,16]:
        deltas=[(2*y+mv/y)-(2*x0+mv/x0) for x0 in [s.Rational(1,2),1,s.Rational(19,10),s.Rational(19999,10000)] for y in [s.Integer(2)] if x0<y]
        check(f'3.RV.92.16 m={mv} sample',all(z<0 for z in deltas) if mv>=8 else any(z>0 for z in deltas))
    for r in rows:
        check(r['id']+' no empty or inherited OCR answer','ocrdraft' not in r['answer'] and r['answer'].strip() not in ['略','略。'])
    # Generated PDF and references are checked against final delivered copies.
    pdfinfo=[];texts=[]
    for stem in ['期中教材题库_答案与知识点','期中知识点总表']:
        p=OUT/(stem+'.pdf');doc=pymupdf.open(p);text='\n'.join(page.get_text() for page in doc);texts.append(text)
        check(stem+' has pages',len(doc)>0)
        check(stem+' A4 pages',all(abs(p.rect.width-595.28)<2 and abs(p.rect.height-841.89)<2 for p in doc))
        pdfinfo.append({'file':p.name,'pages':len(doc),'size':p.stat().st_size})
    for r in rows:check(r['id']+' visible in teacher PDF',r['id'] in texts[0])
    for tag in KNOWLEDGE:check(tag+' visible in summary',tag in texts[1])
    report={'checks_passed':len(checks),'items':len(rows),'knowledge_groups':len(KNOWLEDGE),'documents':pdfinfo,
      'meaning':'结构、来源路径、全部ID、图件与若干关键算式/边界的程序检查；不代替逐题推理或教师签核。',
      'teacher_approved':0,'review_items':2,'proofs_and_open_responses':'368条参考答案含逐题关键推理或开放回应；作图题附图或关键点/作图规则。'}
    (OUT/'验算与交付核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
