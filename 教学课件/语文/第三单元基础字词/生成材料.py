# -*- coding: utf-8 -*-
"""使用 Codex 附带 Python 运行；临时渲染文件位于仓库 tmp/unit3。"""
from pathlib import Path
import re, json, hashlib, shutil
from html import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER
from pypdf import PdfReader, PdfWriter
from 内容数据 import UNITS, NOTES

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
TMP=ROOT/'tmp'/'unit3'
SOURCE=Path(r'D:\guanghui\AI读取\第三单元基础字词.pdf')
TMP.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('Song',r'C:\Windows\Fonts\simsun.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('Hei',r'C:\Windows\Fonts\simhei.ttf'))
pdfmetrics.registerFontFamily('Song',normal='Song',bold='Hei',italic='Song',boldItalic='Hei')
ST={
 'title':ParagraphStyle('title',fontName='Hei',fontSize=20,leading=29,spaceAfter=10),
 'unit':ParagraphStyle('unit',fontName='Hei',fontSize=15,leading=24,spaceBefore=8,spaceAfter=6,keepWithNext=True),
 'group':ParagraphStyle('group',fontName='Hei',fontSize=12,leading=20,spaceBefore=10,spaceAfter=4,keepWithNext=True),
 'body':ParagraphStyle('body',fontName='Song',fontSize=11,leading=18,spaceAfter=3,wordWrap='CJK'),
 'small':ParagraphStyle('small',fontName='Song',fontSize=9,leading=14,spaceAfter=4,textColor=colors.HexColor('#555555'),wordWrap='CJK'),
}
def P(t,style='body'):
    return Paragraph(t.replace('\n','<br/>'),ST[style])
def plain(t): return re.sub(r'</?b>','',t)
def md(t): return t.replace('<b>','**').replace('</b>','**')
def filled(q,a,g):
    if '识记字音' in g:
        vals=a.split('；')
        for v in vals: q=q.replace('(　　)','(<b>'+v+'</b>)',1)
        return q
    if '辨识字形' in g:
        ch=a.split('；')[0]
        q=q.replace('______','<b>'+ch+'</b>')
        if '拾' in q: q+='（duō）'
        return q
    if '古今异义' in g:
        result=q.replace('____________','<b>'+a.split('补充今义：')[0].replace('古义：','')+'</b>',1)
        if '补充今义：' in a: result+='\n补充今义：'+a.split('补充今义：')[1]
        # 原稿讹字只在保真题库留存；背诵版明确更正。
        if '鼓出来' in result:
            result='4.铁骑<b>突出</b>刀枪鸣\n古义：<b>突然冲出。</b>\n今义：凸出来；也指显著、超过一般。'
        return result
    if '文言句式' in g:
        return q.split('(　　)')[0]+'\n'+a
    if '词语积累' in g:
        return q.split('.')[0]+'.'+a
    return re.sub(r'\(　　\)','',q)+'　<b>'+a+'</b>'

def footer(canvas,doc):
    canvas.saveState(); canvas.setFont('Song',9); canvas.setFillColor(colors.HexColor('#555555'))
    canvas.drawString(46,25,'高中语文必修上册  第三单元基础字词')
    canvas.drawRightString(549,25,str(doc.page)); canvas.restoreState()
def document(path,story,title):
    doc=SimpleDocTemplate(str(path),pagesize=(595.276,841.89),rightMargin=46,leftMargin=46,topMargin=40,bottomMargin=44,title=title,author='教学资料整理')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)

def add_rows(story,g,answer=False):
    rows=g['rows']
    if '识记字音' in g['title'] or '辨识字形' in g['title']:
        # 每行三项，不使用边框表格；多音字仍保留字头。
        for i in range(0,len(rows),3):
            parts=[filled(r['q'],r['a'],g['title']) if answer else r['q'] for r in rows[i:i+3]]
            story.append(P('　　'.join(parts)))
    else:
        for r in rows:
            text=filled(r['q'],r['a'],g['title']) if answer else r['q']
            story.append(P(text))

def add_group(story,g,answer=False):
    block=[P(g['title'],'group')]
    add_rows(block,g,answer)
    # 标题与首条内容一起换页，防止标题独留页尾。
    if len(block)>1: story.append(KeepTogether([block[0],block[1]]));story.extend(block[2:])

study=[]
study.append(P('第三单元基础字词背诵讲义','title'))
study.append(P('高中语文期中复习  答案填全版','small'))
study.append(P('按原资料的三组顺序复习字音、字形、词义和文言知识。加粗处对应原题加点内容及需记住的答案。'))
for i,u in enumerate(UNITS):
    if i: study.append(Spacer(1,12))
    study.append(P(u['title'],'unit')); study.append(P(u['source'],'small'))
    for g in u['groups']:
        add_group(study,g,True)
