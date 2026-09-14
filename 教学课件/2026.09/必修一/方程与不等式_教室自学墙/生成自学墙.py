"""A3 自学墙；修改本文件中的文字后运行。依赖 reportlab 和微软雅黑字体。"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A3

ROOT = Path(__file__).resolve().parent
pdfmetrics.registerFont(TTFont('CN', 'C:/Windows/Fonts/msyh.ttc'))
pdfmetrics.registerFont(TTFont('B', 'C:/Windows/Fonts/msyhbd.ttc'))
W,H=A3
INK=HexColor('#172f42'); BLUE=HexColor('#175d75'); GRAY=HexColor('#536471')
c=canvas.Canvas(str(ROOT/'方程与不等式_从头学起_A3张贴版.pdf'),pagesize=A3)
c.setTitle('方程与不等式，从头学起 | 教室自学墙')
page_no=0
y=0

def text(s,size=21,color=INK,font='CN',gap=14):
    global y
    st=ParagraphStyle('p',fontName=font,fontSize=size,leading=size*1.48,textColor=color)
    p=Paragraph(s,st); _,h=p.wrap(W-100,H)
    if y-h<245: raise ValueError(f'第{page_no}张正文过长: {s}')
    p.drawOn(c,50,y-h); y-=h+gap

def heading(s): text(s,25,BLUE,'B',10)
def start(title,goal,route):
    global page_no,y
    if page_no: c.showPage()
    page_no+=1
    c.setFillColor(BLUE); c.rect(0,H-18,W,18,fill=1,stroke=0)
    c.setFont('CN',15); c.setFillColor(GRAY)
    c.drawString(50,H-53,'方程与不等式 · 从头学起')
    c.drawRightString(W-50,H-53,f'{page_no:02d} / 10')
    c.setFont('B',34); c.setFillColor(INK); c.drawString(50,H-112,title)
    y=H-143; text(goal,20,GRAY,gap=24)
    c.setFont('CN',14); c.setFillColor(GRAY)
    c.drawString(50,33,route)
    c.drawRightString(W-50,33,'只讨论实数')

def end(check,answer,trap):
    c.setLineWidth(1)
    c.setStrokeColor(HexColor('#b8c9d0')); c.line(50,229,W-50,229)
    def fixed(s,top,size,color):
        p=Paragraph(s,ParagraphStyle('f',fontName='CN',fontSize=size,leading=size*1.42,textColor=color))
        _,h=p.wrap(W-100,200); p.drawOn(c,50,top-h)
    fixed('别踩坑｜'+trap,214,18,INK)
    fixed('遮住答案试一题｜'+check,157,20,BLUE)
    fixed('核对｜'+answer,100,17,GRAY)

def fraction(prefix,numerator,denominator):
    global y
    c.setFont('CN',26); c.setFillColor(INK)
    c.drawString(130,y-39,prefix)
    cx=270; width=max(pdfmetrics.stringWidth(numerator,'CN',26),90)+28
    c.drawCentredString(cx,y-16,numerator)
    c.setStrokeColor(INK); c.setLineWidth(1.5); c.line(cx-width/2,y-29,cx+width/2,y-29)
    c.drawCentredString(cx,y-62,denominator); y-=91

def numberline(lo=2,hi=5,inside=True,closed=False):
    global y
    yy=y-30; left=90; right=W-90; a=300; b=540
    c.setStrokeColor(GRAY); c.setLineWidth(1.2); c.line(left,yy,right,yy)
    c.line(right,yy,right-10,yy+5); c.line(right,yy,right-10,yy-5)
    c.setStrokeColor(BLUE); c.setLineWidth(5)
    if inside: c.line(a,yy,b,yy)
    else:
        c.line(left,yy,a,yy); c.line(b,yy,right-12,yy)
        c.setLineWidth(2)
        c.line(left,yy,left+10,yy+5); c.line(left,yy,left+10,yy-5)
    for xx,label in [(a,lo),(b,hi)]:
        c.setFillColor(BLUE if closed else white); c.circle(xx,yy,6,fill=1,stroke=1)
        c.setFont('CN',19); c.setFillColor(INK); c.drawCentredString(xx,yy-33,str(label))
    y-=100

def signs():
    global y
    rows=[['x 的位置','x < 2','2 < x < 5','x > 5'],['x − 2','−','+','+'],['x − 5','−','−','+'],['两项相乘','+','−','+']]
    widths=[180,180,200,W-100-560]; top=y
    for i,row in enumerate(rows):
        xx=50
        for j,item in enumerate(row):
            c.setFillColor(HexColor('#edf3f5') if i in (0,3) else white)
            c.setStrokeColor(HexColor('#b8c9d0')); c.rect(xx,top-51*(i+1),widths[j],51,fill=1,stroke=1)
            c.setFillColor(INK); c.setFont('CN',19); c.drawCentredString(xx+widths[j]/2,top-51*i-33,item)
            xx+=widths[j]
    y-=230

start('先看懂：什么叫“解”？','不会移项，从第 1 张开始；会解方程，直接看第 7 张。','下一张 → 解一元一次方程')
heading('1　x 是一个等待确定的数')
text('2x 表示 2 × x；x² 表示 x × x。<br/>例如 x = 3 时，2x = 6，x² = 9。')
heading('2　“解”就是让式子成立的数')
text('方程：x + 2 = 5。代入 x = 3，左边等于右边。<br/>所以 x = 3 是解；x = 2 不是解。')
text('不等式：x + 2 &lt; 5。x = 0、1、2 都能使它成立。<br/>全部解可以写成 x &lt; 3，也包括负数和小数。')
heading('3　先认清这些符号')
text('&gt; 大于　　&lt; 小于　　≥ 大于或等于　　≤ 小于或等于<br/>“解集”就是所有解组成的集合。')
heading('4　负数运算先过关')
text('同号相乘得正，异号相乘得负。<br/>(−3) × (−2) = 6；(−3) × 2 = −6。<br/>(−3)² = 9；−3² = −9（先平方，再取负号）。')
end('x = −2 时，2x 和 x² 分别是多少？','2x = −4；x² = (−2) × (−2) = 4。','x² 不是 2x；判断一个数是不是解，可以代入检查。')

start('解一次方程：把 x 留在一边','这一张只学三件事：去括号、移项、两边同除。','上一步 01 → 下一张 03：平方与开平方')
heading('1　等式像天平，两边要做同样的事')
text('两边同加、同减同一个数，等式仍成立。<br/>两边同乘，或同除以同一个非零数，等式仍成立。')
heading('2　移项变号，其实是两边同加或同减')
text('x + 3 = 7<br/>两边同时减 3：x + 3 − 3 = 7 − 3<br/>得到 x = 4。简写为：x = 7 − 3。')
heading('3　跟着完整例题走一遍')
text('解方程：2(x − 1) + 3 = 7',24,BLUE)
text('① 去括号：2x − 2 + 3 = 7<br/>　 2 要乘到括号里的每一项。<br/>② 合并同类项：2x + 1 = 7<br/>③ 两边减 1：2x = 6<br/>④ 两边除以 2：x = 3。')
text('代回检查：2 × (3 − 1) + 3 = 7，成立。')
end('解方程：3x − 4 = 8。','3x = 12，所以 x = 4。','移项变号；去括号时，括号前的数要乘到每一项。')

start('解二次方程：先学开平方','“二次”说的是：整理后，x 的最高次数是 2。','上一步 02 → 下一张 04：因式分解')
heading('1　标准形式与系数')
text('ax² + bx + c = 0，且 a ≠ 0。<br/>a、b、c 是数，符号也算在系数里。<br/>2x² = 3x + 2 → 2x² − 3x − 2 = 0，<br/>所以 a = 2，b = −3，c = −2。')
heading('2　平方等于 9，原来的数有两种可能')
text('3² = 9，(−3)² = 9。<br/>所以 x² = 9 的解是 x = 3 或 x = −3，<br/>简写为 x = ±3；“±”表示正、负两种情况。<br/>方程的解也叫方程的“根”。')
heading('3　把括号看成一个整体')
text('解方程：(x − 1)² = 9',24,BLUE)
text('① 开平方：x − 1 = 3 或 x − 1 = −3。<br/>② 分别解一次方程：x = 4 或 x = −2。')
heading('4　平方等于 0 或负数呢？')
text('x² = 0 → x = 0。<br/>x² = −4 → 没有实数解，因为实数的平方不会小于 0。')
end('解方程：(x + 2)² = 16。','x + 2 = ±4，所以 x = 2 或 x = −6。','√9 = 3，但 x² = 9 有两个根，不能漏掉 −3。')

start('因式分解：把加减变成乘法','关键：两个数相乘等于 0，至少有一个数等于 0。','上一步 03 → 下一张 05：配方法')
heading('1　先看一个容易漏根的例子')
text('解方程：x² = 3x',24,BLUE)
text('① 移项：x² − 3x = 0。<br/>② 提出共同的 x：x(x − 3) = 0。<br/>③ x = 0 或 x − 3 = 0。<br/>④ 所以 x = 0 或 x = 3。')
heading('2　怎样把 x² − 5x + 6 分解？')
text('找两个数：和为 −5，积为 6，它们是 −2、−3。<br/>(x − 2)(x − 3) = x² − 3x − 2x + 6<br/>　　　　　　　　 = x² − 5x + 6。')
text('因此 x² − 5x + 6 = 0<br/>→ (x − 2)(x − 3) = 0<br/>→ x − 2 = 0 或 x − 3 = 0<br/>→ x = 2 或 x = 3。')
heading('3　再记一个常用公式')
text('x² − d² = (x − d)(x + d)。<br/>例如 x² − 9 = (x − 3)(x + 3)。')
end('解方程：x² − 4x = 0。','x(x − 4) = 0，所以 x = 0 或 x = 4。','右边先化为 0；不能直接除以 x，否则可能漏掉根 0。')

start('配方法：凑成“一个式子的平方”','当 x² 前的系数不是 1 时，先把两边同除以这个系数。','上一步 04 → 下一张 06：求根公式')
heading('1　先把完全平方公式展开看')
text('(x + 2)² = (x + 2)(x + 2)<br/>　　　　 = x² + 4x + 4。<br/>所以 x² + 4x 后面补上 4，就能写成 (x + 2)²。')
heading('2　要补多少？')
text('一次项系数的一半，再平方。<br/>x² + 6x 要补 (6 ÷ 2)² = 9；<br/>x² − 4x 要补 (−4 ÷ 2)² = 4。')
heading('3　完整例题：x² + 4x − 1 = 0')
text('① 移常数项：x² + 4x = 1。<br/>② 两边同加 4：x² + 4x + 4 = 1 + 4。<br/>③ 写成平方：(x + 2)² = 5。<br/>④ 开平方：x + 2 = ±√5。<br/>⑤ 得到 x = −2 + √5 或 x = −2 − √5。')
text('√5 表示平方等于 5 的那个正数，约为 2.236。<br/>答案通常保留 √5，不必算成小数。',20,GRAY)
end('解方程：x² + 6x + 5 = 0。','x² + 6x = −5；两边加 9，得 (x + 3)² = 4；x = −1 或 −5。','补数时必须两边一起补；不能只改变等式左边。')

start('公式法：按步骤求根','分解不出来时，就用这一张。先整理，再代数，最后计算。','上一步 05 → 下一张 07：一次不等式')
heading('1　整理成 ax² + bx + c = 0（a ≠ 0）')
text('先计算 Δ = b² − 4ac。“Δ”读作德尔塔，叫判别式。<br/>Δ &gt; 0：两个不相等的实数根。<br/>Δ = 0：两个相等的实数根（只有一个不同的根值）。<br/>Δ &lt; 0：没有实数根，不再开平方。')
heading('2　当 Δ ≥ 0 时，用求根公式')
fraction('x =','−b ± √Δ','2a')
heading('3　完整例题：2x² − 3x − 2 = 0')
text('① 认系数：a = 2，b = −3，c = −2。<br/>② 算判别式：Δ = (−3)² − 4 × 2 × (−2) = 25。<br/>③ 代公式：x = (3 ± 5) ÷ 4。<br/>④ 拆成两种：x = (3 + 5) ÷ 4 = 2，<br/>　　　　　 或 x = (3 − 5) ÷ 4 = −1/2。')
end('x² − 2x − 3 = 0 的判别式和两根分别是多少？','Δ = 4 + 12 = 16；x = (2 ± 4) ÷ 2，即 x = 3 或 −1。','负系数代入时加括号；整个分子都要除以 2a。')

start('一次不等式：什么时候要变号？','方程求哪些数使两边相等；不等式求哪些数使大小关系成立。','上一步 06 → 下一张 08：二次式的正负')
heading('1　最重要的规则')
text('两边同加、同减同一个数：不等号方向不变。<br/>两边同乘、同除以同一个正数：方向不变。<br/>两边同乘、同除以同一个负数：方向反过来！')
text('例如 2 &lt; 3；两边乘 −1 后，−2 &gt; −3。',22,BLUE)
heading('2　完整例题：3 − 2x ≥ 7')
text('① 两边减 3：−2x ≥ 4。<br/>② 两边除以 −2，方向反过来：x ≤ −2。<br/>这表示 −2 以及所有比 −2 小的数。')
heading('3　怎样读出一段范围？')
text('2 &lt; x &lt; 5：x 同时大于 2、小于 5，写作 (2, 5)。<br/>2 ≤ x ≤ 5：还包括 2 和 5，写作 [2, 5]。<br/>圆括号不含端点，方括号包含端点；∞ 表示无穷。<br/>x ≤ −2 也可写成 (−∞, −2]，无穷处只用圆括号。',20)
text('图中加粗部分表示 2 &lt; x &lt; 5；空心点表示端点不取。',19,GRAY)
numberline()
end('解不等式：5 − 3x &lt; 11。','−3x &lt; 6；除以 −3，得到 x &gt; −2。','只有同乘或同除以负数才反向；移项只改变移过去那一项的符号。')

start('二次不等式：先看乘积的正负','先解对应方程，找分界点；再判断每一段的符号。','上一步 07 → 下一张 09：完整解题流程')
heading('1　以 x² − 7x + 10 为例')
text('x² − 7x + 10 = (x − 2)(x − 5)。<br/>乘积等于 0 时，x = 2 或 x = 5。<br/>这两个数把数轴分成三段。')
heading('2　看清每个因式的正负')
signs()
text('例如 x &lt; 2 时：x − 2 &lt; 0，x − 5 &lt; 0。<br/>两个负数相乘得正，所以这一整段的乘积都为正。',20)
heading('3　题目要负，就选中间；要正，就选两侧')
text('x² − 7x + 10 &lt; 0 → 2 &lt; x &lt; 5。<br/>x² − 7x + 10 &gt; 0 → x &lt; 2 或 x &gt; 5。')
text('图中表示乘积 &gt; 0 的范围。两个端点都使乘积等于 0。',19,GRAY)
numberline(inside=False)
end('解不等式：x² − 7x + 10 ≤ 0。','2 ≤ x ≤ 5，即 [2, 5]；“≤”允许乘积等于 0，所以取端点。','“两侧为正、中间为负”要满足二次项系数为正且有两个不同实根。')

start('二次不等式：照这四步做','① 一边化为 0　② 二次项系数化正　③ 求根　④ 选范围、查端点','上一步 08 → 下一张 10：重根与无实根')
heading('例 1　解 x² − x ≤ 6')
text('① 移项：x² − x − 6 ≤ 0。<br/>② x² 的系数为 1，已经是正数。<br/>③ 解 x² − x − 6 = 0：<br/>　 (x − 3)(x + 2) = 0，根是 −2 和 3。<br/>④ 乘积要小于或等于 0，选两根之间，包含端点。<br/>　 答案：−2 ≤ x ≤ 3，即 [−2, 3]。')
heading('例 2　解 −x² + x + 6 &gt; 0')
text('① 右边已经是 0。<br/>② 两边乘 −1：x² − x − 6 &lt; 0。<br/>　 注意：不等号由 &gt; 变为 &lt;！<br/>③ 对应方程的根仍是 −2 和 3。<br/>④ 乘积要小于 0，选两根之间，不包含端点。<br/>　 答案：−2 &lt; x &lt; 3，即 (−2, 3)。')
heading('写完再检查两个地方')
text('取 x = 0，代回原不等式，应当成立。<br/>把端点 −2、3 代回：例 1 成立，例 2 不成立。',20)
end('解不等式：−x² + x + 6 ≥ 0。','乘 −1 得 x² − x − 6 ≤ 0，所以 −2 ≤ x ≤ 3。','端点能不能取，看原题有没有等号；答案是一段范围，不只是两个根。')

start('只有一个根，或没有实根呢？','先把二次项系数化为正，再分情况；不要硬套“两根之间”。','需要复习：求根看 06；不等号变向看 07；符号表看 08')
heading('情况一　Δ = 0：可以写成一个平方')
text('x² − 4x + 4 = (x − 2)²。<br/>平方总是 ≥ 0，只有 x = 2 时等于 0。<br/>所以：<br/>(x − 2)² &gt; 0 → x ≠ 2。<br/>(x − 2)² ≥ 0 → 所有实数。<br/>(x − 2)² &lt; 0 → 无解。<br/>(x − 2)² ≤ 0 → x = 2。')
heading('情况二　Δ &lt; 0：系数化正后，恒为正')
text('例如 x² + 2x + 3 = (x + 1)² + 2 ≥ 2 &gt; 0。<br/>所以它 &gt; 0 或 ≥ 0 时，解为所有实数；<br/>它 &lt; 0 或 ≤ 0 时，无解。')
text('一般地：a &gt; 0 时，配方可写成<br/>a[x + b/(2a)]² − Δ/(4a)。<br/>若 Δ &lt; 0，平方项 ≥ 0，后面的常数 &gt; 0，故整个式子 &gt; 0。',19,GRAY)
heading('最后记住')
text('所有实数可写作 R（实数集），或 (−∞, +∞)。<br/>无解表示没有任何实数满足，不是说“x = 0”。',20)
end('解不等式：x² + 1 &gt; 0；再解 x² + 1 ≤ 0。','前者为所有实数；后者无解。因为 x² ≥ 0，所以 x² + 1 ≥ 1。','方程没有实根，不代表不等式无解；必须看式子的正负与题目要求。')
c.save()
print(f'Created {page_no} A3 posters')
