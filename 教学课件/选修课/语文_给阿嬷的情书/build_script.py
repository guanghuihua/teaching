from pathlib import Path
import json, html
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle

ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/'课程内容.json').read_text('utf8'))
pdfmetrics.registerFont(TTFont('Chinese',r'C:\Windows\Fonts\simsun.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('Hei',r'C:\Windows\Fonts\simhei.ttf'))
PAPER=HexColor('#FCFAF5'); INK=HexColor('#203E39'); MUTED=HexColor('#59645E'); RED=HexColor('#A14B37')
W,H=A4; LEFT=43; RIGHT=W-43; WIDTH=RIGHT-LEFT
STYLES={
 'body':ParagraphStyle('body',fontName='Chinese',fontSize=11.2,leading=18,textColor=INK,wordWrap='CJK',spaceAfter=6),
 'small':ParagraphStyle('small',fontName='Chinese',fontSize=9.4,leading=14,textColor=MUTED,wordWrap='CJK'),
 'title':ParagraphStyle('title',fontName='Hei',fontSize=18,leading=27,textColor=INK,wordWrap='CJK'),
 'meta':ParagraphStyle('meta',fontName='Hei',fontSize=10,leading=16,textColor=RED,wordWrap='CJK'),
}
OUT=ROOT/'给阿嬷的情书_45分钟教师逐字稿.pdf'
c=canvas.Canvas(str(OUT),pagesize=A4)
c.setTitle('给阿嬷的情书 高中语文选修课教师逐字稿')
c.setAuthor('教学资料')
page=0
def begin(label='教师逐字稿'):
 global page
 page+=1;c.setFillColor(PAPER);c.rect(0,0,W,H,fill=1,stroke=0)
 c.setFillColor(MUTED);c.setFont('Chinese',9);c.drawString(LEFT,H-30,'给阿嬷的情书  高中语文选修课')
 c.drawRightString(RIGHT,H-30,label)
 c.setFont('Chinese',9);c.drawRightString(RIGHT,25,str(page))
def para(value,y,kind='body',width=WIDTH,x=LEFT):
 p=Paragraph(html.escape(value).replace('\n','<br/>'),STYLES[kind]);_,h=p.wrap(width,H)
 p.drawOn(c,x,y-h);return y-h
def section(d,i,start,y):
 y=para(f"第{i+1:02d}页  {d['title']}",y,'title')-6
 y=para(f"课堂 {start:02d}—{start+d['minutes']:02d} 分钟   本页 {d['minutes']} 分钟",y,'meta')-10
 y=para(d['script'],y)-10
 y=para('活动与停顿  '+d['action'],y,'small')-8
 if d.get('follow'):y=para('追问或参考回应  '+d['follow'],y,'small')-8
 return y

begin('45分钟教学安排')
y=H-82
y=para('给阿嬷的情书',y,'title')-5
y=para('侨批里的日常与深情 教师逐字稿',y,'title')-18
y=para('本稿与23页PPT逐页对应。前22页用于45分钟课堂，第23页为课后来源页。学生无须预先看过影片，课堂会提供必要梗概和文字。逐字稿可直接朗读，活动提示无需念出。',y)-15
y=para('教学目标',y,'title')-8
for t in ['从评论材料中提取人物行动与语言证据，形成一段有依据的分析。','解释重复量词、日常动作与物件怎样承载情感。','完成100—150字家书，以具体细节表达关心，并根据同伴或自评反馈修改。']:
 y=para(t,y)-7
y-=7;y=para('课前准备',y,'title')-8
y=para('投影课件，准备纸笔。无需播放视频。故事梗概涉及关键剧情，可在开课前说明。课堂允许学生虚构场景或自评，不要求分享私人家庭经历。',y)-15
y=para('时间安排',y,'title')-8
start=0;rows=[]
for a,b,name in [(0,5,'导入与背景'),(5,12,'图文细读与人物讨论'),(12,17,'文化联系与评论辨析'),(17,22,'写作与反馈')]:
 mins=sum(s['minutes'] for s in DATA['slides'][a:b]);rows.append([f'{start:02d}—{start+mins:02d}分钟',name,f'P{a+1}—P{b}']);start+=mins
table=Table(rows,colWidths=[105,280,WIDTH-385],rowHeights=29)
table.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Chinese'),('FONTSIZE',(0,0),(-1,-1),10),('TEXTCOLOR',(0,0),(-1,-1),INK),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),0)]))
_,th=table.wrap(WIDTH,H);table.drawOn(c,LEFT,y-th);y-=th+16
y=para('评价证据  口头分析中的词句依据、家书中的具体细节、落实的一处修改、离堂记录。所有参考回应均为教学示例，授课时以真实课堂回应为准。',y,'small')
assert y>48,y
c.showPage()

elapsed=0
for i,d in enumerate(DATA['slides'][:-1]):
 begin(f'课件第{i+1:02d}页')
 y=section(d,i,elapsed,H-70)
 # A generous note area makes this a usable lectern copy and prevents sections splitting.
 y-=16;y=para('现场记录',y,'meta')-10
 c.setStrokeColor(HexColor('#DBDED5'));c.setLineWidth(.45)
 for yy in [y-12,y-44,y-76]:c.line(LEFT,yy,RIGHT,yy)
 assert y-76>48,(i,y)
 elapsed+=d['minutes'];c.showPage()

begin('来源与使用说明')
y=H-75;y=para('阅读与图片来源',y,'title')-15
sources=[
 '主要阅读材料：用户提供的《选修课〈阿嬷的情书〉》PDF第1页，内含《语文导报》高中版2026年7月6日第02—03版。本课集中使用其中《给阿嬷的情书》评论。PDF文字识别存在错字，直接引文已对照页面图像核读。',
 '电影相关内容属于艺术叙事与评论材料。第4页配图为暨南大学世界华侨华人文献馆的侨批，第6页为电影宣传剧照，第20页为电影侨批道具展览，三类资料分别标明。',
 'UNESCO：Qiaopi and Yinxin Correspondence and Remittance Documents from Overseas Chinese。用于核对侨批文献性质与2013年登记信息。',
 '海南日报《乡音系家国》，2026年5月18日。用于电影海报及宣传图。',
 '人民网报道，暨南大学新闻网转载，2026年5月20日。用于电影宣传剧照、侨批道具与真实侨批文献照片，摄影者和图片说明见原报道。',
 '杜甫《春望》、张籍《秋思》，所引诗句为通行文本。',
 'P2、P10、P19的短信、改写及示例为教学原创。学生参考回应、追问与评价规则均为教学设计。未将示例写成真实学生表现。',
 '图片版权归电影出品方、摄影者或原权利人。图片出处保留于PPT备注、图片来源表和本页。',
]
for t in sources:y=para(t,y)-13
for url in [
'https://www.unesco.org/en/memory-world/qiaopi-and-yinxin-correspondence-and-remittance-documents-overseas-chinese?hub=1081',
'https://news.hndaily.cn/h5/html5/2026-05/18/content_58485_19540937.htm',
'https://news.jnu.edu.cn/content/202605/19/c6222.html']:
 y=para(url,y,'small')-12
assert y>40,y
c.showPage();c.save()

# Markdown is the editable companion and shares the exact script data with the deck.
md=['# 给阿嬷的情书 高中语文选修课逐字稿','', '主题：侨批里的日常与深情。课时45分钟，与23页PPT对应。活动提示不必朗读。','']
elapsed=0
for i,d in enumerate(DATA['slides']):
 md += [f"## 第{i+1:02d}页 {d['title']}",'',f"时间：{elapsed}—{elapsed+d['minutes']}分钟（本页{d['minutes']}分钟）",'',d['script'],'','**活动与停顿**', '',d['action'],'']
 if d.get('follow'):md += ['**追问或参考回应**','',d['follow'],'']
 md += ['**来源与说明**','',d['source'],''];elapsed+=d['minutes']
(ROOT/'给阿嬷的情书_45分钟教师逐字稿.md').write_text('\n'.join(md),'utf8')
print(f'{OUT}\nPDF pages: {page}; slides: {len(DATA["slides"])}; minutes: {elapsed}')