study.append(Spacer(1,7))
study.append(P('易错辨析','group'))
study.append(P('“信难求”的“信”是实在，“信手”是随手；“因为长句”应拆为“因（于是）＋为（创作）”。“天台”的“台”读tāi，“商贾”的“贾”读gǔ，“佛狸祠”的“佛”读bì，“将进酒”的“将”读qiāng。'))
study.append(P('“风流”在现代也可作褒义，原题只列出一项贬义用法。词类活用应结合句意判断：“栗、惊”是使动，“重、轻”是意动。'))
study.append(P('来源：用户提供的《第三单元基础字词.pdf》三页。答案为补配参考答案；原题、原页及具体校注见配套题库。','small'))
document(HERE/'第三单元基础字词_背诵讲义_答案填全.pdf',study,'第三单元基础字词背诵讲义')

bank=[P('第三单元基础字音词语积累题库','title'),P('原题转录  参考答案  原页附录','small'),P('第一部分 原题','unit')]
for i,u in enumerate(UNITS):
    if i: bank.append(Spacer(1,12))
    bank.append(P(u['title'],'unit'));bank.append(P(u['source'],'small'))
    bank.append(P('任务二　基础知识积累'))
    bank.append(P('自查工具书，完成下面的学习任务。'))
    for g in u['groups']:
        add_group(bank,g)
bank.append(PageBreak());bank.append(P('第二部分 参考答案','unit'))
for i,u in enumerate(UNITS):
    if i: bank.append(Spacer(1,12))
    bank.append(P(u['title'],'unit'))
    for g in u['groups']:
        if '识记字音' in g['title'] or '辨识字形' in g['title']:
            add_group(bank,g,True)
        else:
            block=[P(g['title'],'group')]
            for j,r in enumerate(g['rows'],1): block.append(P(str(j)+'. '+r['a']))
            bank.append(KeepTogether([block[0],block[1]]));bank.extend(block[2:])
bank.append(PageBreak());bank.append(P('第三部分 来源与校注','unit'))
for i,n in enumerate(NOTES,1):bank.append(P(str(i)+'. '+n))
bank.append(P('原稿：第三单元基础字词.pdf，3页；第2、3页可见书页68、78。扫描页页眉为《高中同步辅导与检测·语文 必修 上册（人教版）》，出版年与完整出版信息未见，不作推定。','small'))
bank.append(P('下一页起为完整原页附录，顺序与用户文件一致。原有手写答案、裁切边缘和赏析文字均保留，供保真核对。','small'))
document(TMP/'bank-body.pdf',bank,'第三单元基础字音词语积累题库')
writer=PdfWriter();writer.append(str(TMP/'bank-body.pdf'));writer.append(str(SOURCE));writer.add_metadata({'/Title':'第三单元基础字音词语积累题库 原题与答案','/Author':'教学资料整理'})
with (HERE/'第三单元基础字词_原题题库与答案.pdf').open('wb') as f:writer.write(f)

lines=['# 第三单元基础字音词语积累题库','','## 原题','']
for u in UNITS:
    lines.extend(['### '+u['title'],'',u['source'],'','任务二　基础知识积累','','自查工具书，完成下面的学习任务。',''])
    for g in u['groups']:
        lines.extend(['#### '+g['title'],''])
        for r in g['rows']: lines.extend([md(r['q']).replace('\n','<br>\n'),''])
lines.extend(['## 参考答案',''])
for u in UNITS:
    lines.extend(['### '+u['title'],''])
    for g in u['groups']:
        lines.extend(['#### '+g['title'],''])
        for i,r in enumerate(g['rows'],1):
            if '识记字音' in g['title'] or '辨识字形' in g['title']: s=md(filled(r['q'],r['a'],g['title']))
            else:s=str(i)+'. '+r['a']
            lines.extend([s,''])
lines.extend(['## 来源与校注',''])
for n in NOTES:lines.extend(['- '+n,''])
lines.extend(['原始文件位置：`D:\\guanghui\\AI读取\\第三单元基础字词.pdf`。完整原页保存在配套题库PDF末尾。','',
'核查参考：国家中小学智慧教育平台所载《普通高中教科书 语文 必修上册》课文注释（检索摘录用于核对“因”等课内释义）；[教育部异体字字典“將”条](https://dict.variants.moe.edu.tw/dictView.jsp?ID=11493&powerMode=2&q=1)用于核对“将息”“将进酒”的多音义。不同地区字音不得混用，采用大陆课内普通话口径。',''])
(HERE/'第三单元基础字词_原题与答案.md').write_text('\n'.join(lines),encoding='utf-8')
manifest={
 'source_path':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'source_pages':len(PdfReader(SOURCE).pages),
 'groups':[{'title':u['title'],'sections':len(u['groups']),'entries':sum(len(g['rows']) for g in u['groups'])} for u in UNITS],
 'outputs':{p.name:len(PdfReader(p).pages) for p in HERE.glob('*.pdf')},
}
(TMP/'verification.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
