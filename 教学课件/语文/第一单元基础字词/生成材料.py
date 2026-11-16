# -*- coding: utf-8 -*-
"""生成两份正式PDF和Markdown题库；临时文件置于仓库tmp/unit1。"""
from pathlib import Path
import re,json,hashlib
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,KeepTogether,Table,TableStyle
from pypdf import PdfReader,PdfWriter
from 内容数据 import UNITS,NOTES,REFERENCES

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
TMP=ROOT/'tmp'/'unit1'
SOURCE=Path(r'D:\guanghui\AI读取\第一单元字词复习资料.pdf')
TMP.mkdir(parents=True,exist_ok=True)
pdfmetrics.registerFont(TTFont('Song',r'C:\Windows\Fonts\simsun.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('Hei',r'C:\Windows\Fonts\simhei.ttf'))
pdfmetrics.registerFontFamily('Song',normal='Song',bold='Hei',italic='Song',boldItalic='Hei')
ST={
'title':ParagraphStyle('title',fontName='Hei',fontSize=20,leading=29,spaceAfter=8),
'unit':ParagraphStyle('unit',fontName='Hei',fontSize=14,leading=23,spaceBefore=8,spaceAfter=5,keepWithNext=True),
'group':ParagraphStyle('group',fontName='Hei',fontSize=12,leading=20,spaceBefore=10,spaceAfter=4,keepWithNext=True),
'body':ParagraphStyle('body',fontName='Song',fontSize=11,leading=18,spaceAfter=3,wordWrap='CJK'),
'cell':ParagraphStyle('cell',fontName='Song',fontSize=11,leading=18,wordWrap='CJK'),
'small':ParagraphStyle('small',fontName='Song',fontSize=9,leading=14,spaceAfter=4,textColor=colors.HexColor('#555555'),wordWrap='CJK'),
}
def P(s,kind='body'):
    for clause in ['否则将会害人害己','实在是太让人气愤了','坚持信仰，未来就在前方']:
        s=s.replace(clause,'<br/>'+clause)
    return Paragraph(s.replace('\n','<br/>'),ST[kind])
def md(s):return s.replace('<b>','**').replace('</b>','**')
def filled(row):
    s=row['q']
    for val in row['fills']:
        token='(　　)' if '(　　)' in s else '______'
        replacement='(<b>'+val+'</b>)' if token=='(　　)' else '<b>'+val+'</b>'
        assert token in s,(s,val)
        s=s.replace(token,replacement,1)
    assert '______' not in s and '(　　)' not in s,s
    return s
def footer(c,doc):
    c.saveState();c.setFont('Song',9);c.setFillColor(colors.HexColor('#555555'))
    c.drawString(46,25,'高中语文必修上册  第一单元基础字词')
    c.drawRightString(549,25,str(doc.page));c.restoreState()
def document(path,story,title):
    d=SimpleDocTemplate(str(path),pagesize=(595.276,841.89),leftMargin=46,rightMargin=46,topMargin=40,bottomMargin=44,title=title,author='教学资料整理')
    d.build(story,onFirstPage=footer,onLaterPages=footer)
def compact(g,answer):
    out=[]
    for i in range(0,len(g['rows']),3):
        cells=[P(filled(r) if answer else r['q'],'cell') for r in g['rows'][i:i+3]]
        cells+=['']*(3-len(cells))
        t=Table([cells],colWidths=[167.75]*3)
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
        out.append(t)
    return out
def add_group(story,g,answer=False):
    title=P(g['title'],'group')
    if '词语积累' not in g['title']:
        rows=compact(g,answer)
    else:
        rows=[]
        for r in g['rows']:
            text=filled(r) if answer else re.sub(r'：______', '：'+'_'*42,r['q'])
            rows.append(P(text))
    story.append(KeepTogether([title,rows[0]]))
    for row in rows[1:]:
        story.append(KeepTogether([row]) if '词语积累' in g['title'] else row)

study=[P('第一单元基础字词背诵讲义','title'),P('高中语文期中复习  答案填全版','small'),P('按课文分组复习字音、字形与词语。辨析题保留完整例句，需填内容均已补全；加粗字对应原稿加点或所填答案。')]
for i,u in enumerate(UNITS):
    if i:study.append(Spacer(1,10))
    study.extend([P(u['title'],'unit'),P(u['source'],'small')])
    for g in u['groups']:add_group(study,g,True)
study.append(P('易错提醒','group'))
study.append(P('当代dāng、当铺dàng；揳xiē、罅xià；荫蔽yīn、荫庇yìn；皱褶zhě、吸吮shǔn；怂恿sǒng yǒng、搡sǎng；执拗niù、拗口ào、拗断ǎo；包扎zā、扎营zhā、挣扎zhá。嘟囔读dū nang，掂量读diān liang，后一个音节均读轻声。哟作叹词读yō，作语气词或衬字可读轻声yo。'))
study.append(P('正字：幔帐、为虎作伥、啁啾、绯闻、厮打、讴歌、烽燧、忸怩、撼动、遗憾。幔用巾字旁，伥用单人旁，啁用口字旁，燧用火字旁。'))
study.append(P('“分辨”重在区分，“分辩”重在用言语辩白。“故意”不一律贬义，本题语境含责备；“刻意”重在用心。“豆蔻年华”只用于十三四岁的女子。'))
study.append(P('来源：用户提供的《第一单元字词复习资料.pdf》六页。答案为逐题核对后补配的参考答案；原题、完整原页及校注见配套题库。','small'))
document(HERE/'第一单元基础字词_背诵讲义_答案填全.pdf',study,'第一单元基础字词背诵讲义')

bank=[P('第一单元基础字音词语积累题库','title'),P('原题转录  参考答案  原页附录','small'),P('第一部分 原题','unit')]
for i,u in enumerate(UNITS):
    if i:bank.append(Spacer(1,10))
    bank.extend([P(u['title'],'unit'),P(u['source'],'small'),P('任务二　基础知识积累'),P('自查工具书，完成下面的学习任务。')])
    for g in u['groups']:add_group(bank,g)
bank.extend([PageBreak(),P('第二部分 参考答案','unit')])
for i,u in enumerate(UNITS):
    if i:bank.append(Spacer(1,10))
    bank.append(P(u['title'],'unit'))
    for g in u['groups']:
        if '词语积累' not in g['title']:add_group(bank,g,True)
        else:
            bank.append(KeepTogether([P(g['title'],'group'),P('1. '+g['rows'][0]['a'])]))
            for j,r in enumerate(g['rows'][1:],2):bank.append(KeepTogether([P(str(j)+'. '+r['a'])]))
bank.extend([PageBreak(),P('第三部分 来源与校注','unit')])
for i,n in enumerate(NOTES,1):bank.append(P(str(i)+'. '+n))
bank.append(P('来源：第一单元字词复习资料.pdf，共6页；第1、3、5页书页码分别为2、9、15。页眉可见《高中同步辅导与检测·语文 必修 上册（人教版）》。其余出版信息未见，不作推定。','small'))
bank.append(P('核查参考','group'))
for name,url in REFERENCES:bank.append(P('<link href="'+url+'" color="#333333">'+name+'</link>','small'))
bank.append(P('下一页起完整附入用户所供六页PDF，保留全部原文、版式、图表、手写痕迹和裁切边缘，按原文件顺序排列。','small'))
document(TMP/'bank-body.pdf',bank,'第一单元基础字音词语积累题库')
writer=PdfWriter();writer.append(str(TMP/'bank-body.pdf'));writer.append(str(SOURCE));writer.add_metadata({'/Title':'第一单元基础字音词语积累题库 原题与答案','/Author':'教学资料整理'})
with (HERE/'第一单元基础字词_原题题库与答案.pdf').open('wb') as f:writer.write(f)

lines=['# 第一单元基础字音词语积累题库','','## 原题','']
for u in UNITS:
    lines.extend(['### '+u['title'],'',u['source'],'','任务二　基础知识积累','','自查工具书，完成下面的学习任务。',''])
    for g in u['groups']:
        lines.extend(['#### '+g['title'],''])
        for r in g['rows']:lines.extend([md(r['q']).replace('\n','<br>\n'),''])
lines.extend(['## 参考答案',''])
for u in UNITS:
    lines.extend(['### '+u['title'],''])
    for g in u['groups']:
        lines.extend(['#### '+g['title'],''])
        for j,r in enumerate(g['rows'],1):
            text=md(filled(r)) if '词语积累' not in g['title'] else str(j)+'. '+r['a']
            lines.extend([text,''])
lines.extend(['## 来源与校注',''])
for n in NOTES:lines.extend(['- '+n,''])
lines.extend(['原始文件位置：`D:\\guanghui\\AI读取\\第一单元字词复习资料.pdf`。完整六页附在配套题库PDF末尾。','','## 核查参考',''])
for name,url in REFERENCES:lines.extend(['- ['+name+']('+url+')',''])
(HERE/'第一单元基础字词_原题与答案.md').write_text('\n'.join(lines),encoding='utf-8')
manifest={'source_path':str(SOURCE),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'source_pages':len(PdfReader(SOURCE).pages),'groups':[{'title':u['title'],'sections':len(u['groups']),'entries':sum(len(g['rows']) for g in u['groups'])} for u in UNITS],'outputs':{p.name:len(PdfReader(p).pages) for p in HERE.glob('*.pdf')}}
(TMP/'verification.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest,ensure_ascii=False,indent=2))
