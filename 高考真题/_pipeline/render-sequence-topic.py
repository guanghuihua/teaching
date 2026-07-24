#!/usr/bin/env python3
"""Render aligned sequence questions and answers as shared exam-zh content."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import shutil
import struct
from pathlib import Path


MAJOR_HEADINGS = {
    "等差数列的性质",
    "等比数列的性质",
    "数列求和",
}

TEACHING_SUPPLEMENTS = r"""
\ifshowanswers
\section*{教学补充：典型问题的多种解法}

\subsection*{一、等差数列前 $n$ 项和的最值}
设 $a_n=a_1+(n-1)d$，且 $a_1>0,\ d<0$。

\textbf{方法一（看项的正负）}\quad
$S_{n+1}-S_n=a_{n+1}$，所以部分和在下一项为正时增加、为负时减少。
若 $a_m>0,\ a_{m+1}<0$，则 $S_m$ 是唯一最大值；
若 $a_{m+1}=0$，则 $S_m=S_{m+1}$，两者同为最大值。
这一步能够避免只看二次函数对称轴时漏掉“两个相邻整数同为最值”的情形。

\textbf{方法二（二次函数）}\quad
\[
S_n=na_1+\frac{n(n-1)}2d
=\frac d2n^2+\left(a_1-\frac d2\right)n .
\]
其对称轴为
\[
n_0=\frac12-\frac{a_1}{d}.
\]
在正整数中取离 $n_0$ 最近的整数；若 $n_0$ 恰为半整数，则两个相邻整数对应的部分和相等。

\textbf{方法三（中间项）}\quad
$S_n=\dfrac n2(a_1+a_n)$。在已经能判断正、负项分界的位置时，
用 $a_n$ 与 $a_{n+1}$ 的符号直接确定最值，通常比展开 $S_n$ 更快。

\subsection*{二、$\{a_n\}$ 与 $\left\{\dfrac{S_n}{n}\right\}$ 的等差性}
\textbf{正向证明}\quad 若 $\{a_n\}$ 是等差数列，则
\[
\frac{S_n}{n}=\frac{a_1+a_n}{2},
\]
右端是关于 $n$ 的一次式，故 $\left\{\dfrac{S_n}{n}\right\}$ 也是等差数列。

\textbf{反向证明}\quad 若
\[
\frac{S_n}{n}=u+(n-1)v,
\]
则 $S_n=vn^2+(u-v)n$。由 $a_1=S_1$，以及 $n\ge2$ 时
$a_n=S_n-S_{n-1}$，统一得到
\[
a_n=u+2(n-1)v,
\]
所以 $\{a_n\}$ 是等差数列。这里必须单独检查 $n=1$，不能只写
$a_n=S_n-S_{n-1}$ 后默认结论对首项成立。

\subsection*{三、等差乘等比型求和}
以 $T_n=\sum_{k=1}^n kq^k$ 为例。

\textbf{方法一（错位相减）}\quad 当 $q\ne1$ 时，把 $T_n$ 与 $qT_n$ 对齐相减：
\[
(1-q)T_n=q+q^2+\cdots+q^n-nq^{n+1},
\]
从而
\[
T_n=\frac{q\left[1-(n+1)q^n+nq^{n+1}\right]}{(1-q)^2}.
\]
当 $q=1$ 时，$T_n=\dfrac{n(n+1)}2$。

\textbf{方法二（求导法）}\quad 由
\[
1+q+\cdots+q^n=\frac{1-q^{n+1}}{1-q}
\]
两边对 $q$ 求导，再乘以 $q$，即可得到同一公式。
此法适合教师讲解公式来源；考场书写通常以错位相减更稳妥。

