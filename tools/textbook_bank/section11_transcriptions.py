"""Source-image checked, editable TeX statements for textbook section 1.1.

Transcription only: no new answer key. Each entry still needs teacher approval.
The unusual set membership in exercise 5 is deliberately kept as printed.
"""
ENTRIES = {
"EX-P003-Y0620": r'''设 $L(A,B)$ 表示直线 $AB$ 上全体点组成的集合，则 $P\in L(A,B)$ 的含义是什么？''',
"EX-P003-Y1223": r'''下列集合中哪些是有限集？哪些是无限集？
\subq{1}一元二次方程 $x^2+1=0$ 的全体实根组成的集合 $A$；
\subq{2}所有素数（即质数）组成的集合 $B$；
\subq{3}所有矩形组成的集合 $C$；
\subq{4}所有亚洲国家组成的集合 $D$。''',
"PR-P004-Y0218": r'''使用“$\in$”“$\notin$”填空：
\subq{1}“255 是正整数”即 $255\blank\mathbb Z_+$；
\subq{2}“$\sqrt2$ 不是有理数”即 $\sqrt2\blank\mathbb Q$；
\subq{3}“1.414 是正实数”即 $1.414\blank\mathbb R_+$；
\subq{4}“$x$ 是负实数”即 $x\blank\mathbb R_-$。''',
"PR-P004-Y0443": r'''下列集合中哪些是有限集？哪些是无限集？
\subq{1}不等式 $5x-3>7$ 的所有实数解组成的集合；
\subq{2}一元二次方程 $x^2+x+1=0$ 的全体实根组成的集合；
\subq{3}中国古代四大发明组成的集合；
\subq{4}二次函数 $y=3x^2+4$ 的函数值组成的集合。''',
"EX-P004-Y1108": r'''用列举法表示下列集合：
\subq{1}由方程 $x^2-1=0$ 的所有实数解构成的集合 $S$；
\subq{2}平方不大于 9 的所有整数构成的集合 $P$。''',
"EX-P005-Y0448": r'''选择适当方法表示下列集合：
\subq{1}由大于 20 且小于 30 的所有实数组成的集合 $A$；
\subq{2}由方程 $x^2+y^2=4$ 的所有整数解 $(x,y)$ 组成的集合 $B$。''',
"EX-P005-Y1339": r'''用区间表示下列集合：
\subq{1}$\{x\in\mathbb R\mid -2\le x\le4\}$；
\subq{2}$\{t\in\mathbb R\mid t<a,\ a\in\mathbb R\}$；
\subq{3}$\{u\in\mathbb R\mid u\ge0\}$。''',
"PR-P006-Y0217": r'''用列举法表示下列集合：
\subq{1}$\{\text{不超过 30 的素数}\}$；
\subq{2}$\{\text{五边形 }ABCDE\text{ 的对角线}\}$；
\subq{3}$\{60\text{ 的正约数}\}$；
\subq{4}$\{(x,y)\mid x+2y=6,\ x\in\mathbb N,\ y\in\mathbb N\}$。''',
"PR-P006-Y0346": r'''用描述法表示下列集合：
\subq{1}$\{1,3,5,7,9\}$；
\subq{2}不等式 $3x>2$ 的解集；
\subq{3}$\{3,5,7,11,13,17,19\}$。''',
"PR-P006-Y0475": r'''用区间表示下列集合：
\subq{1}$\{x\in\mathbb R\mid 3-x>5\}$；
\subq{2}$\{x\in\mathbb R\mid x+3>1\text{ 且 }5-x>2\}$。''',
"TH-P006-Y0849": r'''观察下列各组集合，你能发现两个集合间的关系吗？
\subq{1}$A=\{3,5,7\}$，$B=(2,8]$；
\subq{2}$A=\{\text{等边三角形}\}$，$B=\{\text{等腰三角形}\}$。''',
"EX-P007-Y0656": r'''设 $S=\{a,b,c\}$，写出 $S$ 的所有子集，并指出哪些是它的真子集。''',
"TH-P007-Y1130": r'''观察下列各组中的三个集合，你能发现它们之间的关系吗？
\subq{1}$U=\{1,2,3,4,5,6\}$，$A=\{1,3,5\}$，$B=\{2,4,6\}$；
\subq{2}$U=\{\text{三角形}\}$，$A=\{\text{锐角三角形，钝角三角形}\}$，$B=\{\text{直角三角形}\}$。''',
"EX-P008-Y0280": r'''设 $U=\{x\in\mathbb Z\mid x\in(0,12]\}$，$A=\{x\in\mathbb N\mid0<x<6\}$，$B=\{x\in\mathbb Z\mid x\in[7,11]\}$，求 $\complement_U A$ 和 $\complement_U B$。''',
"EX-P008-Y0515": r'''把区间 $[0,1]$ 看成全集，写出它的下列子集的补集：
\[A=(0,1),\quad B=\{1\},\quad C=\{x\mid0\le x<0.5\},\quad D=[0,1].\]''',
"PR-P008-Y0877": r'''设 $Y$ 是由 6 的全体正约数组成的集合，写出 $Y$ 的所有子集。''',
"PR-P008-Y0920": r'''判断下列每对集合之间的关系：
\subq{1}$A=\{x\mid x=2k,\ k\in\mathbb N\}$，$B=\{y\mid y=4m,\ m\in\mathbb N\}$；
\subq{2}$C=\{1,2,3,4\}$，$D=\{x\mid x\text{ 是 }12\text{ 的约数}\}$；
\subq{3}$E=\{x\mid x-3<2,\ x\in\mathbb N_+\}$，$F=\{1,2,3,4,5\}$。''',
"PR-P008-Y1092": r'''设 $I=\{x\in\mathbb Z\mid x\in[-5,5]\}$，$A=\{x\in\mathbb Z\mid-5<x<5\}$，$B=\{x\in\mathbb Z\mid x\in[-3,3)\}$，求 $\complement_I A$，$\complement_I B$。''',
"PR-P008-Y1178": r'''把区间 $[1,+\infty)$ 看成全集，写出它的下列子集的补集：
\[A=(1,+\infty),\quad B=\{1\},\quad C=\{x\mid1\le x<5\},\quad D=[3,+\infty).\]''',
"TH-P009-Y0951": r'''观察下列各组中的三个集合，你能发现它们之间的关系吗？
\subq{1}$A=\{1,3,5,7,9\}$，$B=\{3,4\}$，$C=\{3\}$；
\subq{2}$A=\{\text{等腰三角形}\}$，$B=\{\text{直角三角形}\}$，$C=\{\text{等腰直角三角形}\}$。''',
"EX-P010-Y0276": r'''求下列各组集合的交集：
\subq{1}$A=\{2,3,5,7,11\}$，$B=\{9,10,8,6,1,4\}$；
\subq{2}$C=\{x\mid x^2-4x+3=0\}$，$D=\{x\mid3x-x^2=0\}$。''',
"EX-P010-Y0596": r'''设方程 $2x+3y=7$ 的全体解组成集合 $U$，方程 $3x-y=5$ 的全体解组成集合 $V$，求 $U\cap V$。''',
"TH-P010-Y1233": r'''观察下列各组中的三个集合，你能发现它们之间的关系吗？
\subq{1}$A=\{\text{有理数}\}$，$B=\{\text{无理数}\}$，$C=\{\text{实数}\}$；
\subq{2}$A=\{\text{直角三角形}\}$，$B=\{\text{锐角三角形，钝角三角形}\}$，$C=\{\text{三角形}\}$。''',
"EX-P011-Y0417": r'''设 $A=\{0,1,4,9,16\}$，$B=\{9,4,\pi,\sqrt2,1\}$，求 $A\cup B$。''',
"EX-P011-Y0583": r'''求下列各组集合的并集：
\subq{1}$A=(1,3)$，$B=[2,5]$；
\subq{2}$C=[0,1]$，$D=\{x\mid-1<x\le1\}$。''',
"TH-P011-Y1054": r'''分别求出方程 $x^2-9=0$ 和 $x^2-3x+2=0$ 的解集，由此你能运用并集的知识求出方程 $(x^2-9)(x^2-3x+2)=0$ 的解集吗？''',
"PR-P011-Y1439": r'''设任意全集 $U$ 及其子集 $A$，求 $A\cap\overline A$，$A\cup\overline A$。''',
"PR-P011-Y1484": r'''已知集合 $A=\{x\mid x-2=0\}$，$B=\{x\mid x^2-x-2=0\}$，求 $A\cap B$，$A\cup B$。''',
"PR-P011-Y1526": r'''已知集合 $A=\{(x,y)\mid x-y=0\}$，$B=\{(x,y)\mid x+y=0\}$，求 $A\cap B$。''',
"PR-P011-Y1570": r'''已知集合 $A=\{x\mid-2\le x\le4\}$，$B=\{x\mid-4<x<-2\}$，求 $A\cup B$，$A\cap B$。''',
"HW-P012-Y0440": r'''判断下列各组对象能否构成集合。若能构成集合，指出是有限集还是无限集；若不能构成集合，试说明理由。
\subq{1}我国古代四大名著的名称；
\subq{2}尾数是 5 的自然数；
\subq{3}我们班身高大于 $1.7\,\mathrm m$ 的同学。''',
"HW-P012-Y0651": r'''用符号“$\in$”和“$\notin$”填空：
\subq{1}$\dfrac12\blank\mathbb N$；
\subq{2}$1\blank\mathbb Z_-$；
\subq{3}$-2\blank\mathbb R$；
\subq{4}$\pi\blank\mathbb Q_+$；
\subq{5}$3^2\blank\mathbb N$；
\subq{6}$0\blank\varnothing$。''',
"HW-P012-Y0852": r'''用列举法表示下列集合：
\subq{1}组成中国国旗的颜色名称的集合；
\subq{2}方程组 $\begin{cases}3x-y=1,\\x+y=3\end{cases}$ 的解集。''',
"HW-P012-Y1024": r'''用描述法表示下列集合：
\subq{1}奇数组成的集合；
\subq{2}平面直角坐标系内第一象限的点组成的集合。''',
"HW-P012-Y1154": r'''判断下列关系是否成立。
\subq{1}$\{0\}\in(-2,3)$；
\subq{2}$\{a,c,b\}=\{a,b,c\}$；
\subq{3}$\mathbb R\subseteq(-\infty,-3]$；
\subq{4}$\{1,2,4\}\subsetneq\{x\mid x\text{ 是 }8\text{ 的约数}\}$。''',
"HW-P012-Y1286": r'''\subq{1}只有一个元素的集合有多少个子集？
\subq{2}两个元素组成的集合有多少个子集？
\subq{3}$n\ (n\in\mathbb Z_+)$ 个元素组成的集合有多少个子集？''',
"HW-P012-Y1412": r'''判断题（对的画“$\checkmark$”，错的画“$\times$”）：
\subq{1}根据研究问题的不同，可以指定不同的全集。\hfill（\quad）
\subq{2}设全集为 $U$，存在 $x_0\in U$，$x_0\notin A$，且 $x_0\notin\complement_U A$。\hfill（\quad）
\subq{3}设全集 $U=\mathbb R$，$A=\{x\mid x>\frac12\}$，则 $\complement_U A=\{x\mid x\le\frac12\}$。\hfill（\quad）
\subq{4}设全集 $U=\{(x,y)\mid x\in\mathbb R,\ y\in\mathbb R\}$，$A=\{(x,y)\mid x>0\text{ 且 }y>0\}$，$\complement_U A=\{(x,y)\mid x\ge0\text{ 且 }y\le0\}$。\hfill（\quad）''',
"HW-P013-Y0307": r'''设 $A=\{1,3,5\}$，$B=\{3,4,5,6,7\}$，$C=\{1,3,6,8\}$，求：
\subq{1}$A\cap B$，$A\cap C$，$A\cap(B\cup C)$；
\subq{2}$A\cup B$，$A\cup C$，$C\cup(A\cap B)$。''',
"HW-P013-Y0433": r'''已知集合 $A=\{x\mid-2<x\le5\}$，$B=\{x\mid2<x<8\}$，求 $\complement_{\mathbb R}(A\cup B)$，$\complement_{\mathbb R}(A\cap B)$，$(\complement_{\mathbb R}A)\cap B$，$A\cup(\complement_{\mathbb R}B)$。''',
"HW-P013-Y0665": r'''已知集合 $A=\{0,1,2,3,4\}$，$B=\{(x,y)\mid x\in A,\ y\in A,\ x+y\in A,\ x-y\in A\}$，求集合 $B$ 中元素的个数。''',
"HW-P013-Y0750": r'''在 $\mathbb N$，$\mathbb Z$，$\mathbb Q$，$\mathbb R$ 中任取两个，求它们的并集和交集。''',
"HW-P013-Y0794": r'''把 $\mathbb R$ 看成全集，用区间形式写出下列各集合的补集：
\subq{1}$A=(2,+\infty)$；
\subq{2}$B=(-\infty,1)$；
\subq{3}$C=[1,+\infty)$。''',
"HW-P013-Y0922": r'''设 $U$ 是全集，$A$，$B$ 是 $U$ 的两个非空子集，$A\cap B\ne\varnothing$，用 Venn 图表示：
\subq{1}$A\cap(\complement_U B)$；
\subq{2}$B\cap(\complement_U A)$；
\subq{3}$(\complement_U A)\cap(\complement_U B)$；
\subq{4}$(\complement_U A)\cup(\complement_U B)$。''',
"HW-P013-Y1051": r'''一家市场调查公司为了了解当地市民在阅读某种报纸（纸质版和电子版）方面的取向，抽样调查了 500 个市民，调查结果显示：订阅纸质版的有 334 人，订阅电子版的有 297 人，其中两种都订的有 150 人。试问：
\subq{1}只订纸质版不订电子版的有多少人？
\subq{2}只订电子版不订纸质版的有多少人？
\subq{3}至少订一种的有多少人？
\subq{4}一种都没订的有多少人？''',
"HW-P013-Y1352": r'''设 $I=\{x\in\mathbb Z\mid x^3\in[-125,125]\}$，$A=\{2k\mid-5<2k<5,\ k\in\mathbb Z\}$，$B=\{2k+1\mid k\in[0,3),\ k\in\mathbb Z\}$，求 $\complement_I A$，$\complement_I B$。''',
"HW-P013-Y1442": r'''设 $\mathbb R$ 为全集，$A=\{x\mid x<a\}$，$B=\{x\mid1<x<2\}$，且 $A\cup\overline B=\mathbb R$，求 $a$ 的取值范围。''',
"HW-P013-Y1531": r'''已知 $U=\{1,2,3,4,5,6,7,8\}$，$A\cap(\complement_U B)=\{1,8\}$，$(\complement_U A)\cap B=\{2,6\}$，$(\complement_U A)\cap(\complement_U B)=\{4,7\}$，求集合 $A$，$B$。''',
}