\subsection*{四、裂项求和中的等号与放缩}
例如
\[
\frac{1}{n(n+2)}
=\frac12\left(\frac1n-\frac1{n+2}\right)
\]
是恒等变形，可以直接得到精确和；而
\[
\frac1{n^2}<\frac1{n(n-1)}
=\frac1{n-1}-\frac1n\qquad(n\ge2)
\]
是放缩，只能推出上界。教学时应明确标出“恒等裂项”与“为便于求界而放缩”的区别，
并检查放缩方向及起始项，避免把严格不等式误写成等式。
\fi
"""

# The source repeats these questions later with additional subquestions. Keep the
# expanded versions and omit the shorter copies; the third range is a literal copy.
EXCLUDED_ANSWER_RANGES = (
    range(44, 55),
    range(119, 130),
    range(503, 514),
)

# Optional teaching edition: retain one representative question for each core
# solution pattern. Values are source paragraph indices of the removed stems.
DEDUPLICATED_QUESTION_STARTS = {
    106,
    113,
    220,
    242,
    316,
    320,
    330,
    390,
    393,
    404,
    408,
    436,
    466,
    533,
    542,
    584,
    699,
    744,
    773,
    782,
    1210,
    1240,
    1251,
}

FORMULA_OVERRIDES = {
    "image31.wmf": (
        r"\begin{aligned}"
        r"(1+1)&=2\times1,\\"
        r"(2+1)(2+2)&=2^2\times1\times3,\\"
        r"(3+1)(3+2)(3+3)&=2^3\times1\times3\times5."
        r"\end{aligned}"
    ),
    "image34.wmf": (
        r"a_n=\begin{cases}S_1,&n=1,\\S_n-S_{n-1},&n\geq2.\end{cases}"
    ),
    "image35.wmf": r"\Longrightarrow",
    "image38.wmf": r"\quad\text{时，}\quad a_n=S_n-S_{n-1}",
    "image65.png": (
        r"\left[1+\frac{\lambda(n-1)}2\right]"
        r"\left(1+\frac{\lambda n}2\right)"
    ),
    "image67.png": r"\begin{cases}\lambda\ne0,\\2-\dfrac{\lambda}{2}=0,\end{cases}",
    "image78.wmf": r"\therefore",
    "image82.wmf": r"\therefore",
    "image86.wmf": r"\therefore",
    "image122.wmf": (
        r"\begin{aligned}a_n&=a_1+(n-1)d,\\a_n&=a_1q^{n-1}\end{aligned}"
    ),
    "image126.png": r"b_{n+1}=\frac{b_n}{b_n+1}",
    "image128.png": r"b_{n+1}=\frac{b_n}{b_n+1}",
    "image152.png": r"\frac1{a_na_{n+1}}",
    "image157.wmf": r"q",
    "image172.wmf": r"\because",
    "image179.wmf": r"\{a_n\}",
    "image185.wmf": r"\vdots",
    "image186.wmf": (
        r"\begin{aligned}"
        r"a_2-a_1&=3,\\a_3-a_2&=5,\\a_4-a_3&=7,\\"
        r"&\ \vdots\\a_n-a_{n-1}&=2n-1."
        r"\end{aligned}"
    ),
    "image193.wmf": (
        r"\frac{a_2}{a_1}\frac{a_3}{a_2}\cdots\frac{a_n}{a_{n-1}}"
        r"=\frac21\frac32\frac43\cdots\frac{n}{n-1}=n,"
        r"\quad\frac{a_n}{a_1}=n,\quad a_n=2n"
    ),
    "image210.wmf": r"\{a_n\}",
    "image214.wmf": r"\{a_n\}",
    "image219.wmf": r"\{a_n+1\}",
    "image274.wmf": r"a_{n+1}=qa_n+d^n\quad(q,d\ne0,\ q\ne1,\ d\ne1)",
    "image277.wmf": r"a_{n+1}=Aa_n+B\quad(A,B\text{为常数})",
    "image288.wmf": r"\{a_n\}\text{的通项公式：}",
    "image323.wmf": r"\{a_n\}",
    "image392.wmf": r"\frac{S_3}{S_6}=\frac13,\quad\frac{S_6}{S_{12}}=",
    "image395.wmf": r"\{a_n\}",
    "image424.png": (
        r"\begin{cases}49+21d<56+28d,\\63+36d<56+28d,\end{cases}"
    ),
    "image528.wmf": (
        r"\begin{cases}a_1>0,&\{a_n\}\text{为递增数列},\\"
        r"a_1<0,&\{a_n\}\text{为递减数列},\end{cases}"
    ),
    "image529.wmf": (
        r"\begin{cases}a_1>0,&\{a_n\}\text{为递减数列},\\"
        r"a_1<0,&\{a_n\}\text{为递增数列},\end{cases}"
    ),
    "image604.png": r"5a_3a_1=(2a_2+2)^2",
    "image611.wmf": r"\ldots",
    "image618.wmf": r"\ldots",
    "image622.wmf": r"\ldots",
    "image650.wmf": r"q",
    "image690.png": r"\left(\frac{\sqrt2}{2},\frac{\sqrt3}{3}\right)",
    "image693.wmf": r"\log_a^{\,1+\frac1n}=\log_a^{\,n+1}-\log_a^{\,n}",
    "image723.png": (
        r"\begin{cases}3a_1+3d=0,\\"
        r"5a_1+\dfrac{5(5-1)}2d=-5,\end{cases}"
    ),
    "image865.png": r"\begin{cases}13+3d\geq0,\\13+4d\leq0,\end{cases}",
    "image917.png": r"b_1+b_2+\cdots+b_n<\sqrt{\frac n3}",
    "image930.png": (
        r"b_n=\frac{\sqrt{a_na_{n+1}}}{\sqrt{a_n}+\sqrt{a_{n+1}}}"
    ),
    "image938.png": r"b_1+b_2+\cdots+b_n<\sqrt{\frac n3}",
    "image992.png": (
        r"\begin{cases}4a_1+6d=8a_1+4d,\\"
        r"a_1+(2n-1)d=2a_1+2(n-1)d+1,\end{cases}"
    ),
    "image1023.png": r"\frac23",
    "image1030.png": r"\begin{cases}a_1+d=4,\\(a_1+3d)+(a_1+6d)=15,\end{cases}",
    "image1031.png": r"\begin{cases}a_1=3,\\d=1,\end{cases}",
    "image1088.wmf": r"q",
    "image1121.wmf": r"\therefore",
    "image1138.wmf": (
        r"\begin{cases}S_2=d<1,\\S_3=3d<1,\end{cases}"
        r"\Longrightarrow d<\frac13"
    ),
    "image1210.wmf": r"\therefore",
    "image1213.wmf": r"\therefore",
    "image1267.wmf": r"\begin{cases}a_1=2,\\d=1,\end{cases}",
    "image1268.wmf": r"\begin{cases}a_1=-2,\\d=-1,\end{cases}",
    "image1269.wmf": r"\begin{cases}a_1=2,\\d=1,\end{cases}",
    "image1271.wmf": r"\begin{cases}a_1=-2,\\d=-1,\end{cases}",
    "image1288.wmf": r"\begin{cases}2+d=2q+1,\\2+2d=2q^2,\end{cases}",
    "image1289.wmf": r"\begin{cases}d=3,\\q=2,\end{cases}",
    "image1317.wmf": r"\because",
    "image1323.wmf": r"\therefore",
    "image1326.wmf": r"\therefore",
    "image1329.wmf": r"\therefore",
    "image1365.wmf": r"\ldots",
    "image1379.wmf": r"\ldots",
    "image1418.wmf": r"\therefore",
    "image1419.wmf": (
        r"\begin{cases}a_1+d=11,\\10a_1+\dfrac{10\cdot9}{2}d=40,\end{cases}"
    ),
    "image1420.wmf": r"\begin{cases}a_1+d=11,\\a_1+\dfrac92d=4,\end{cases}",
    "image1424.wmf": (
        r"|a_n|=|-2n+15|="
        r"\begin{cases}-2n+15,&1\leq n\leq7,\\2n-15,&n\geq8.\end{cases}"
    ),
    "image1425.wmf": r"1\leq n\leq7",
    "image1429.wmf": r"1\leq n\leq7",
    "image1445.wmf": r"\therefore",
    "image1446.wmf": (
        r"\begin{cases}a_1+d+a_1+4d=2a_1+5d=16,\\"
        r"a_1+4d-a_1-2d=2d=4,\end{cases}"
    ),
    "image1441.wmf": r"\sum_{i=2^{n-1}}^{2^n-1}a_i\quad(n\in N^*)",
    "image1451.wmf": r"\sum_{i=2^{n-1}}^{2^n-1}a_i",
    "image1452.wmf": r"a_{2^{n-1}}=2\cdot2^{n-1}+1=2^n+1",
    "image1454.wmf": (
        r"\sum_{i=2^{n-1}}^{2^n-1}a_i"
        r"=\frac{2^{n-1}\left[(2^n+1)+(2^{n+1}-1)\right]}2"
        r"=3\cdot2^{2n-2}"
    ),
    "image1472.wmf": r"\because",
    "image1473.wmf": (
        r"\begin{cases}3(a_1+d)=3a_1+a_1+2d,\\"
        r"3a_1+3d+\left(\dfrac2{a_1}+\dfrac6{a_1+d}"
        r"+\dfrac{12}{a_1+2d}\right)=21,\end{cases}"
    ),
    "image1474.wmf": r"\therefore",
    "image1475.wmf": r"\begin{cases}a_1=d,\\6d+\dfrac9d=21,\end{cases}",
    "image1478.wmf": r"\therefore",
    "image1486.wmf": r"\because",
    "image1497.wmf": r"\therefore",
    "image1501.wmf": r"\therefore",
    "image1507.wmf": r"\therefore",
    "image1511.wmf": r"\therefore",
    "image1513.wmf": r"\therefore",
    "image1521.wmf": r"m\}",
    "image1530.wmf": r"m\}",
    "image1583.wmf": r"\because",
    "image1696.wmf": r"\therefore",
    "image20.wmf": r"a_n=\frac{7}{10}\left(10^n-1\right)",
    "image26.wmf": r"a_n=(-1)^{n+1}+1",
    "image27.wmf": r"a_n=1-\cos n\pi",
    "image40.wmf": r"a_n",
    "image123.wmf": r"a_1",
    "image180.wmf": r"a_1",
    "image221.wmf": r"a_n=2\cdot3^{n-1}-1",
    "image261.wmf": r"\xrightarrow{\text{解决方法}}",
    "image265.wmf": (
        r"a_{n+1}=\frac{2a_n}{2a_n+1},\quad"
        r"\frac1{a_{n+1}}=\frac{2a_n+1}{2a_n}"
    ),
    "image264.wmf": r"a_n",
    "image270.wmf": r"a_n=\frac{2^{n+1}}{2^{n+2}-7}",
    "image271.wmf": r"\{a_n\}",
    "image278.wmf": r"\frac{a_{n+1}}{2^{n+1}}-\frac{a_n}{2^n}=\frac12",
    "image285.wmf": r"a_n",
    "image399.wmf": r"\frac{S_{\text{奇}}}{S_{\text{偶}}}=",
    "image396.wmf": r"\frac{S_{\text{奇}}}{S_{\text{偶}}}=\frac{a_n}{a_{n+1}}",
    "image419.wmf": r"a_5\text{与}a_9\text{互为相反数}",
    "image404.wmf": r"S_n=pn^2+qn=\frac{d}{2}n^2+\left(a_1-\frac{d}{2}\right)n",
    "image409.wmf": r"\begin{cases}a_n\geq0,\\a_{n+1}\leq0,\end{cases}",
    "image421.png": r"\frac78",
    "image429.png": r"\frac{S_n}{n}",
    "image430.png": r"\frac{S_{m-1}}{m-1}",
    "image431.png": r"\frac{S_m}{m}",
    "image432.png": r"\frac{S_{m+1}}{m+1}",
    "image433.png": r"\frac{S_m}{m}",
    "image434.png": r"\frac{S_{m-1}}{m-1}",
    "image435.png": r"\frac{S_{m+1}}{m+1}",
    "image436.png": r"-\frac2{m-1}",
    "image437.png": r"\frac3{m+1}",
    "image462.wmf": r"S_n=S_m\ \Longrightarrow\ S_{m+n}=0",
    "image530.wmf": r"\frac{S_{\text{奇}}}{S_{\text{偶}}}=\frac1q",
    "image535.png": r"\frac1{a_n}",
    "image541.png": (
        r"\frac{\frac12\left(1-\frac1{2^n}\right)}{1-\frac12}"
    ),
    "image562.png": r"\frac{1-3^n}{1-3}",
    "image570.png": r"\frac1{a_2}",
    "image571.png": r"\frac1{a_n}",
    "image585.png": r"\frac1{a_2}",
    "image586.png": r"\frac1{a_n}",
    "image593.png": r"\frac1{a_2}",
    "image594.png": r"\frac1{a_n}",
    "image596.png": r"\frac1{a_n}",
    "image601.png": r"|T_n-1|<\frac1{1000}",
    "image602.png": r"\left|1-\frac1{2^n}-1\right|<\frac1{1000}",
    "image603.png": r"<\frac1{1000}",
    "image1054.png": (
        r"\begin{cases}"
        r"2,&n=1,\\"
        r"\dfrac{3^n-n^2-5n+11}{2},&n\geq2."
        r"\end{cases}"
    ),
    "image1517.wmf": r"m\ (m>2)",
    "image1518.wmf": r"a_n",
    "image1520.wmf": r"\ldots",
    "image1528.wmf": r"k\in\{0",
    "image1529.wmf": r"\ldots",
    "image1531.wmf": r"r_k=\max\{i\mid B_i\leq A_k",
    "image1532.wmf": r"i\in\{0",
    "image1533.wmf": r"\ldots",
    "image1534.wmf": r"m\}\}",
    "image1535.wmf": r"\max M",
    "image1543.wmf": r"r_0",
    "image1544.wmf": r"r_1",
    "image1545.wmf": r"r_2",
    "image1546.wmf": r"r_3",
    "image1561.wmf": r"S_6=189",
    "image1254.wmf": r"\{a_n\}",
    "image1385.wmf": r"a_4",
    "image1393.wmf": r"a_4",
    "image1401.wmf": r"a_4",
    "image1442.wmf": r"\{a_n\}",
    "image1483.wmf": r"\{a_n\}",
    "image1567.wmf": r"\{a_n\}",
    "image1571.wmf": r"S_6=189",
    "image1574.wmf": (
        r"\begin{cases}\dfrac{a_1(1-q^3)}{1-q}=21,\\"
        r"\dfrac{a_1(1-q^6)}{1-q}=189.\end{cases}"
    ),
    "image1575.wmf": r"1+q^3=9",
    "image1576.wmf": r"q^3=8",
    "image1682.wmf": r"\left\{k\mid b_k=a_m+a_1,\right.",
    "image1683.wmf": r"\left.1\leq m\leq500\right\}",
    "image1698.wmf": r"2^{k-1}=2m",
    "image1699.wmf": r"1\leq m\leq500",
    "image1700.wmf": r"2\leq2m\leq1000",
    "image1701.wmf": r"2\leq k\leq10",
    "image1702.wmf": r"\left\{k\mid b_k=a_m+a_1,\right.",
    "image1703.wmf": r"\left.1\leq m\leq500\right\}",
    "image664.wmf": r"a_n=f(n+1)-f(n)",
    "image665.wmf": r"a_n=\frac{1}{n(n+1)}=\frac{1}{n}-\frac{1}{n+1}",
    "image666.png": r"c_n=\frac{\sqrt{n+1}-\sqrt n}{\sqrt{n(n+1)}}",
    "image667.png": r"\frac{1}{\sqrt n}-\frac{1}{\sqrt{n+1}}",
    "image668.png": r"\frac{1}{(2n+1)(2n+3)}",
    "image669.png": r"\frac{1}{2}",
    "image670.png": r"\frac{1}{2n+1}",
    "image671.png": r"\frac{1}{2n+3}",
    "image672.png": r"b_n=\frac{1}{a_{n+1}^2}=\frac{1}{(2n+1)^2}",
    "image673.png": r"<\frac{1}{4n^2+4n}",
    "image674.png": r"\frac{1}{4}\left(\frac{1}{n}-\frac{1}{n+1}\right)",
    "image675.png": r"c_n=\frac{2}{n(n+2)}",
    "image676.png": r"\frac{1}{n}-\frac{1}{n+2}",
    "image740.png": r"\frac{a_{n+1}}{S_nS_{n+1}}",
    "image742.png": r"\frac{S_{n+1}-S_n}{S_nS_{n+1}}",
    "image743.png": r"\frac1{S_n}",
    "image744.png": r"\frac1{S_{n+1}}",
    "image746.png": r"-\frac1{S_2}+\frac1{S_2}-\frac1{S_3}",
    "image747.png": r"\frac1{S_n}",
    "image748.png": r"\frac1{S_{n+1}}",
    "image749.png": r"\frac1{S_1}",
    "image921.png": r"\frac17",
    "image924.png": r"a_n=\frac1{3n-2}",
    "image925.png": r"a_k=\frac1{3k-2}",
    "image928.png": r"\frac1{3(k+1)-2}",
    "image929.png": r"a_n=\frac1{3n-2}",
    "image945.png": r"\frac{(3n-1)4^{n+1}+4}{9}",
    "image948.png": r"\frac{2n+1}{2^n}",
    "image949.png": r"\frac{2n+5}{2^n}",
    "image952.png": r"\frac{2n+3}{2^{n-1}}",
    "image1044.png": r"\frac{b_3}{b_2}",
    "image1045.png": r"\frac{a_{14}-a_1}{13}",
    "image155.png": (
        r"a_n=\begin{cases}"
        r"2^{\frac{n-1}{2}},&n\text{为奇数},\\"
        r"2^{\frac n2},&n\text{为偶数}."
        r"\end{cases}"
    ),
    "image317.png": r"\frac{\frac{a_{n+1}}{n+1}}{\frac{a_n}{n}}=2",
    "image964.png": (
        r"\frac32+\frac12\cdot"
        r"\frac{\frac14\left(1-\frac1{2^{n-1}}\right)}{1-\frac12}"
        r"-\frac{a_n}{2^{n+1}}"
    ),
    "image986.png": (
        r"\frac{\frac12\left(1-\frac1{2^{n-2}}\right)}{1-\frac12}"
    ),
    "image1053.png": (
        r"\begin{cases}"
        r"2,&n=1,\\3,&n=2,\\"
        r"\dfrac{3^n-n^2-5n+11}{2},&n\geq3."
        r"\end{cases}"
    ),
}

OCR_CORRECTIONS = {
    "image60.png": r"\frac{\lambda}{\lambda-1}",
    "image61.png": r"\frac1{1-\lambda}",
    "image59.png": r"\frac{a_n}{a_{n-1}}",
    "image63.png": r"a_n=1+\frac{\lambda(n-1)}2",
    "image66.png": (
        r"\frac{\lambda^2}{4}n^2+\left(\lambda-\frac{\lambda^2}{4}\right)n"
        r"+2-\frac{\lambda}{2}"
    ),
    "image68.png": r"S_n=n^2",
    "image90.png": (
        r"a_n=\begin{cases}3,&n=1,\\3^{n-1},&n>1.\end{cases}"
    ),
    "image93.png": r"S_n^2-(n^2+n-3)S_n-3(n^2+n)=0",
    "image96.png": r"a_n=S_n-S_{n-1}=(n^2+n)-[(n-1)^2+(n-1)]=2n",
    "image97.png": r"a_n=2n\quad(n\in N^*)",
    "image129.png": r"\frac1{b_{n+1}}=\frac{b_n+1}{b_n}=1+\frac1{b_n}",
    "image131.png": r"\frac1{b_1}",
    "image132.png": r"\frac12",
    "image134.png": r"\frac12",
    "image135.png": r"\frac1{a_na_{n+1}}",
    "image137.png": r"\frac1{a_na_{n+1}}",
    "image142.png": r"\frac1{a_1}",
    "image143.png": r"\frac1{a_1+d}",
    "image144.png": r"\frac1{a_1+d}",
    "image149.png": r"\frac1{a_1}",
    "image200.png": r"\frac12",
    "image203.png": r"a_1+\frac12=\frac32",
    "image204.png": r"\frac12",
    "image206.png": r"\frac12",
    "image229.png": r"\frac12",
    "image230.png": r"\frac92",
    "image250.png": r"\frac12",
    "image255.png": r"\frac12",
    "image299.png": r"\frac12",
    "image298.png": r"\frac{2+2}{2^{2-1}}",
    "image305.png": r"\frac12",
    "image309.png": r"\frac12",
    "image295.png": r"\frac2{2n-1}",
    "image296.png": r"\frac{n+2}{2^{n-1}}",
    "image297.png": r"\frac{n+2}{2^{n-1}}",
    "image300.png": r"\frac{n+2}{2^{n-1}}",
    "image301.png": r"\frac{n+1}{2^{n-2}}",
    "image303.png": r"\frac1{2^{n-1}}",
    "image318.png": r"b_n=\frac{a_n}{n}",
    "image320.png": r"b_n=b_1\cdot2^{n-1}=2^{n-1}",
    "image322.png": r"a_n=n\cdot2^{n-1}",
    "image331.png": r"\frac{S_9}{S_5}=\frac{9a_5}{5a_3}=9",
    "image344.png": r"\frac12",
    "image428.png": r"\frac{m(a_1+a_m)}2",
    "image468.png": r"q^{m^2}",
    "image469.png": r"q^{m^2}",
    "image475.png": r"\frac12",
    "image537.png": r"\frac12",
    "image542.png": r"\frac{a_1(1-q^n)}{1-q}",
    "image546.png": r"\frac{a_1(1-q^n)}{1-q}",
    "image548.png": r"a_1",
    "image549.png": r"a_2",
    "image550.png": r"a_n",
    "image558.png": r"\frac{a_1(1-q^n)}{1-q}",
    "image564.png": r"a_{11}^2=a_1a_{13}",
    "image565.png": r"(a_1+10d)^2=a_1(a_1+12d)",
    "image568.png": r"\frac12",
    "image569.png": r"\frac1{a_1}",
    "image575.png": r"a_1+\frac12=\frac32",
    "image576.png": r"\frac12",
    "image584.png": r"\frac1{a_1}",
    "image592.png": r"\frac1{a_1}",
    "image605.png": r"5(a_1+2d)a_1=(2a_1+2d+2)^2",
    "image606.png": (
        r"|a_1|+|a_2|+\cdots+|a_n|=S_n"
        r"=-\frac12n^2+\frac{21}{2}n"
    ),
    "image672.png": r"b_n=\frac1{a_{n+1}^2}=\frac1{(2n+1)^2}",
    "image686.png": (
        r"\frac1{a_n\sqrt{a_{n+1}}+a_{n+1}\sqrt{a_n}}"
    ),
    "image688.png": r"\frac{\sqrt n}{n}-\frac{\sqrt{n+1}}{n+1}",
    "image691.png": r"\left(\frac{\sqrt n}{n}-\frac{\sqrt{n+1}}{n+1}\right)",
    "image692.png": r"1-\frac{\sqrt{n+1}}{n+1}",
    "image703.png": r"\frac1{b_{n+1}}=\frac{b_n+1}{b_n}=1+\frac1{b_n}",
    "image705.png": r"\frac1{b_1}",
    "image706.png": r"\frac1{b_1}=1",
    "image707.png": r"\frac1{b_n}=\frac1{b_1}+(n-1)=n",
    "image709.png": r"b_nb_{n+1}=\frac1{n(n+1)}=\frac1n-\frac1{n+1}",
    "image711.png": r"\frac{a_n}{2n+1}",
    "image713.png": r"\frac{a_n}{2n+1}",
    "image721.png": r"\frac1{a_{2n-1}a_{2n+1}}",
    "image726.png": r"\frac1{a_{2n-1}a_{2n+1}}",
    "image728.png": r"\frac12\left(-1-\frac1{2n-1}\right)=\frac{n}{1-2n}",
    "image729.png": (
        r"b_n=\frac1{\log_2(a_n+3)\log_2(a_{n+1}+3)}"
    ),
    "image730.png": r"\frac1{\log_2 2^n\log_2 2^{n+1}}",
    "image734.png": r"\frac12",
    "image735.png": r"\frac12",
    "image740.png": r"\frac{a_{n+1}}{S_nS_{n+1}}",
    "image741.png": r"\frac{a_1(1-q^n)}{1-q}",
    "image745.png": r"\frac1{S_1}",
    "image749.png": r"\frac1{S_1}",
    "image751.png": (
        r"\frac{2S_n}{n}=a_{n+1}-\frac13n^2-n-\frac23"
    ),
    "image754.png": (
        r"2S_n=na_{n+1}-\frac13n^3-n^2-\frac23n"
    ),
    "image755.png": (
        r"2S_{n-1}=(n-1)a_n-\frac13(n-1)^3-(n-1)^2-\frac23(n-1)"
    ),
    "image756.png": r"2a_n=na_{n+1}-(n-1)a_n-n^2-n",
    "image757.png": r"\frac{a_{n+1}}{n+1}=\frac{a_n}{n}+1",
    "image758.png": r"\frac{a_{n+1}}{n+1}-\frac{a_n}{n}=1",
    "image761.png": r"\frac{a_n}{n}=n",
    "image762.png": r"a_n=n^2",
    "image763.png": (
        r"\frac1{a_n}=\frac1{n^2}<\frac1{(n-1)n}"
        r"=\frac1{n-1}-\frac1n"
    ),
    "image778.png": r"\frac12",
    "image780.png": r"-(n^2+n-1)S_n-(n^2+n)=0",
    "image783.png": r"-(n^2+n-1)S_n-(n^2+n)=0",
    "image789.png": (
        r"\frac1{(n-1)^2}-\frac1{(n+1)^2}"
        r"+\frac1{n^2}-\frac1{(n+2)^2}"
    ),
    "image791.png": r"<\frac1{16}\left(1+\frac14\right)=\frac5{64}",
    "image792.png": r"\frac1{a_1(a_1+1)}",
    "image798.png": r"S_n^2-(n^2+n-3)S_n-3(n^2+n)=0",
    "image801.png": r"a_n=S_n-S_{n-1}=(n^2+n)-[(n-1)^2+(n-1)]=2n",
    "image806.png": r"\frac12",
    "image808.png": r"\frac1{a_1(a_1+1)}",
    "image811.png": (
        r"\frac1{a_1(a_1+1)}+\frac1{a_2(a_2+1)}+\cdots"
        r"+\frac1{a_n(a_n+1)}"
    ),
    "image815.png": r"\frac12",
    "image817.png": (
        r"\frac1{a_1(a_1+1)}+\frac1{a_2(a_2+1)}+\cdots"
        r"+\frac1{a_n(a_n+1)}"
    ),
    "image819.png": r"\frac12",
    "image822.png": r"\frac12",
    "image826.png": r"\frac12",
    "image835.png": r"\frac12",
    "image838.png": r"\frac{4n}{a_na_{n+1}}",
    "image841.png": r"(2^2-2+2a_1)^2=a_1(4^2-4+4a_1)",
    "image865.png": r"\begin{cases}13+3d\geq0,\\13+4d\leq0,\end{cases}",
    "image883.png": r"\frac12",
    "image892.png": r"\frac12",
    "image903.png": r"\sqrt{n+1}",
    "image911.png": r"\sqrt{n+1}",
    "image915.png": r"a_{n+1}=\frac{(n-1)a_n}{n-a_n}\quad(n\geq2)",
    "image916.png": (
        r"b_n=\frac{\sqrt{a_na_{n+1}}}{\sqrt{a_n}+\sqrt{a_{n+1}}}"
    ),
    "image919.png": r"a_{n+1}=\frac{(n-1)a_n}{n-a_n}\quad(n\geq2)",
    "image920.png": r"\frac{a_2}{2-a_2}",
    "image926.png": r"a_{k+1}=\frac{(k-1)a_k}{k-a_k}",
    "image930.png": (
        r"b_n=\frac{\sqrt{a_na_{n+1}}}{\sqrt{a_n}+\sqrt{a_{n+1}}}"
    ),
    "image938.png": r"b_1+b_2+\cdots+b_n<\sqrt{\frac n3}",
    "image943.png": r"a_nb_n=n\cdot2^n",
    "image944.png": r"T_n=(n-1)2^{n+1}+2",
    "image947.png": r"S_n=(2n-3)2^n+3\quad(n\in N^*)",
    "image961.png": (
        r"\frac{a_1}{2^1}+\frac{a_2}{2^2}+\cdots"
        r"+\frac{a_{n-1}}{2^{n-1}}+\frac{a_n}{2^n}"
    ),
    "image969.png": r"\frac{a_{n+1}}{n+1}=\frac{a_n}{n}+1",
    "image970.png": r"\frac{a_{n+1}}{n+1}-\frac{a_n}{n}=1",
    "image971.png": r"\frac{a_n}{n}=1+(n-1)\cdot1=n",
    "image981.png": r"\frac12",
    "image1007.png": r"\frac12",
    "image1031.png": r"\begin{cases}a_1=3,\\d=1,\end{cases}",
    "image1043.png": (
        r"\frac{n(n+1)}2+2^{n+1}-n-2=n+2^{n+1}"
    ),
    "image1046.png": r"\frac12",
    "image1051.png": r"\frac{(n+7)(n-2)}2",
    # Complex PNG equations checked against the surrounding derivation.
    "image94.png": r"(S_n+3)\bigl[S_n-(n^2+n)\bigr]=0",
    "image138.png": r"\frac1{[a_1+(n-1)d](a_1+nd)}",
    "image150.png": r"\frac{n}{a_1(a_1+nd)}",
    "image151.png": r"\frac{n}{a_1^2+a_1dn}",
    "image154.png": r"\begin{cases}a_1^2=1,\\a_1d=2,\end{cases}",
    "image201.png": (
        r"\frac{a_{n+1}+\frac12}{a_n+\frac12}"
        r"=\frac{3a_n+1+\frac12}{a_n+\frac12}=3"
    ),
    "image202.png": r"\frac{3\left(a_n+\frac12\right)}{a_n+\frac12}",
    "image308.png": r"a_n=2^n\quad(n\in N^*)",
    "image312.png": r"\frac{b_n}{n}=b_{n+1}-b_n",
    "image313.png": r"\frac{b_{n+1}}{n+1}=\frac{b_n}{n}",
    "image319.png": r"\frac{b_{n+1}}{b_n}=2",
    "image422.png": r"\frac{n(n-1)d}{2}",
    "image479.png": r"a_1a_3^2a_5=a_3^4=\frac14",
    "image523.png": r"a_5^6=a_2^3a_8^3=50",
    "image566.png": r"\frac{n(a_1+a_{3n-2})}{2}",
    "image573.png": (
        r"\frac{a_{n+1}+\frac12}{a_n+\frac12}"
        r"=\frac{3a_n+1+\frac12}{a_n+\frac12}=3"
    ),
    "image574.png": r"\frac{3\left(a_n+\frac12\right)}{a_n+\frac12}",
    "image583.png": r"\frac1{a_1}=1<\frac32",
    "image600.png": (
        r"T_n=\frac12+\frac1{2^2}+\cdots+\frac1{2^n}"
        r"=\frac{\frac12\left[1-\left(\frac12\right)^n\right]}{1-\frac12}"
        r"=1-\frac1{2^n}"
    ),
    "image607.png": r"\frac12n^2-\frac{21}{2}n+110",
    "image608.png": (
        r"\begin{cases}"
        r"\frac12n^2+\frac{21}{2}n,&n\leq11,\\"
        r"\frac12n^2-\frac{21}{2}n+110,&n\geq12."
        r"\end{cases}"
    ),
    "image677.png": (
        r"\left(1-\frac13\right)+\left(\frac12-\frac14\right)"
        r"+\cdots+\left(\frac1n-\frac1{n+2}\right)"
    ),
    "image681.png": (
        r"\frac32-\frac{2n+3}{(n+1)(n+2)}"
        r"=\frac{n(3n+5)}{2(n+1)(n+2)}"
    ),
    "image682.png": r"\frac{2\cdot3^n}{a_na_{n+1}}",
    "image683.png": r"\frac{2\cdot3^n}{(3^n-1)(3^{n+1}-1)}",
    "image687.png": (
        r"\frac1{n\sqrt{n+1}+(n+1)\sqrt n}"
    ),
    "image689.png": r"1-\frac{\sqrt2}{2}",
    "image690.png": r"\frac{\sqrt2}{2}-\frac{\sqrt3}{3}",
    "image693.wmf": (
        r"\log_a\left(1+\frac1n\right)=\log_a(n+1)-\log_a n"
    ),
    "image694.wmf": (
        r"a_n=\frac{n+1}{n^2(n+2)^2}"
        r"=\frac14\left(\frac1{n^2}-\frac1{(n+2)^2}\right)"
    ),
    "image695.wmf": (
        r"a_n=\frac{n+2}{n(n+1)2^n}"
        r"=\frac{2(n+1)-n}{n(n+1)2^n}"
    ),
    "image696.wmf": (
        r"=\frac1{n2^{n-1}}-\frac1{(n+1)2^n}"
    ),
    "image697.wmf": r"S_n=1-\frac1{(n+1)2^n}",
    "image698.wmf": (
        r"a_n=\frac1{n(n+1)(n+2)}"
        r"=\frac12\left[\frac1{n(n+1)}-\frac1{(n+1)(n+2)}\right]"
    ),
    "image699.wmf": (
        r"a_n=\frac{(2n)^2}{(2n-1)(2n+1)}"
        r"=1+\frac12\left(\frac1{2n-1}-\frac1{2n+1}\right)"
    ),
    "image700.wmf": (
        r"a_n=\frac1{(An+B)(An+C)}"
        r"=\frac1{C-B}\left(\frac1{An+B}-\frac1{An+C}\right)"
    ),
    "image701.png": r"b_{n+1}=\frac{b_n}{b_n+1}",
    "image702.png": r"\left\{\frac1{b_n}\right\}",
    "image710.png": (
        r"S_n=1-\frac12+\frac12-\frac13+\cdots+\frac1n-\frac1{n+1}"
        r"=\frac{n}{n+1}"
    ),
    "image722.png": r"S_n=na_1+\frac{n(n-1)d}{2}",
    "image725.png": (
        r"\frac1{a_{2n-1}a_{2n+1}}"
        r"=\frac1{(3-2n)(1-2n)}"
        r"=\frac12\left(\frac1{2n-3}-\frac1{2n-1}\right)"
    ),
    "image727.png": (
        r"\frac12\left[\left(\frac1{-1}-1\right)"
        r"+\left(1-\frac13\right)+\cdots"
        r"+\left(\frac1{2n-3}-\frac1{2n-1}\right)\right]"
    ),
    "image752.png": (
        r"\frac1{a_1}+\frac1{a_2}+\cdots+\frac1{a_n}<\frac74"
    ),
    "image753.png": r"\frac{2S_1}{1}=2a_1=a_2-\frac13-1-\frac23",
    "image759.png": r"\frac{a_2}{2}-\frac{a_1}{1}=2-1=1",
    "image764.png": (
        r"\frac1{a_1}+\cdots+\frac1{a_n}"
        r"=1+\frac1{2^2}+\cdots+\frac1{n^2}"
        r"<1+\frac14+\left(\frac12-\frac13\right)+\cdots"
        r"+\left(\frac1{n-1}-\frac1n\right)"
    ),
    "image765.png": r"1+\frac14+\frac12-\frac1n=\frac74-\frac1n<\frac74",
    "image771.png": r"\frac{2\cdot3^n}{(3^n-1)(3^{n+1}-1)}",
    "image781.png": r"b_n=\frac{n+1}{(n+2)^2a_n^2}",
    "image782.png": r"T_n<\frac5{64}",
    "image785.png": r"b_n=\frac{n+1}{(n+2)^2a_n^2}",
    "image786.png": r"\frac{n+1}{4n^2(n+2)^2}",
    "image787.png": r"\frac1{16}\left(\frac1{n^2}-\frac1{(n+2)^2}\right)",
    "image788.png": (
        r"T_n=\frac1{16}\bigl[\left(1-\frac1{3^2}\right)"
        r"+\left(\frac1{2^2}-\frac1{4^2}\right)+\cdots"
    ),
    "image790.png": (
        r"\frac1{16}\left(1+\frac14-\frac1{(n+1)^2}-\frac1{(n+2)^2}\right)"
    ),
    "image799.png": r"(S_n+3)\bigl[S_n-(n^2+n)\bigr]=0",
    "image793.png": r"\frac1{a_2(a_2+1)}",
    "image797.png": r"S_1^2+S_1-6=0",
    "image807.png": r"\frac1{2n-1}-\frac1{2n+1}",
    "image812.png": r"\frac1{2(2+1)}",
    "image814.png": r"\frac13",
    "image816.png": r"\frac1{2n+1}",
    "image802.png": r"a_n=2n\quad(n\in N^*)",
    "image813.png": (
        r"\frac12\left(\frac13-\frac15+\frac15-\frac17+\cdots"
        r"+\frac1{2n-1}-\frac1{2n+1}\right)"
    ),
    "image825.png": r"\frac12\left(\frac1n-\frac1{n+2}\right)",
    "image829.png": r"\frac12\left(\frac1n-\frac1{n+2}\right)",
    "image831.png": (
        r"\frac12\bigl[\left(1-\frac13\right)"
        r"+\left(\frac12-\frac14\right)"
    ),
    "image839.png": r"na_1+\frac{n(n-1)d}{2}",
    "image823.png": r"\left(\frac12a_n+n\right)",
    "image842.png": r"(1+a_1)^2=a_1(3+a_1)",
    "image843.png": r"\frac{4n}{a_na_{n+1}}",
    "image845.png": (
        r"(-1)^{n-1}\left(\frac1{2n-1}+\frac1{2n+1}\right)"
    ),
    "image863.png": (
        r"\begin{cases}\dfrac{2n}{2n+1},&n\text{为偶数},\\"
        r"\dfrac{2n+2}{2n+1},&n\text{为奇数}.\end{cases}"
    ),
    "image881.png": r"\frac1{\sqrt{a_n}+\sqrt{a_{n+1}}}",
    "image882.png": r"\frac1{\sqrt{2n-1}+\sqrt{2n+1}}",
    "image884.png": r"\sqrt{2n-1}",
    "image885.png": r"\sqrt{2n-1}",
    "image886.png": r"\sqrt3-1",
    "image887.png": r"\sqrt5-\sqrt3",
    "image891.png": r"\sqrt{2n-1}",
    "image892.png": r"\frac12\left(\sqrt{2n+1}-1\right)",
    "image922.png": r"a_4=\frac{2a_3}{3-a_3}",
    "image927.png": (
        r"\frac{(k-1)\cdot\frac1{3k-2}}{k-\frac1{3k-2}}"
    ),
    "image931.png": r"\frac13\left(\sqrt{3n+1}-\sqrt{3n-2}\right)",
    "image932.png": (
        r"\frac13\left[(\sqrt4-1)+(\sqrt7-\sqrt4)+\cdots"
        r"+(\sqrt{3n+1}-\sqrt{3n-2})\right]"
    ),
    "image934.png": r"\frac13\left(\sqrt{3n+1}-1\right)<\sqrt{\frac n3}",
    "image955.png": r"c_n=b_n=\frac{2n-2}{2^{2n-1}}=\frac{n-1}{4^{n-1}}",
    "image956.png": r"R_n=\frac49\left(1-\frac{3n+1}{4^n}\right)",
    "image962.png": (
        r"\frac{a_1}{2^2}+\frac{a_2}{2^3}+\cdots"
        r"+\frac{a_{n-1}}{2^n}+\frac{a_n}{2^{n+1}}"
    ),
    "image963.png": (
        r"\frac{a_1}{2}+d\left(\frac1{2^2}+\cdots+\frac1{2^n}\right)"
        r"-\frac{a_n}{2^{n+1}}"
    ),
    "image965.png": (
        r"\frac32+\frac12\left(1-\frac1{2^{n-1}}\right)"
        r"-\frac{n+2}{2^{n+1}}"
    ),
    "image966.png": r"\frac{n+4}{2^{n+1}}",
    "image974.png": (
        r"S_n=1\cdot3+2\cdot3^2+3\cdot3^3+\cdots+(n-1)"
    ),
    "image975.png": (
        r"3S_n=1\cdot3^2+2\cdot3^3+3\cdot3^4+\cdots+(n-1)"
    ),
    "image976.png": r"-2S_n=3+3^2+3^3+\cdots+",
    "image979.png": r"S_n=\frac{2n-1}{4}\,3^{n+1}+\frac34",
    "image990.png": r"\frac{b_1}{a_1}+\frac{b_2}{a_2}+\cdots+\frac{b_n}{a_n}",
    "image999.png": r"\frac{b_n}{a_n}",
    "image1001.png": r"\frac1{2^{n-1}}",
    "image1003.png": r"\frac{2n-1}{2^n}",
    "image1009.png": r"\frac3{2^3}",
    "image1010.png": r"\frac{2n-3}{2^n}",
    "image1020.png": r"\frac{2n+3}{2^n}",
    "image1021.png": (
        r"a_n=\begin{cases}3,&n=1,\\3^{n-1},&n>1.\end{cases}"
    ),
    "image1041.png": r"S_n=\frac{n(n+1)}2",
    "image1042.png": (
        r"(2^1+2^2+\cdots+2^n)-n"
        r"=\frac{2(1-2^n)}{1-2}-n"
    ),
    "image3.wmf": r"\frac12,-\frac23,\frac34,-\frac45,\ldots",
    "image32.wmf": (
        r"(n+1)(n+2)\cdots(n+n)=2^n\cdot1\cdot3\cdot5\cdots(2n-1)"
    ),
}

FORMULA_OVERRIDES.update(OCR_CORRECTIONS)

RAW_LATEX_OVERRIDES = {
    "image326.wmf": (
        r"\begin{minipage}{0.94\linewidth}"
        r"已知 $\{a_n\}$ 是等差数列。\\"
        r"(1) $2a_3=a_1+a_5$ 是否成立？$2a_3=a_2+a_4$ 呢？为什么？\\"
        r"(2) $2a_n=a_{n-1}+a_{n+1}\ (n\geq2)$ 是否成立？"
        r"你能得出什么结论？"
        r"\end{minipage}"
    ),
    "image426.wmf": (
        r"若 $\{a_n\}$ 是等差数列，则 "
        r"$\left\{\dfrac{S_n}{n}\right\}$ 也是等差数列。"
    ),
    "image427.wmf": (
        r"点列 $(1,a_1),(2,a_2),\ldots,(n,a_n)$ 共线；"
        r"点列 $(1,S_1),(2,S_2),\ldots,(n,S_n)$ 共线。"
    ),
}

PARAGRAPH_OVERRIDES_BY_IMAGE = {
    "image311.png": (
        r"当 $n\geq2$ 时，"
        r"$b_1+\dfrac12b_2+\dfrac13b_3+\cdots"
        r"+\dfrac1{n-1}b_{n-1}=b_n-1$，与原递推式作差得，"
    ),
    "image541.png": (
        r"所以 $T_n=\dfrac12+\dfrac1{2^2}+\cdots+\dfrac1{2^n}"
        r"=\dfrac{\frac12\left(1-\frac1{2^n}\right)}{1-\frac12}"
        r"=1-\dfrac1{2^n}$．"
    ),
    "image601.png": (
        r"由 $|T_n-1|<\dfrac1{1000}$，得 "
        r"$\left|1-\dfrac1{2^n}-1\right|<\dfrac1{1000}$，"
        r"即 $2^n>1000$。又 $2^9=512<1000<1024=2^{10}$，故 $n\geq10$。"
    ),
    "image812.png": (
        r"\["
        r"\sum_{k=1}^{n}\frac1{a_k(a_k+1)}"
        r"<\frac16+\frac12\left(\frac13-\frac1{2n+1}\right)"
        r"=\frac13-\frac1{2(2n+1)}<\frac13."
        r"\]"
    ),
    "image819.png": (
        r"例10（2017·郑州二模）已知数列 $\{a_n\}$ 的前 $n$ 项和为 $S_n$，"
        r"$a_1=-2$，且 $S_n=\dfrac12a_{n+1}+n+1\ (n\in N^*)$。"
    ),
    "image820.png": (
        r"（Ⅱ）若 $b_n=\log_3(-a_n+1)$，求数列"
        r"$\left\{\dfrac1{b_nb_{n+2}}\right\}$ 的前 $n$ 项和 $T_n$，"
        r"并证明 $T_n<\dfrac34$。"
    ),
    "image843.png": (
        r"（Ⅱ）由（Ⅰ）可得"
        r"$b_n=(-1)^{n-1}\dfrac{4n}{a_na_{n+1}}"
        r"=(-1)^{n-1}\left(\dfrac1{2n-1}+\dfrac1{2n+1}\right)$。"
    ),
    "image852.png": (
        r"当 $n$ 为偶数时，"
        r"$T_n=1-\dfrac1{2n+1}=\dfrac{2n}{2n+1}$。"
    ),
    "image859.png": (
        r"当 $n$ 为奇数时，"
        r"$T_n=1+\dfrac1{2n+1}=\dfrac{2n+2}{2n+1}$。"
    ),
    "image882.png": (
        r"（Ⅱ）$b_n=\dfrac1{\sqrt{a_n}+\sqrt{a_{n+1}}}"
        r"=\dfrac1{\sqrt{2n-1}+\sqrt{2n+1}}"
        r"=\dfrac12\left(\sqrt{2n+1}-\sqrt{2n-1}\right)$，"
    ),
    "image886.png": (
        r"则 $\{b_n\}$ 的前 $n$ 项和为"
        r"\["
        r"\frac12\left[(\sqrt3-1)+(\sqrt5-\sqrt3)+\cdots"
        r"+(\sqrt{2n+1}-\sqrt{2n-1})\right]"
        r"=\frac12\left(\sqrt{2n+1}-1\right)."
        r"\]"
    ),
    "image892.png": "",
    "image1053.png": (
        r"则 $T_n=\begin{cases}"
        r"2,&n=1,\\3,&n=2,\\"
        r"\dfrac{3^n-n^2-5n+11}{2},&n\geq3."
        r"\end{cases}$"
    ),
}

PARAGRAPH_OVERRIDES_BY_PREFIX = {
    "1.（2013•福建）已知等比数列": (
        r"1.（2013·福建）已知等比数列 $\{a_n\}$ 的公比为 $q$，记"
        r"\["
        r"b_n=\sum_{i=1}^{m}a_{m(n-1)+i},\qquad{}"
        r"c_n=\prod_{i=1}^{m}a_{m(n-1)+i}"
        r"\]"
        r"（$m,n\in N^*$），则以下结论一定正确的是（\quad）。"
    ),
    "4.（2014•广东）等比数列": (
        r"4.（2014·广东）等比数列 $\{a_n\}$ 的各项均为正数，且"
        r"$a_1a_5=4$，则"
        r"\["
        r"\log_2a_1+\log_2a_2+\log_2a_3+\log_2a_4+\log_2a_5=5."
        r"\]"
    ),
    "【解答】解：log2a1+log2a2": (
        r"解："
        r"\["
        r"\sum_{k=1}^{5}\log_2a_k"
        r"=\log_2(a_1a_2a_3a_4a_5)"
        r"=\log_2a_3^5=5\log_2a_3."
        r"\]"
    ),
    "所以b_{1}+b_{2}+…+b_{n}=": (
        r"所以"
        r"\["
        r"\sum_{k=1}^{n}b_k"
        r"=\frac13\left[(\sqrt4-1)+(\sqrt7-\sqrt4)+\cdots"
        r"+(\sqrt{3n+1}-\sqrt{3n-2})\right]"
        r"=\frac13\left(\sqrt{3n+1}-1\right)."
        r"\]"
    ),
}


def signature(paragraph: dict) -> str:
    value = "".join(
        part.get("text", "") if part["type"] == "text" else "<IMG>"
        for part in paragraph["parts"]
    )
    value = value.replace("【解答】", "").replace("【分析】", "")
    return re.sub(r"\s+", "", value).strip()


def split_embedded_answers(paragraphs: list[dict]) -> list[dict]:
    """Split legacy Word paragraphs that contain both a stem and its answer."""
    result: list[dict] = []
    for paragraph in paragraphs:
        split_at: tuple[int, int] | None = None
        for part_index, part in enumerate(paragraph["parts"]):
            if part["type"] != "text":
                continue
            marker_index = part.get("text", "").find("【解答】")
            if marker_index > 0:
                split_at = (part_index, marker_index)
                break
        if split_at is None:
            result.append(paragraph)
            continue

        part_index, marker_index = split_at
        part = paragraph["parts"][part_index]
        stem_parts = paragraph["parts"][:part_index] + [
            {**part, "text": part["text"][:marker_index]}
        ]
        answer_parts = [
            {**part, "text": part["text"][marker_index:]}
        ] + paragraph["parts"][part_index + 1 :]
        result.extend(
            [
                {**paragraph, "parts": stem_parts},
                {**paragraph, "parts": answer_parts},
            ]
        )
    return result


def align_visible(question_paragraphs: list[dict], answer_paragraphs: list[dict]) -> set[int]:
    question_signatures = [signature(item) for item in question_paragraphs]
    answer_signatures = [signature(item) for item in answer_paragraphs]
    matcher = difflib.SequenceMatcher(
        None, question_signatures, answer_signatures, autojunk=False
    )
    blocks = matcher.get_matching_blocks()
    visible: set[int] = set()
    for block in blocks:
        visible.update(range(block.b, block.b + block.size))

    # Recover edited stems within each gap while preserving document order.
    anchors = [(0, 0)] + [
        (block.a + block.size, block.b + block.size) for block in blocks
    ]
    previous_q = previous_a = 0
    for next_q, next_a in anchors[1:]:
        q_gap = range(previous_q, next_q)
        a_start = previous_a
        for q_index in q_gap:
            wanted = question_signatures[q_index]
            if not wanted:
                continue
            best_index = None
            best_score = 0.0
            for a_index in range(a_start, next_a):
                candidate = answer_signatures[a_index]
                if not candidate or re.search(r"【(?:解答|答案|分析)】|\[答案\]", candidate):
                    continue
                score = difflib.SequenceMatcher(None, wanted, candidate, autojunk=False).ratio()
                if score > best_score:
                    best_index, best_score = a_index, score
            if best_index is not None and best_score >= 0.62:
                visible.add(best_index)
                a_start = best_index + 1
        previous_q, previous_a = next_q, next_a
    return visible


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    return struct.unpack(">II", header[16:24])


def is_formula(name: str, assets: Path) -> bool:
    if name in FORMULA_OVERRIDES or name in RAW_LATEX_OVERRIDES:
        return True
    if name.lower().endswith(".wmf"):
        return True
    _, height = png_size(assets / name)
    return height < 78


def escape_text(text: str) -> str:
    protected_math: list[str] = []

    def protect(latex: str) -> str:
        marker = f"@@MATH{len(protected_math)}@@"
        protected_math.append(rf"\ensuremath{{{latex}}}")
        return marker

    # Word's legacy equation runs often flatten superscripts into plain text.
    # Normalize full-width signs first so terms such as S_{n-1} stay intact.
    text = (
        text.replace("【解答】解：", "解：")
        .replace("【解答】", "")
        .replace("﹣", "-")
        .replace("－", "-")
        .replace("＋", "+")
        .replace("＞", ">")
        .replace("＜", "<")
    )
    # Word may split one exponent/subscript across several formatted runs, e.g.
    # ``2^{n}^{+}^{1}``. Join those runs before converting them to LaTeX.
    previous = None
    while text != previous:
        previous = text
        text = re.sub(
            r"\^\{([^{}]*)\}\s*\^\{([^{}]*)\}",
            lambda match: "^{" + match.group(1).strip() + match.group(2).strip() + "}",
            text,
        )
        text = re.sub(
            r"_\{([^{}]*)\}\s*_\{([^{}]*)\}",
            lambda match: "_{" + match.group(1).strip() + match.group(2).strip() + "}",
            text,
        )
    text = re.sub(r"\|Tn-1\|", lambda _: protect(r"|T_n-1|"), text)
    text = re.sub(
        r"log_\{([^{}]+)\}",
        lambda match: protect(rf"\log_{{{match.group(1)}}}"),
        text,
    )
    text = re.sub(
        r"([A-Za-z])_\{(奇|偶|中)\}",
        lambda match: protect(
            rf"{match.group(1)}_{{\text{{{match.group(2)}}}}}"
        ),
        text,
    )
    text = re.sub(
        r"([A-Za-z])_\{([^{}]*?)([，。])\}",
        lambda match: protect(rf"{match.group(1)}_{{{match.group(2)}}}")
        + match.group(3),
        text,
    )
    text = re.sub(
        r"([A-Za-z0-9])_\{([^{}]+)\}\^\{([^{}]+)\}",
        lambda match: protect(
            rf"{match.group(1)}_{{{match.group(2).replace('（', '(').replace('）', ')')}}}"
            rf"^{{{match.group(3)}}}"
        ),
        text,
    )
    text = re.sub(
        r"（([^（）]+)）\s*\^\{([^{}]+)\}",
        lambda match: protect(rf"({match.group(1)})^{{{match.group(2)}}}"),
        text,
    )
    text = re.sub(
        r"([A-Za-z0-9)])\s*\^\{([^{}]+)\}",
        lambda match: protect(rf"{match.group(1)}^{{{match.group(2)}}}"),
        text,
    )
    text = re.sub(
        r"([A-Za-z])_\{([^{}]+)\}",
        lambda match: protect(
            rf"{match.group(1)}_{{{match.group(2).replace('（', '(').replace('）', ')')}}}"
        ),
        text,
    )
    text = re.sub(
        r"\^\{([^{}]+)\}",
        lambda match: protect(rf"{{}}^{{{match.group(1)}}}"),
        text,
    )
    text = re.sub(r"_\{\s*\}", "", text)
    text = re.sub(
        r"([A-Z])n2\b",
        lambda match: protect(rf"{match.group(1)}_n^2"),
        text,
    )
    text = re.sub(
        r"\((n(?:[+\-]\d+)?)\)2\b",
        lambda match: protect(rf"({match.group(1)})^2"),
        text,
    )
    text = re.sub(r"\bn2\b", lambda _: protect(r"n^2"), text)
    text = re.sub(
        r"\blog(\d+)",
        lambda match: protect(rf"\log_{{{match.group(1)}}}"),
        text,
    )
    text = text.replace("N*", protect(r"N^*"))
    text = re.sub(
        r"[｛{]\s*([aAbBcCsStT])n\s*[｝}]",
        lambda match: protect(rf"\{{{match.group(1)}_n\}}"),
        text,
    )
    text = re.sub(
        r"([aAbBcCsStT])((?:n(?:[+\-]\d+)?)|\d+)",
        lambda match: protect(
            rf"{match.group(1)}_{{{match.group(2).replace('+', '+').replace('-', '-')}}}"
        ),
        text,
    )
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "$": r"\$",
        "^": r"\textasciicircum{}",
        "\t": r"\qquad{}",
        "\n": r"\par{}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    symbols = {
        "π": r"\ensuremath{\pi}",
        "λ": r"\ensuremath{\lambda}",
        "∈": r"\ensuremath{\in}",
        "≥": r"\ensuremath{\ge}",
        "≤": r"\ensuremath{\le}",
        "≠": r"\ensuremath{\ne}",
        "∞": r"\ensuremath{\infty}",
        "∵": r"\ensuremath{\because}",
        "∴": r"\ensuremath{\therefore}",
        "×": r"\ensuremath{\times}",
        "⇒": r"\ensuremath{\Longrightarrow}",
        "⇔": r"\ensuremath{\Longleftrightarrow}",
        "∀": r"\ensuremath{\forall}",
        "′": r"\ensuremath{'}",
        "…": r"\ldots{}",
        "△": r"\ensuremath{\triangle}",
    }
    for old, new in symbols.items():
        text = text.replace(old, new)
    for index, latex in enumerate(protected_math):
        text = text.replace(f"@@MATH{index}@@", latex)
    return text


def clean_formula(latex: str) -> str:
    latex = latex.strip()
    latex = re.sub(r"^\$|\$$", "", latex)
    latex = re.sub(r"^\\\[|\\\]$", "", latex)
    substitutions = {
        r"\mathbb{N}": r"\mathbb{N}",
        r"\mathrm{N}": "N",
        r"\boldsymbol{n}": "n",
        r"\boldsymbol{k}": "k",
        r"\boldsymbol{a}": "a",
        r"\boldsymbol{S}": "S",
        r"\mathbf{\pi}": r"\pi",
        r"\mathbb{T}": r"\pi",
        r"\mathrm{T}": r"\pi",
        r"\Phi": r"\varphi",
    }
    for old, new in substitutions.items():
        latex = latex.replace(old, new)
    latex = latex.replace(r"\left[", "[").replace(r"\right]", "]")
    latex = latex.replace(r"\right.", "").replace(r"\lbrack", "[")
    latex = latex.replace(r"\inN", r"\in N").replace(r"\inZ", r"\in Z")
    unicode_math = {
        "∴": r"\therefore ",
        "∵": r"\because ",
        "∑": r"\sum ",
        "×": r"\times ",
        "⋅": r"\cdot ",
        "⩽": r"\leq ",
        "≤": r"\leq ",
        "⩾": r"\geq ",
        "≥": r"\geq ",
        "∈": r"\in ",
        "≠": r"\ne ",
        "∞": r"\infty ",
        "⇒": r"\Longrightarrow ",
        "⇔": r"\Longleftrightarrow ",
        "…": r"\ldots ",
        "，": r",\quad ",
        "。": ".",
        "（": "(",
        "）": ")",
    }
    for old, new in unicode_math.items():
        latex = latex.replace(old, new)
    latex = re.sub(
        r"\\(display|text|script|scriptscript)style(?=[A-Za-z0-9])",
        r"\\\1style ",
        latex,
    )
    latex = re.sub(r"\\mathrm\{(sin|cos|tan|ln)\}", lambda m: rf"\{m.group(1)}", latex)
    left_count = len(re.findall(r"\\left\b", latex))
    right_count = len(re.findall(r"\\right\b", latex))
    if left_count > right_count:
        latex += r"\right." * (left_count - right_count)
    elif right_count > left_count:
        latex = r"\left." * (right_count - left_count) + latex

    balance = 0
    cleaned = []
    for index, character in enumerate(latex):
        escaped = index > 0 and latex[index - 1] == "\\"
        if character == "{" and not escaped:
            balance += 1
        elif character == "}" and not escaped:
            if balance == 0:
                continue
            balance -= 1
        cleaned.append(character)
    cleaned.extend("}" * balance)
    return "".join(cleaned) or r"\text{公式待校}"


def anomaly_score(latex: str) -> int:
    weights = {
        "mathfrak": 5,
        "mathcal": 4,
        "mathbb": 4,
        "stackrel": 5,
        "underbrace": 5,
        "overbrace": 5,
        "operatorname": 3,
        "nabla": 5,
        "Upsilon": 5,
        "pounds": 5,
        r"\vec": 5,
        r"\Im": 8,
        r"\oplus": 8,
        "sqrtE": 8,
        "object Object": 10,
        "!j!": 10,
        "boldmath": 10,
        r"\cdotn": 10,
        r"\mp": 10,
        r"\Lambdar": 10,
        r"\O_": 8,
        r"\langle": 4,
        r"\begin{array}": 8,
        r"\S": 8,
        r"\(": 20,
        r"\)": 20,
        r"\text{公式缺失}": 20,
    }
    score = sum(latex.count(token) * weight for token, weight in weights.items())
    score += abs(latex.count(r"\left") - latex.count(r"\right")) * 5
    score += latex.count(r"\scriptsize") * 2
    score += max(0, (len(latex) - 300) // 100) * 3
    if re.search(r"\\\d", latex):
        score += 20
    if r"\begin{array}" in latex and len(latex) > 150:
        score += 20
    return score


def plain_text(paragraph: dict) -> str:
    return "".join(part.get("text", "") for part in paragraph["parts"]).strip()


def render_paragraph(
    paragraph: dict,
    formulas: dict,
    source_assets: Path,
    formula_fallbacks: dict[str, str],
) -> str:
    text = plain_text(paragraph)
    for prefix, override in PARAGRAPH_OVERRIDES_BY_PREFIX.items():
        if text.startswith(prefix):
            return override

    image_names = {
        part["name"] for part in paragraph["parts"] if part["type"] == "image"
    }
    for name, override in PARAGRAPH_OVERRIDES_BY_IMAGE.items():
        if name in image_names:
            return override

    output: list[str] = []
    diagram_count = sum(
        part["type"] == "image" and not is_formula(part["name"], source_assets)
        for part in paragraph["parts"]
    )
    for part in paragraph["parts"]:
        if part["type"] == "text":
            output.append(escape_text(part["text"]))
            continue
        name = part["name"]
        if is_formula(name, source_assets):
            if name in RAW_LATEX_OVERRIDES:
                output.append(RAW_LATEX_OVERRIDES[name])
            elif name in formula_fallbacks:
                width = part.get("width_pt") or 120
                height = part.get("height_pt") or 24
                output.append(
                    rf"\DocImage{{{formula_fallbacks[name]}}}{{{width:.2f}}}{{{height:.2f}}}"
                )
            else:
                latex = FORMULA_OVERRIDES.get(
                    name,
                    clean_formula(
                        formulas.get(name, {}).get("latex", r"\text{公式待校}")
                    ),
                )
                output.append(rf"\FormulaOCR{{{name}}}{{{latex}}}")
        else:
            width = part.get("width_pt") or 180
            height = part.get("height_pt") or 120
            if diagram_count >= 2:
                width = min(width, 190)
            output.append(rf"\DocImage{{{name}}}{{{width:.2f}}}{{{height:.2f}}}")
    return "".join(output).strip()


def heading_command(text: str, rendered: str) -> str | None:
    safe_text = escape_text(text).replace(
        "公式法（利用间的关系求通项）",
        r"公式法（利用 $S_n$ 与 $a_n$ 的关系求通项）",
    )
    if re.match(r"^[一二三四五六七八九十]+、", text):
        title = re.sub(r"^[一二三四五六七八九十]+、", "", safe_text, count=1)
        return rf"\par\bigskip\noindent{{\zihao{{3}}\bfseries {title}}}"
    if text in MAJOR_HEADINGS:
        return rf"\par\bigskip\noindent{{\zihao{{3}}\bfseries {safe_text}}}"
    if re.match(r"^\d+[、.]\s*(?:累加法|累乘法|构造法|取倒法|取对数|其他|裂项求和|错位相减)", text):
        title = re.sub(r"^\d+[、.]\s*", "", safe_text, count=1)
        return rf"\par\medskip\noindent{{\zihao{{4}}\bfseries {title}}}"
    if re.match(r"^性质\d+", text):
        return rf"\par\medskip\noindent\textbf{{{safe_text}}}"
    return None


def is_question_start(text: str) -> bool:
    return bool(
        re.match(
            r"^(?:"
            r"例\s*\d+"
            r"|P\s*\d+"
            r"|（多选）\s*\d+"
            r"|(?:选择|填空|解答)题\s*\d+"
            r"|\d+[．.]\s*(?:（|\(|已知|设|数列|在|若|一个|某|观察|求|证明)"
            r")",
            text,
        )
    )


def answer_space_height(question_text: str, subquestion_count: int) -> str:
    if re.search(r"（\s*　\s*）|（\s*）|\([ ]*\)|选择|填空", question_text):
        return "1.2cm"
    if subquestion_count >= 3:
        return "6.0cm"
    if subquestion_count == 2:
        return "4.8cm"
    if subquestion_count == 1:
        return "3.5cm"
    return "2.5cm"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("questions", type=Path)
    parser.add_argument("answers", type=Path)
    parser.add_argument("formula_json", type=Path)
    parser.add_argument("source_assets", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("final_assets", type=Path)
    parser.add_argument("--alignment-report", type=Path)
    parser.add_argument(
        "--deduplicate-types",
        action="store_true",
        help="remove parallel exercises that use the same core solution pattern",
    )
    args = parser.parse_args()

    questions = json.loads(args.questions.read_text(encoding="utf-8"))["paragraphs"]
    answers = json.loads(args.answers.read_text(encoding="utf-8"))["paragraphs"]
    answers = split_embedded_answers(answers)
    formulas = json.loads(args.formula_json.read_text(encoding="utf-8"))["formulas"]
    visible = align_visible(questions, answers)
    args.final_assets.mkdir(parents=True, exist_ok=True)
    formula_fallbacks: dict[str, str] = {}
    for name, entry in formulas.items():
        if name in FORMULA_OVERRIDES:
            continue
        if anomaly_score(entry.get("latex", "")) < 8:
            continue
        raster = Path(entry.get("raster", ""))
        if not raster.is_file():
            continue
        destination_name = f"formula-{Path(name).stem}.png"
        shutil.copy2(raster, args.final_assets / destination_name)
        formula_fallbacks[name] = destination_name

    lines = [
        "% 由“数列总结.doc”和“数列总结答案.doc”对齐整理生成。",
        "% 题目与答案共用本文件；答案段由 \\ifshowanswers 控制。",
        "",
    ]
    answer_open = False
    active_question = ""
    active_subquestions = 0
    copied: set[str] = set()
    skip_question = False
    skipped_answer_seen = False
    for position, paragraph in enumerate(answers):
        is_visible = position in visible
        text = plain_text(paragraph)
        if args.deduplicate_types:
            # A question block consists of its visible stem/subquestions followed
            # by hidden answer paragraphs. The first visible paragraph after the
            # answer starts normal rendering again.
            if skip_question and not is_visible:
                skipped_answer_seen = True
            elif skip_question and is_visible and skipped_answer_seen:
                skip_question = False
                skipped_answer_seen = False
            if is_visible and is_question_start(text):
                skip_question = paragraph["index"] in DEDUPLICATED_QUESTION_STARTS
                skipped_answer_seen = False
            if skip_question:
                continue
        if any(paragraph["index"] in excluded for excluded in EXCLUDED_ANSWER_RANGES):
            continue
        if text.startswith("声明：试题解析著作权"):
            continue
        if is_visible and answer_open:
            lines.extend([r"\par\endgroup\fi", ""])
            answer_open = False
        elif not is_visible and not answer_open:
            if active_question:
                height = answer_space_height(active_question, active_subquestions)
                lines.append(rf"\QuestionSpace{{{height}}}")
                active_question = ""
                active_subquestions = 0
            lines.extend(
                [
                    r"\ifshowanswers",
                    r"\par\begingroup\color{solutioncolor}\noindent\textbf{解答}\quad",
                ]
            )
            answer_open = True

        rendered = render_paragraph(
            paragraph, formulas, args.source_assets, formula_fallbacks
        )
        if not rendered:
            continue
        if is_visible and is_question_start(text):
            active_question = text
            active_subquestions = 0
            lines.append(r"\Needspace{6\baselineskip}")
        elif is_visible and active_question and re.match(
            r"^[（(](?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]|\d+)[）)]", text
        ):
            active_subquestions += 1
        heading = heading_command(text, rendered) if is_visible else None
        lines.append((heading or rendered) + r"\par")

        for part in paragraph["parts"]:
            if part["type"] == "image" and not is_formula(part["name"], args.source_assets):
                name = part["name"]
                if name not in copied:
                    shutil.copy2(args.source_assets / name, args.final_assets / name)
                    copied.add(name)

    if answer_open:
        lines.extend([r"\par\endgroup\fi", ""])
    lines.extend(["", TEACHING_SUPPLEMENTS.strip(), ""])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")

    if args.alignment_report:
        unmatched_questions = [
            {
                "paragraph_index": item["index"],
                "text": signature(item),
            }
            for item in questions
            if signature(item)
            and not any(
                difflib.SequenceMatcher(
                    None, signature(item), signature(answers[index]), autojunk=False
                ).ratio()
                >= 0.62
                for index in visible
            )
        ]
        args.alignment_report.write_text(
            json.dumps(
                {
                    "question_paragraphs": len(questions),
                    "answer_paragraphs": len(answers),
                    "visible_answer_paragraphs": len(visible),
                    "unmatched_questions": unmatched_questions,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    print(
        f"aligned {len(visible)}/{len(questions)} visible paragraphs; "
        f"copied {len(copied)} diagrams and {len(formula_fallbacks)} OCR fallbacks"
    )


if __name__ == "__main__":
    main()
