#!/usr/bin/env python3
"""Render the curated trigonometry Word collection as exam-zh content."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import struct
from pathlib import Path


SECTIONS = [
    (2, "题型一：周期与参数"),
    (85, "题型二：由图象确定解析式"),
    (184, "题型三：函数图象的识别与判断"),
    (243, "题型四：图象变换"),
    (350, "题型五：单调性"),
    (446, "题型六：值域与最值"),
    (472, "题型七：三角恒等变换"),
    (571, "题型八：对称轴与对称中心"),
    (630, "题型九：零点、交点与图象作法"),
    (677, "题型十：三角函数的实际应用"),
    (689, "题型十一：与数列、导数等知识综合"),
    (712, "题型十二：综合解答题"),
]

# These entries are literal duplicates elsewhere in the source document.
EXCLUDED_DUPLICATES = {350, 418, 451, 521}
EXTRA_STARTS = {446, 451, 455, 459, 614, 696}
HEADING_INDICES = {83, 182, 235, 349, 441, 471, 570, 629, 676, 688, 711}

FORMULA_OVERRIDES = {
    "image64.png": r"\frac13T",
    "image172.png": r"\frac T2",
    "image193.png": r"2,\ -\frac{\pi}{6}",
    "image198.png": r"\frac T2",
    "image207.png": r"\left(x_0+\frac{\pi}{4},-y_0\right)",
    "image208.png": r"x_0+\frac{\pi}{4}-x_0",
    "image241.png": r"\frac7{12}",
    "image246.png": r"\frac23",
    "image250.png": r"\frac23",
    "image251.png": r"\vec a=\left(-\frac{\pi}{6},0\right)",
    "image253.png": r"y=\sin\left(x+\frac{\pi}{6}\right)",
    "image254.png": r"y=\sin\left(x-\frac{\pi}{6}\right)",
    "image255.png": r"y=\sin\left(2x+\frac{\pi}{3}\right)",
    "image256.png": r"y=\sin\left(2x-\frac{\pi}{3}\right)",
    "image257.png": r"\vec a=\left(-\frac{\pi}{6},0\right)",
    "image258.png": r"y=\sin\omega\left(x+\frac{\pi}{6}\right)",
    "image263.png": r"y=\sin\left(x+\frac{\pi}{6}\right)",
    "image264.png": r"y=\sin\left(2x-\frac{\pi}{6}\right)",
    "image265.png": r"y=\cos\left(4x-\frac{\pi}{3}\right)",
    "image266.png": r"y=\cos\left(2x-\frac{\pi}{6}\right)",
    "image268.png": r"\frac{\pi}{12}+\frac{\pi}{6}=\frac{\pi}{4}",
    "image270.png": r"y=\sin2\left(x+\frac{\pi}{6}\right)",
    "image271.png": (
        r"\sin\left(2x+\frac{\pi}{3}\right)"
        r"=\cos\left(-\frac{\pi}{2}+2x+\frac{\pi}{3}\right)"
        r"=\cos\left(2x-\frac{\pi}{6}\right)"
    ),
    "image391.png": r"\frac1{\tan x}",
    "image392.png": (
        r"\sqrt{\left(1-\frac1{\tan x}\right)^2+1}"
        r"+\sqrt{\left(1+\frac1{\tan x}\right)^2+1}"
    ),
    "image405.png": r"\frac{\cos6x}{2^x-2^{-x}}",
    "image410.png": r"\frac{\cos6x}{2^x-2^{-x}}",
    "image411.png": r"\frac{\cos(-6x)}{2^{-x}-2^x}",
    "image412.png": r"y=\sin\left(x+\frac{\pi}{6}\right)",
    "image413.png": r"y=\sin\left(x-\frac{\pi}{3}\right)",
    "image423.png": r"y=\sin\left(x+\frac{\pi}{6}\right)",
    "image424.png": r"y=\sin\left(x-\frac{\pi}{3}\right)",
    "image429.png": r"T=\frac{2\pi}{|a|}",
    "image462.png": r"-\frac{\pi}{4},\ \frac{\pi}{4}",
    "image552.png": r"\frac{k\pi}{2}-\frac{\pi}{8}",
    "image675.png": r"f(x)=\sin\left(2x-\frac{\pi}{4}\right)",
    "image718.png": r"\frac{2n+1}{4}\,T=\frac{\pi}{2}",
    "image719.png": r"\frac{2n+1}{4}\cdot\frac{2\pi}{\omega}=\frac{\pi}{2}",
    "image724.png": r"\frac T2",
    "image739.png": r"\omega=1\Longrightarrow\omega x+\frac{\pi}{4}\in\left[\frac{3\pi}{4},\frac{5\pi}{4}\right]",
    "image742.png": (
        r"\frac{\pi}{2}\omega+\frac{\pi}{4}\geq\frac{\pi}{2},\quad"
        r"\pi\omega+\frac{\pi}{4}\leq\frac{3\pi}{2}"
        r"\Longleftrightarrow\frac12\leq\omega\leq\frac54"
    ),
    "image748.png": r"\frac{\omega\pi}{3}=2k\pi+\frac{\pi}{2}",
    "image755.png": (
        r"-\frac{\pi}{2}+2k\pi"
        r"\leq\frac13x+\frac{\pi}{3}"
        r"\leq\frac{\pi}{2}+2k\pi"
    ),
    "image766.png": r"f\left(\frac{\pi}{2}\right)>f(\pi)",
    "image776.png": r"\sqrt2\sin\left(\omega x+\varphi+\frac{\pi}{4}\right)",
    "image785.png": r"\frac{\pi}{|\omega|}\geq\pi",
    "image803.png": r"\frac a4",
    "image804.png": r"\frac a4\leq\frac12",
    "image887.png": r"\frac65",
    "image891.png": r"\frac65",
    "image944.png": r"\sin\alpha-\cos\alpha=\sqrt2,\quad\alpha\in(0,\pi)",
    "image971.wmf": r"\sin\left(\theta-\frac{\pi}{4}\right)=1",
    "image1206.wmf": (
        r"\begin{cases}"
        r"\varphi=2k\pi+\frac{\pi}{3},\\"
        r"\varphi=m\pi-\frac{2\pi}{3}"
        r"\end{cases}"
    ),
    "image1432.png": r"y_1=\frac1{1-x}",
    "image1436.png": r"\left(\frac72,4\right)",
    "image1436.wmf": r"\left(\frac72,4\right)",
    "image1685.wmf": r"|\varphi|<\frac{\pi}{2},\quad\sin\varphi>0",
}

# Several legacy Equation Editor objects are already blank in the source Word file.
# Restore those short paragraphs from the mathematical context and supplied answers.
PARAGRAPH_OVERRIDES = {
    6: r"（2018•新课标Ⅰ）已知函数 $f(x)=2\cos^2x-\sin^2x+2$，则（　　）",
    7: r"A．$f(x)$ 的最小正周期为 $\pi$，最大值为 $3$",
    8: r"B．$f(x)$ 的最小正周期为 $\pi$，最大值为 $4$",
    9: r"C．$f(x)$ 的最小正周期为 $2\pi$，最大值为 $3$",
    10: r"D．$f(x)$ 的最小正周期为 $2\pi$，最大值为 $4$",
    11: r"解：$f(x)=2\cos^2x-\sin^2x+2(\sin^2x+\cos^2x)=3\cos^2x+1$，",
    12: r"即 $f(x)=\frac32\cos2x+\frac52$，故最小正周期为 $\pi$，最大值为 $4$．故选 B．",
    13: r"",
    34: r"（2017•天津）设函数 $f(x)=2\sin(\omega x+\varphi)$，其中 $\omega>0$，$|\varphi|<\pi$．若 $f(\frac{5\pi}{8})=2$，$f(\frac{11\pi}{8})=0$，且 $f(x)$ 的最小正周期大于 $2\pi$，则（　　）",
    35: r"A．$\omega=\frac23$，$\varphi=\frac{\pi}{12}$\qquad B．$\omega=\frac23$，$\varphi=-\frac{11\pi}{12}$",
    36: r"C．$\omega=\frac13$，$\varphi=-\frac{11\pi}{24}$\qquad D．$\omega=\frac13$，$\varphi=\frac{7\pi}{24}$",
    37: r"解：由两个已知函数值及 $T>2\pi$，可知从最大值点到右侧相邻零点的距离为 $\frac T4=\frac{11\pi}{8}-\frac{5\pi}{8}=\frac{3\pi}{4}$，故 $T=3\pi$，$\omega=\frac23$．再由 $\sin(\frac{5\pi}{12}+\varphi)=1$ 及 $|\varphi|<\pi$，得 $\varphi=\frac{\pi}{12}$．故选 A．",
    38: r"（2016•浙江）设函数 $f(x)=\sin^2x+b\sin x+c$，则 $f(x)$ 的最小正周期（　　）",
    41: r"解：常数 $c$ 只使图象上下平移，故周期与 $c$ 无关．",
    42: r"当 $b=0$ 时，$f(x)=\frac12-\frac12\cos2x+c$，最小正周期为 $\pi$；",
    43: r"当 $b\ne0$ 时，$f(x)=\frac12-\frac12\cos2x+b\sin x+c$，最小正周期为 $2\pi$．因此周期与 $b$ 有关、与 $c$ 无关．故选 B．",
    44: r"",
    48: r"交点对应 $\sin(\omega x+\frac{\pi}{6})=\frac12$．相邻交点的最小距离为 $\frac T3$，故 $\frac T3=\frac{\pi}{3}$，得 $T=\pi$．故选 C．",
    49: r"",
    53: r"解：$f(-x)=\frac{-\sin x}{-\sin x-2\sin\frac{x}{2}}=f(x)$，所以 $f(x)$ 是偶函数；又 $f(x+4\pi)=f(x)$，而 $2\pi$ 不是它的周期，故选 A．",
    54: r"",
    55: r"",
    56: r"（2007•广东）已知简谐运动 $f(x)=2\sin(\frac{\pi}{3}x+\varphi)$（$|\varphi|<\frac{\pi}{2}$）的图象经过点 $(0,1)$，则其最小正周期 $T$ 和初相 $\varphi$ 分别为（　　）",
    57: r"A．$T=6$，$\varphi=\frac{\pi}{6}$\qquad B．$T=6$，$\varphi=\frac{\pi}{3}$\qquad C．$T=6\pi$，$\varphi=\frac{\pi}{6}$\qquad D．$T=6\pi$，$\varphi=\frac{\pi}{3}$",
    58: r"解：由 $f(0)=1$ 得 $2\sin\varphi=1$．结合 $|\varphi|<\frac{\pi}{2}$，得 $\varphi=\frac{\pi}{6}$；又 $T=\frac{2\pi}{\pi/3}=6$．故选 A．",
    59: r"",
    60: r"（2014•北京）设函数 $f(x)=A\sin(\omega x+\varphi)$（$A>0$，$\omega>0$）．若 $f(x)$ 在 $[\frac{\pi}{6},\frac{\pi}{2}]$ 上具有单调性，且 $f(\frac{\pi}{2})=f(\frac{2\pi}{3})=-f(\frac{\pi}{6})$，则 $f(x)$ 的最小正周期为\AnswerBlank{\ensuremath{\pi}}．",
    85: r"（2016•新课标Ⅱ）函数 $y=A\sin(\omega x+\varphi)$ 的部分图象如图所示，则（　　）",
    87: r"A．$y=2\sin(2x-\frac{\pi}{6})$\qquad B．$y=2\sin(2x-\frac{\pi}{3})$\qquad C．$y=2\sin(x+\frac{\pi}{6})$\qquad D．$y=2\sin(x+\frac{\pi}{3})$",
    88: r"解：由图得振幅 $A=2$，且 $\frac T2=\frac{\pi}{3}+\frac{\pi}{6}=\frac{\pi}{2}$，故 $T=\pi$，$\omega=2$．",
    89: r"将图上的最大值点 $(\frac{\pi}{3},2)$ 代入 $y=2\sin(2x+\varphi)$，得 $\frac{2\pi}{3}+\varphi=\frac{\pi}{2}+2k\pi$．取符合图象的相位，得 $\varphi=-\frac{\pi}{6}$．故选 A．",
    93: r"解：由图可知最小水深为 $2$ m，故 $-3+k=2$，得 $k=5$．因此最大水深为 $3+k=8$ m．故选 C．",
    95: r"（2015•新课标Ⅰ）函数 $f(x)=\cos(\omega x+\varphi)$ 的部分图象如图所示，则 $f(x)$ 的单调递减区间为（　　）",
    96: r"A．$(k\pi-\frac14,\,k\pi+\frac34)$\quad B．$(2k\pi-\frac14,\,2k\pi+\frac34)$\quad($k\in\mathbb Z$)",
    97: r"C．$(k-\frac14,\,k+\frac34)$\quad D．$(2k-\frac14,\,2k+\frac34)$\quad($k\in\mathbb Z$)",
    98: r"解：由图得 $T=2$，故 $\omega=\pi$．又图象经过关键点 $(\frac14,0)$，可得 $\varphi=\frac{\pi}{4}$，即 $f(x)=\cos(\pi x+\frac{\pi}{4})$．",
    99: r"令 $2k\pi\leq\pi x+\frac{\pi}{4}\leq2k\pi+\pi$，得 $2k-\frac14\leq x\leq2k+\frac34$．故选 D．",
    100: r"（2013•四川）函数 $f(x)=2\sin(\omega x+\varphi)$（$\omega>0$，$-\frac{\pi}{2}<\varphi<\frac{\pi}{2}$）的部分图象如图所示，则 $\omega,\varphi$ 的值分别是（　　）",
    102: r"A．$2,-\frac{\pi}{3}$\qquad B．$2,-\frac{\pi}{6}$\qquad C．$4,\frac{\pi}{6}$\qquad D．$4,\frac{\pi}{3}$",
    103: r"解：图中 $x=\frac{5\pi}{12}$ 为最大值点，$x=\frac{11\pi}{12}$ 为最小值点，故 $\frac T2=\frac{\pi}{2}$，从而 $T=\pi$，$\omega=2$．再由 $\frac{5\pi}{6}+\varphi=\frac{\pi}{2}+2k\pi$ 及相位范围，得 $\varphi=-\frac{\pi}{3}$．故选 A．",
    107: r"解：由图可见，横坐标相差 $\frac{\pi}{4}$ 的对应点函数值互为相反数，故 $\frac T2=\frac{\pi}{4}$，从而 $T=\frac{\pi}{2}$．",
    108: r"由 $\frac{2\pi}{\omega}=\frac{\pi}{2}$，得 $\omega=4$．故选 B．",
    109: r"（2011•辽宁）已知函数 $f(x)=A\tan(\omega x+\varphi)$（$\omega>0$，$|\varphi|<\frac{\pi}{2}$）的部分图象如图，则 $f(\frac{\pi}{24})=$（　　）",
    111: r"A．$2+\sqrt3$\qquad B．$\sqrt3$\qquad C．$\frac{\sqrt3}{8}$\qquad D．$2-\sqrt3$",
    112: r"解：由图得 $T=2(\frac{3\pi}{8}-\frac{\pi}{8})=\frac{\pi}{2}$，故 $\omega=\frac{\pi}{T}=2$．图象过 $(\frac{3\pi}{8},0)$ 且 $|\varphi|<\frac{\pi}{2}$，得 $\varphi=\frac{\pi}{4}$；又图象过 $(0,1)$，得 $A=1$．因此 $f(x)=\tan(2x+\frac{\pi}{4})$，$f(\frac{\pi}{24})=\tan\frac{\pi}{3}=\sqrt3$．故选 B．",
    119: r"解：由图可知振幅为 $1$、周期为 $\pi$，并可取解析式 $y=\sin(2x+\frac{\pi}{3})=\sin2(x+\frac{\pi}{6})$．",
    120: r"先将 $y=\sin x$ 的图象向左平移 $\frac{\pi}{3}$ 个单位，得到 $y=\sin(x+\frac{\pi}{3})$；再把横坐标缩短为原来的一半，得到 $y=\sin(2x+\frac{\pi}{3})$．故选 A．",
    121: r"",
    122: r"",
    123: r"（2009•辽宁）已知函数 $f(x)=A\cos(\omega x+\varphi)$ 的图象如图所示，$f(\frac{\pi}{2})=-\frac23$，则 $f(0)=$（　　）",
    125: r"A．$-\frac23$\qquad B．$-\frac12$\qquad C．$\frac23$\qquad D．$\frac12$",
    126: r"解：由图得 $T=2(\frac{11\pi}{12}-\frac{7\pi}{12})=\frac{2\pi}{3}$，故 $\omega=3$．由 $f(\frac{\pi}{2})=A\sin\varphi=-\frac23$；又由图中零点 $x=-\frac{\pi}{12}$，得 $A\cos(\varphi-\frac{\pi}{4})=\frac{\sqrt2}{2}(A\cos\varphi+A\sin\varphi)=0$．故 $f(0)=A\cos\varphi=\frac23$，选 C．",
    130: r"解：平移后函数为 $y=\sin\omega(x+\frac{\pi}{6})$．由图中关键点得 $\omega(\frac{7\pi}{12}+\frac{\pi}{6})=\frac{3\pi}{2}$，解得 $\omega=2$．",
    131: r"故解析式为 $y=\sin2(x+\frac{\pi}{6})=\sin(2x+\frac{\pi}{3})$．故选 C．",
    187: r"解：建立以 $O$ 为原点、$OB$ 为 $x$ 轴正方向的坐标系．当 $P$ 在 $BC$ 上时，$0\leq x\leq\frac{\pi}{4}$，$BP=\tan x$，",
    188: r"$PA+PB=\sqrt{4+\tan^2x}+\tan x$，随 $x$ 单调递增．",
    189: r"当 $P$ 在 $CD$ 上时，$\frac{\pi}{4}\leq x\leq\frac{3\pi}{4}$．设 $P=(u,1)$，则 $u=\cot x$，",
    190: r"$PA+PB=\sqrt{(u+1)^2+1}+\sqrt{(u-1)^2+1}$，其图象关于 $x=\frac{\pi}{2}$ 对称，并在 $x=\frac{\pi}{2}$ 处取得最小值 $2\sqrt2$．",
    191: r"当 $P$ 在 $AD$ 上时，$\frac{3\pi}{4}\leq x\leq\pi$，$PA+PB=\sqrt{4+\tan^2x}-\tan x$．",
    192: r"结合端点值、对称性及各段变化趋势，符合的图象为 B．",
    193: r"",
    194: r"",
    208: r"又当 $x\to0^+$ 时，$y\to+\infty$，可排除 B；当 $x\to+\infty$ 时，$y\to0$，可排除 C．",
    260: r"（2016•北京）将函数 $y=\sin(2x-\frac{\pi}{3})$ 图象上的点 $P(\frac{\pi}{4},t)$ 向左平移 $s$（$s>0$）个单位得到点 $P'$．若 $P'$ 位于 $y=\sin2x$ 的图象上，则（　　）",
    261: r"A．$t=\frac12$，$s$ 的最小值为 $\frac{\pi}{6}$\qquad B．$t=\frac{\sqrt3}{2}$，$s$ 的最小值为 $\frac{\pi}{6}$",
    262: r"C．$t=\frac12$，$s$ 的最小值为 $\frac{\pi}{3}$\qquad D．$t=\frac{\sqrt3}{2}$，$s$ 的最小值为 $\frac{\pi}{3}$",
    263: r"解：$t=\sin(2\cdot\frac{\pi}{4}-\frac{\pi}{3})=\sin\frac{\pi}{6}=\frac12$．平移后 $P'=(\frac{\pi}{4}-s,\frac12)$，故 $\sin(\frac{\pi}{2}-2s)=\frac12$，即 $\cos2s=\frac12$．由 $s>0$ 得最小值为 $\frac{\pi}{6}$．故选 A．",
    265: r"A．$y=2\sin(2x+\frac{\pi}{4})$\qquad B．$y=2\sin(2x+\frac{\pi}{3})$\qquad C．$y=2\sin(2x-\frac{\pi}{4})$\qquad D．$y=2\sin(2x-\frac{\pi}{3})$",
    267: r"解：函数 $y=2\sin(2x+\frac{\pi}{6})$ 的周期为 $T=\pi$，向右平移四分之一个周期，得 $y=2\sin[2(x-\frac{\pi}{4})+\frac{\pi}{6}]=2\sin(2x-\frac{\pi}{3})$．故选 D．",
    269: r"A．向左平移 $\frac{\pi}{3}$ 个单位长度\qquad B．向右平移 $\frac{\pi}{3}$ 个单位长度",
    270: r"C．向上平移 $\frac{\pi}{3}$ 个单位长度\qquad D．向下平移 $\frac{\pi}{3}$ 个单位长度",
    271: r"解：$y=\sin(x+\frac{\pi}{3})$ 由 $y=\sin x$ 的图象向左平移 $\frac{\pi}{3}$ 个单位长度得到．故选 A．",
    273: r"A．向左平移 $\frac{\pi}{3}$ 个单位长度\qquad B．向右平移 $\frac{\pi}{3}$ 个单位长度",
    274: r"C．向左平移 $\frac{\pi}{6}$ 个单位长度\qquad D．向右平移 $\frac{\pi}{6}$ 个单位长度",
    275: r"解：把 $y=\sin 2x$ 的图象向右平移 $\frac{\pi}{6}$ 个单位长度，得 $y=\sin[2(x-\frac{\pi}{6})]=\sin(2x-\frac{\pi}{3})$．故选 D．",
    276: r"（2016•新课标Ⅱ）若将函数 $y=2\sin 2x$ 的图象向左平移 $\frac{\pi}{12}$ 个单位长度，则平移后图象的对称轴为（　　）\par A．$x=\frac{k\pi}{2}-\frac{\pi}{6}$\quad B．$x=\frac{k\pi}{2}+\frac{\pi}{6}$\quad C．$x=\frac{k\pi}{2}-\frac{\pi}{12}$\quad D．$x=\frac{k\pi}{2}+\frac{\pi}{12}$\quad($k\in\mathbb Z$)",
    277: r"解：平移后的函数为 $y=2\sin(2x+\frac{\pi}{6})$．令 $2x+\frac{\pi}{6}=k\pi+\frac{\pi}{2}$，得 $x=\frac{k\pi}{2}+\frac{\pi}{6}$，$k\in\mathbb Z$．",
    278: r"因此对称轴为 $x=\frac{k\pi}{2}+\frac{\pi}{6}$，$k\in\mathbb Z$．故选 B．",
    294: r"A．向右平移 $\frac{\pi}{4}$ 个单位\qquad B．向左平移 $\frac{\pi}{4}$ 个单位",
    295: r"C．向右平移 $\frac{\pi}{12}$ 个单位\qquad D．向左平移 $\frac{\pi}{12}$ 个单位",
    296: r"解：$\sin 3x+\cos 3x=\sqrt2\cos(3x-\frac{\pi}{4})=\sqrt2\cos[3(x-\frac{\pi}{12})]$，故将 $y=\sqrt2\cos 3x$ 的图象向右平移 $\frac{\pi}{12}$ 个单位即可．故选 C．",
    302: r"（2013•山东）函数 $y=\sin(2x+\varphi)$ 的图象沿 $x$ 轴向左平移 $\frac{\pi}{8}$ 个单位后，得到一个偶函数的图象，则 $\varphi$ 的一个可能值为（　　）",
    303: r"A．$\frac{3\pi}{4}$\qquad B．$\frac{\pi}{4}$\qquad C．$0$\qquad D．$-\frac{\pi}{4}$",
    304: r"解：平移后的函数为 $\sin[2(x+\frac{\pi}{8})+\varphi]=\sin(2x+\frac{\pi}{4}+\varphi)$．其为偶函数，故 $\frac{\pi}{4}+\varphi=k\pi+\frac{\pi}{2}$，即 $\varphi=k\pi+\frac{\pi}{4}$．",
    305: r"取 $k=0$，得 $\varphi=\frac{\pi}{4}$．故选 B．",
    318: r"（2009•湖北）函数 $y=\cos(2x+\frac{\pi}{6})-2$ 的图象 $F$ 按向量 $\vec a$ 平移到 $F'$，$F'$ 的函数解析式为 $y=f(x)$．当 $f(x)$ 为奇函数时，向量 $\vec a$ 可以等于（　　）",
    319: r"A．$(\frac{\pi}{6},-2)$\qquad B．$(-\frac{\pi}{6},2)$\qquad C．$(-\frac{\pi}{6},-2)$\qquad D．$(\frac{\pi}{6},2)$",
    320: r"解：将 $y=\cos(2x+\frac{\pi}{6})-2$ 的图象向左平移 $\frac{\pi}{6}$ 个单位，再向上平移 $2$ 个单位，得 $y=\cos(2x+\frac{\pi}{2})=-\sin 2x$．",
    321: r"因此 $\vec a=(-\frac{\pi}{6},2)$．故选 B．",
    322: r"（2014•重庆）将函数 $f(x)=\sin(\omega x+\varphi)$（$\omega>0$，$-\frac{\pi}{2}\leq\varphi<\frac{\pi}{2}$）图象上每一点的横坐标缩短为原来的一半，纵坐标不变，再向右平移 $\frac{\pi}{6}$ 个单位长度得到 $y=\sin x$ 的图象，则 $f(\frac{\pi}{6})=$\AnswerBlank{\ensuremath{\frac{\sqrt2}{2}}}．",
    284: r"（2015•湖南）将 $f(x)=\sin2x$ 的图象向右平移 $\varphi$（$0<\varphi<\frac{\pi}{2}$）个单位后得到 $g(x)$．若对满足 $|f(x_1)-g(x_2)|=2$ 的 $x_1,x_2$，有 $|x_1-x_2|_{\min}=\frac{\pi}{3}$，则 $\varphi=$（　　）\par A．$\frac{5\pi}{12}$\qquad B．$\frac{\pi}{3}$\qquad C．$\frac{\pi}{4}$\qquad D．$\frac{\pi}{6}$",
    285: r"解：$g(x)=\sin(2x-2\varphi)$．等式 $|f(x_1)-g(x_2)|=2$ 要求一个函数取 $1$、另一个取 $-1$．",
    286: r"比较两组极值点可得，在 $0<\varphi<\frac{\pi}{2}$ 内，满足条件的横坐标最小距离为 $\frac{\pi}{2}-\varphi$．",
    287: r"由 $\frac{\pi}{2}-\varphi=\frac{\pi}{3}$，得 $\varphi=\frac{\pi}{6}$．故选 D．",
    288: r"",
    306: r"（2012•天津）将函数 $y=\sin\omega x$（$\omega>0$）的图象向右平移 $\frac{\pi}{4}$ 个单位，所得图象经过点 $(\frac{3\pi}{4},0)$，则 $\omega$ 的最小值是（　　）",
    307: r"A．$\frac13$\qquad B．$1$\qquad C．$\frac32$\qquad D．$2$",
    308: r"解：平移后函数为 $y=\sin[\omega(x-\frac{\pi}{4})]$．代入 $(\frac{3\pi}{4},0)$，得 $\sin\frac{\omega\pi}{2}=0$，即 $\frac{\omega\pi}{2}=k\pi$．故最小正值为 $\omega=2$，选 D．",
    309: r"（2011•大纲版）设 $f(x)=\cos\omega x$（$\omega>0$）．将其图象向右平移 $\frac{\pi}{3}$ 个单位后与原图象重合，则 $\omega$ 的最小值为（　　）",
    311: r"解：$\frac{\pi}{3}$ 必须是函数周期的正整数倍，即 $\frac{\pi}{3}=k\frac{2\pi}{\omega}$，$k\in\mathbb N^*$．故 $\omega=6k$，最小值为 $6$．故选 C．",
    312: r"（2010•辽宁）设 $\omega>0$，函数 $y=\sin(\omega x+\frac{\pi}{3})+2$ 的图象向右平移 $\frac{4\pi}{3}$ 个单位后与原图象重合，则 $\omega$ 的最小值是（　　）",
    314: r"解：平移后的函数为 $y=\sin[\omega(x-\frac{4\pi}{3})+\frac{\pi}{3}]+2$．要与原图象重合，需 $\frac{4\omega\pi}{3}=2k\pi$，",
    315: r"即 $\omega=\frac{3k}{2}$，$k\in\mathbb N^*$．故最小值为 $\frac32$，选 C．",
    316: r"",
    317: r"",
    323: r"解：横坐标缩短为原来的一半后，函数变为 $y=\sin(2\omega x+\varphi)$；再向右平移 $\frac{\pi}{6}$，得到",
    324: r"$y=\sin[2\omega(x-\frac{\pi}{6})+\varphi]=\sin(2\omega x+\varphi-\frac{\omega\pi}{3})$．",
    325: r"该函数与 $y=\sin x$ 相同，故 $2\omega=1$ 且 $\varphi-\frac{\omega\pi}{3}=2k\pi$．由相位范围得 $\omega=\frac12$，$\varphi=\frac{\pi}{6}$．",
    326: r"因此 $f(\frac{\pi}{6})=\sin(\frac{\pi}{12}+\frac{\pi}{6})=\sin\frac{\pi}{4}=\frac{\sqrt2}{2}$．",
    327: r"",
    328: r"",
    329: r"",
    359: r"（2013•天津）函数 $f(x)=\sin(2x-\frac{\pi}{4})$ 在区间 $[0,\frac{\pi}{2}]$ 上的最小值是（　　）",
    360: r"A．$-1$\qquad B．$-\frac{\sqrt2}{2}$\qquad C．$\frac{\sqrt2}{2}$\qquad D．$0$",
    361: r"解：当 $x\in[0,\frac{\pi}{2}]$ 时，$2x-\frac{\pi}{4}\in[-\frac{\pi}{4},\frac{3\pi}{4}]$，故 $f(x)\in[-\frac{\sqrt2}{2},1]$，最小值为 $-\frac{\sqrt2}{2}$．故选 B．",
    362: r"（2018•德阳模拟）函数 $f(x)=\sin(2x+\varphi)$（$|\varphi|<\frac{\pi}{2}$）的图象向左平移 $\frac{\pi}{6}$ 个单位后关于原点对称，则 $f(x)$ 在 $[0,\frac{\pi}{2}]$ 上的最小值为（　　）",
    363: r"A．$-\frac{\sqrt3}{2}$\qquad B．$-\frac12$\qquad C．$\frac{\sqrt3}{2}$\qquad D．$\frac12$",
    364: r"解：平移后的函数为 $y=\sin(2x+\frac{\pi}{3}+\varphi)$．其图象关于原点对称，故 $\frac{\pi}{3}+\varphi=k\pi$．由 $|\varphi|<\frac{\pi}{2}$ 得 $\varphi=-\frac{\pi}{3}$．",
    365: r"于是 $f(x)=\sin(2x-\frac{\pi}{3})$．当 $x\in[0,\frac{\pi}{2}]$ 时，$2x-\frac{\pi}{3}\in[-\frac{\pi}{3},\frac{2\pi}{3}]$，",
    366: r"故 $f(x)$ 的最小值为 $-\frac{\sqrt3}{2}$．故选 A．",
    367: r"（2018•乌鲁木齐一模）已知 $\frac{\pi}{3}$ 为函数 $f(x)=\sin(2x+\varphi)$（$0<\varphi<\frac{\pi}{2}$）的零点，则 $f(x)$ 的单调递增区间是（　　）",
    368: r"A．$[2k\pi-\frac{5\pi}{12},\,2k\pi+\frac{\pi}{12}]$\quad B．$[2k\pi+\frac{\pi}{12},\,2k\pi+\frac{7\pi}{12}]$\quad($k\in\mathbb Z$)",
    369: r"C．$[k\pi-\frac{5\pi}{12},\,k\pi+\frac{\pi}{12}]$\quad D．$[k\pi+\frac{\pi}{12},\,k\pi+\frac{7\pi}{12}]$\quad($k\in\mathbb Z$)",
    370: r"解：由 $f(\frac{\pi}{3})=0$，得 $\sin(\frac{2\pi}{3}+\varphi)=0$．结合 $0<\varphi<\frac{\pi}{2}$，得 $\varphi=\frac{\pi}{3}$，故 $f(x)=\sin(2x+\frac{\pi}{3})$．",
    371: r"令 $-\frac{\pi}{2}+2k\pi\leq 2x+\frac{\pi}{3}\leq\frac{\pi}{2}+2k\pi$，解得 $k\pi-\frac{5\pi}{12}\leq x\leq k\pi+\frac{\pi}{12}$．故选 C．",
    372: r"",
    373: r"",
    374: r"（2018•河北区二模）若函数 $f(x)=\cos\omega x-\sin\omega x$（$\omega>0$）在 $(-\frac{\pi}{2},\frac{\pi}{2})$ 上单调递减，则 $\omega$ 的取值不可能为（　　）",
    375: r"A．$\frac15$\qquad B．$\frac14$\qquad C．$\frac12$\qquad D．$\frac34$",
    376: r"解：$f(x)=\sqrt2\cos(\omega x+\frac{\pi}{4})$．要使它在 $(-\frac{\pi}{2},\frac{\pi}{2})$ 上单调递减，该相位区间必须包含在余弦函数的一个递减区间内．",
    377: r"取递减区间 $(0,\pi)$，由 $-\frac{\omega\pi}{2}+\frac{\pi}{4}\geq0$ 且 $\frac{\omega\pi}{2}+\frac{\pi}{4}\leq\pi$，得 $0<\omega\leq\frac12$．",
    378: r"因此 $\frac34$ 不可能．故选 D．",
    379: r"（2016•新课标Ⅰ）已知函数 $f(x)=\sin(\omega x+\varphi)$（$\omega>0$，$|\varphi|\leq\frac{\pi}{2}$），$x=-\frac{\pi}{4}$ 是 $f(x)$ 的零点，$x=\frac{\pi}{4}$ 是 $y=f(x)$ 图象的对称轴，且 $f(x)$ 在 $(\frac{\pi}{18},\frac{5\pi}{36})$ 上单调，则 $\omega$ 的最大值为（　　）\par A．$11$\qquad B．$9$\qquad C．$7$\qquad D．$5$",
    380: r"解：零点与对称轴之间的距离为最小正周期的奇数个四分之一，故 $\omega$ 为正奇数．又给定单调区间的长度为 $\frac{\pi}{12}$，不超过 $\frac{T}{2}=\frac{\pi}{\omega}$，所以 $\omega\leq12$．",
    381: r"当 $\omega=11$ 时，由 $f(-\frac{\pi}{4})=0$ 及 $|\varphi|\leq\frac{\pi}{2}$ 得 $\varphi=-\frac{\pi}{4}$，函数在给定区间内跨过极大值点，故不单调；",
    382: r"当 $\omega=9$ 时，得 $\varphi=\frac{\pi}{4}$，相位区间为 $(\frac{3\pi}{4},\frac{3\pi}{2})$，函数单调递减．因此 $\omega$ 的最大值为 $9$．故选 B．",
    383: r"",
    384: r"",
    385: r"",
    386: r"（2012•新课标）已知 $\omega>0$，函数 $f(x)=\sin(\omega x+\frac{\pi}{4})$ 在区间 $[\frac{\pi}{2},\pi]$ 上单调递减，则 $\omega$ 的取值范围是（　　）",
    387: r"A．$[\frac12,\frac54]$\qquad B．$[\frac12,\frac34]$\qquad C．$(0,\frac12)$\qquad D．$(0,2]$",
    388: r"解：相位 $\omega x+\frac{\pi}{4}$ 在该区间内应落在同一个正弦函数递减区间中．由",
    389: r"$\frac{\omega\pi}{2}+\frac{\pi}{4}\geq\frac{\pi}{2}$，$\omega\pi+\frac{\pi}{4}\leq\frac{3\pi}{2}$，",
    390: r"解得 $\frac12\leq\omega\leq\frac54$．端点均可取，故选 A．",
    391: r"",
    392: r"（2011•山东）若函数 $f(x)=\sin\omega x$（$\omega>0$）在 $[0,\frac{\pi}{3}]$ 上单调递增，在 $[\frac{\pi}{3},\frac{\pi}{2}]$ 上单调递减，则 $\omega=$（　　）",
    393: r"A．$\frac23$\qquad B．$\frac32$\qquad C．$2$\qquad D．$3$",
    394: r"解：由题意，$x=\frac{\pi}{3}$ 是函数的极大值点，故 $\frac{\omega\pi}{3}=2k\pi+\frac{\pi}{2}$．结合选项与两个区间上的单调性，得 $k=0$，$\omega=\frac32$．故选 B．",
    395: r"（2011•天津）已知函数 $f(x)=2\sin(\omega x+\varphi)$，其中 $\omega>0$，$-\pi<\varphi\leq\pi$．若 $f(x)$ 的最小正周期为 $6\pi$，且当 $x=\frac{\pi}{2}$ 时取得最大值，则（　　）",
    396: r"A．$f(x)$ 在 $[-2\pi,0]$ 上是增函数\qquad B．$f(x)$ 在 $[-3\pi,-\pi]$ 上是增函数",
    397: r"C．$f(x)$ 在 $[3\pi,5\pi]$ 上是减函数\qquad D．$f(x)$ 在 $[4\pi,6\pi]$ 上是减函数",
    398: r"解：由 $T=6\pi$ 得 $\omega=\frac13$．再由 $x=\frac{\pi}{2}$ 时取得最大值，得 $\frac{\pi}{6}+\varphi=\frac{\pi}{2}+2k\pi$；结合 $-\pi<\varphi\leq\pi$，得 $\varphi=\frac{\pi}{3}$．",
    399: r"故 $f(x)=2\sin(\frac{x}{3}+\frac{\pi}{3})$，其单调递增区间为 $[6k\pi-\frac{5\pi}{2},\,6k\pi+\frac{\pi}{2}]$，单调递减区间为 $[6k\pi+\frac{\pi}{2},\,6k\pi+\frac{7\pi}{2}]$．故选 A．",
    400: r"",
    401: r"（2011•安徽）已知函数 $f(x)=\sin(2x+\varphi)$．若 $f(x)\leq|f(\frac{\pi}{6})|$ 对 $x\in\mathbb R$ 恒成立，且 $f(\frac{\pi}{2})>f(\pi)$，则 $f(x)$ 的单调递增区间是（　　）",
    402: r"A．$[k\pi-\frac{\pi}{3},\,k\pi+\frac{\pi}{6}]$\quad B．$[k\pi,\,k\pi+\frac{\pi}{2}]$\quad($k\in\mathbb Z$)",
    403: r"C．$[k\pi+\frac{\pi}{6},\,k\pi+\frac{2\pi}{3}]$\quad D．$[k\pi-\frac{\pi}{2},\,k\pi]$\quad($k\in\mathbb Z$)",
    404: r"解：恒等式要求 $|f(\frac{\pi}{6})|=1$，故 $\sin(\frac{\pi}{3}+\varphi)=\pm1$，即 $\varphi=\frac{\pi}{6}+k\pi$．",
    405: r"又 $f(\frac{\pi}{2})=-\sin\varphi>f(\pi)=\sin\varphi$，故 $\sin\varphi<0$，可取 $\varphi=-\frac{5\pi}{6}$．令 $-\frac{\pi}{2}+2k\pi\leq2x-\frac{5\pi}{6}\leq\frac{\pi}{2}+2k\pi$，",
    406: r"解得 $x\in[k\pi+\frac{\pi}{6},\,k\pi+\frac{2\pi}{3}]$，$k\in\mathbb Z$．故选 C．",
    407: r"（2011•新课标）设函数 $f(x)=\sin(\omega x+\varphi)+\cos(\omega x+\varphi)$（$\omega>0$，$|\varphi|<\frac{\pi}{2}$）的最小正周期为 $\pi$，且 $f(-x)=f(x)$，则（　　）",
    408: r"A．$f(x)$ 在 $(0,\frac{\pi}{2})$ 上单调递减\qquad B．$f(x)$ 在 $(\frac{\pi}{4},\frac{3\pi}{4})$ 上单调递减",
    409: r"C．$f(x)$ 在 $(0,\frac{\pi}{2})$ 上单调递增\qquad D．$f(x)$ 在 $(\frac{\pi}{4},\frac{3\pi}{4})$ 上单调递增",
    410: r"解：$f(x)=\sqrt2\sin(\omega x+\varphi+\frac{\pi}{4})$．由最小正周期为 $\pi$，得 $\omega=2$．",
    411: r"又 $f(x)$ 为偶函数，故 $\varphi+\frac{\pi}{4}=\frac{\pi}{2}+k\pi$．由 $|\varphi|<\frac{\pi}{2}$ 得 $\varphi=\frac{\pi}{4}$，于是 $f(x)=\sqrt2\cos2x$．",
    412: r"当 $x\in(0,\frac{\pi}{2})$ 时，$2x\in(0,\pi)$，故 $f(x)$ 单调递减．故选 A．",
    413: r"",
    414: r"（2005•黑龙江）已知函数 $y=\tan\omega x$ 在 $(-\frac{\pi}{2},\frac{\pi}{2})$ 上是减函数，则（　　）",
    416: r"解：函数单调递减要求 $\omega<0$；给定区间内不能出现正切函数的间断点，故 $\frac{\pi}{|\omega|}\geq\pi$，即 $|\omega|\leq1$．因此 $-1\leq\omega<0$．故选 B．",
    417: r"",
    420: r"（2014•大纲版）若函数 $f(x)=\cos2x+a\sin x$ 在 $(\frac{\pi}{6},\frac{\pi}{2})$ 上是减函数，则 $a$ 的取值范围是\AnswerBlank{\ensuremath{(-\infty,2]}}．",
    421: r"解：令 $t=\sin x$，则 $t\in(\frac12,1)$，且 $f(x)=-2t^2+at+1$．",
    422: r"由于 $t$ 随 $x$ 递增，原函数递减等价于二次函数在 $(\frac12,1)$ 上递减．其对称轴为 $t=\frac a4$，故 $\frac a4\leq\frac12$，即 $a\leq2$．",
    423: r"所以 $a$ 的取值范围是 $(-\infty,2]$．",
    424: r"（2010•福建）已知函数 $f(x)=3\sin(\omega x-\frac{\pi}{6})$（$\omega>0$）和 $g(x)=2\cos(2x+\varphi)+1$ 的图象的对称轴完全相同．若 $x\in[0,\frac{\pi}{2}]$，则 $f(x)$ 的取值范围是\AnswerBlank{\ensuremath{[-\frac32,3]}}．",
    425: r"解：两函数图象的对称轴完全相同，故 $\omega=2$．于是 $f(x)=3\sin(2x-\frac{\pi}{6})$．",
    426: r"当 $x\in[0,\frac{\pi}{2}]$ 时，$2x-\frac{\pi}{6}\in[-\frac{\pi}{6},\frac{5\pi}{6}]$，故 $f(x)\in[-\frac32,3]$．",
    446: r"函数 $f(x)=\frac15\sin(x+\frac{\pi}{3})+\cos(x-\frac{\pi}{6})$ 的最大值为（　　）",
    447: r"A．$\frac65$\qquad B．$1$\qquad C．$\frac35$\qquad D．$\frac15$",
    448: r"解：由 $\cos(x-\frac{\pi}{6})=\sin(x+\frac{\pi}{3})$，得",
    449: r"$f(x)=\frac65\sin(x+\frac{\pi}{3})\leq\frac65$，且等号可以取得．故选 A．",
    450: r"",
    455: r"若函数 $f(x)=(1+\sqrt3\tan x)\cos x$，$0\leq x<\frac{\pi}{2}$，则 $f(x)$ 的最大值是（　　）",
    457: r"解：$f(x)=\cos x+\sqrt3\sin x=2\sin(x+\frac{\pi}{6})$．",
    458: r"当 $0\leq x<\frac{\pi}{2}$ 时，$\frac{\pi}{6}\leq x+\frac{\pi}{6}<\frac{2\pi}{3}$，故最大值为 $2$．故选 B．",
    459: r"函数 $y=2\sin(\frac{\pi}{3}-x)-\cos(\frac{\pi}{6}+x)$（$x\in\mathbb R$）的最小值等于（　　）",
    461: r"解：因为 $\frac{\pi}{3}-x=\frac{\pi}{2}-(\frac{\pi}{6}+x)$，所以",
    462: r"$y=2\cos(\frac{\pi}{6}+x)-\cos(\frac{\pi}{6}+x)=\cos(\frac{\pi}{6}+x)$，最小值为 $-1$．故选 D．",
    480: r"（2009•辽宁）已知 $\tan\theta=2$，则 $\sin^2\theta+\sin\theta\cos\theta-2\cos^2\theta=$（　　）",
    481: r"A．$-\frac45$\qquad B．$\frac45$\qquad C．$-\frac34$\qquad D．$\frac34$",
    482: r"解：将原式同除以 $\cos^2\theta$，得 $\frac{\tan^2\theta+\tan\theta-2}{\tan^2\theta+1}=\frac{4+2-2}{4+1}=\frac45$．故选 D．",
    483: r"",
    737: r"$\sin2\alpha=2\cdot\frac{\sqrt3}{3}\cdot\frac{\sqrt6}{3}=\frac{2\sqrt2}{3}$，$\cos2\alpha=1-2(\frac{\sqrt3}{3})^2=\frac13$．",
}


def plain_text(paragraph: dict) -> str:
    return "".join(part.get("text", "") for part in paragraph["parts"]).strip()


def is_question_start(paragraph: dict) -> bool:
    index = paragraph["index"]
    if index in EXTRA_STARTS:
        return True
    text = plain_text(paragraph)
    if not re.match(r"^\s*(?:（多选）)?\d+\s*(?:[．.]|(?=（))", text):
        return False
    return bool(re.search(r"（(?:\d+分）)?（?(?:19|20)\d{2}", text[:45]))


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    return struct.unpack(">II", header[16:24])


def is_formula(name: str, assets: Path) -> bool:
    if name.lower().endswith(".wmf"):
        return True
    _, height = png_size(assets / name)
    return height < 78


def escape_text(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "#": r"\#",
        "_": r"\_",
        "$": r"\$",
        "^": r"\textasciicircum{}",
        "﹣": "-",
        "═": "=",
        "\t": r"\qquad{}",
        "\n": r"\par{}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    math_symbols = {
        "π": r"\ensuremath{\pi}",
        "ω": r"\ensuremath{\omega}",
        "φ": r"\ensuremath{\varphi}",
        "α": r"\ensuremath{\alpha}",
        "β": r"\ensuremath{\beta}",
        "θ": r"\ensuremath{\theta}",
        "λ": r"\ensuremath{\lambda}",
        "Δ": r"\ensuremath{\Delta}",
        "∵": r"\ensuremath{\because}",
        "∴": r"\ensuremath{\therefore}",
        "≠": r"\ensuremath{\ne}",
        "≤": r"\ensuremath{\le}",
        "≥": r"\ensuremath{\ge}",
        "⇒": r"\ensuremath{\Longrightarrow}",
        "⇔": r"\ensuremath{\Longleftrightarrow}",
        "∈": r"\ensuremath{\in}",
        "∞": r"\ensuremath{\infty}",
        "×": r"\ensuremath{\times}",
        "△": r"\ensuremath{\triangle}",
        "∠": r"\ensuremath{\angle}",
        "′": r"\ensuremath{'}",
    }
    for old, new in math_symbols.items():
        text = text.replace(old, new)
    text = re.sub(r"　([^　\n]{1,12})　", r"\\AnswerBlank{\1}", text)
    return text


def clean_formula(latex: str) -> str:
    latex = latex.strip()
    latex = re.sub(r"^\${1,2}|\${1,2}$", "", latex).strip()
    latex = re.sub(r"^\\\[|\\\]$", "", latex)
    latex = re.sub(r"\\sqrt\[\s*\]", r"\\sqrt", latex)
    latex = latex.replace(r"\lt", "<").replace(r"\gt", ">")
    substitutions = {
        r"\mathbb{T}": r"\pi",
        r"\mathrm{T}": r"\pi",
        r"\mathcal{T}": r"\pi",
        r"\mathbb{Z}": "2",
        r"\mathrm{Z}": "2",
        r"\mathbb{G}": "6",
        r"\mathrm{G}": "6",
        r"\boldsymbol{x}": "x",
        r"{\boldsymbol{x}}": "x",
        r"\boldsymbol{\omega}": r"\omega",
        r"{\boldsymbol{\omega}}": r"\omega",
        r"\boldsymbol{B}": "B",
        r"{\boldsymbol{C}}": "C",
        r"\mathrm{sin}": r"\sin",
        r"\mathrm{cos}": r"\cos",
        r"\mathrm{tan}": r"\tan",
        r"\Phi": r"\varphi",
    }
    for old, new in substitutions.items():
        latex = latex.replace(old, new)
    unicode_math = {
        "π": r"\pi ",
        "ω": r"\omega ",
        "φ": r"\varphi ",
        "α": r"\alpha ",
        "β": r"\beta ",
        "θ": r"\theta ",
        "λ": r"\lambda ",
        "⋅": r"\cdot ",
        "×": r"\times ",
        "≤": r"\leq ",
        "≥": r"\geq ",
        "≠": r"\ne ",
        "∈": r"\in ",
        "∞": r"\infty ",
        "⇒": r"\Longrightarrow ",
        "⇔": r"\Longleftrightarrow ",
        "⩽": r"\leq ",
        "⩾": r"\geq ",
        "⊆": r"\subseteq ",
        "∵": r"\because ",
        "∴": r"\therefore ",
        "，": r",\quad ",
        "。": ".",
        "═": "=",
        "（": "(",
        "）": ")",
    }
    for old, new in unicode_math.items():
        latex = latex.replace(old, new)
    latex = re.sub(
        r"(?<!\\)(sin|cos|tan|cot|sec|csc|ln|log|max|min)(?=[A-Za-z0-9({\\]|\b)",
        lambda match: rf"\{match.group(1)}",
        latex,
    )
    latex = re.sub(r"\\frac\{1\}\{Z\}", r"\\frac{1}{2}", latex)
    latex = re.sub(r"(?i)s\s+i\s+n", r"\\sin", latex)
    latex = re.sub(r"(?i)c\s+o\s+s", r"\\cos", latex)
    latex = re.sub(
        r"\\(?:mathrm|operatorname)\{(sin|cos|tan)x\}",
        lambda match: rf"\{match.group(1)} x",
        latex,
    )
    latex = re.sub(r"\\(sin|cos|tan)x\b", lambda match: rf"\{match.group(1)} x", latex)
    latex = re.sub(
        r"\\(sin|cos|tan)([A-Za-z])",
        lambda match: rf"\{match.group(1)} {match.group(2)}",
        latex,
    )
    latex = latex.replace(r"\mathbf{\pi}", r"\pi").replace(r"\mathbf{G}", "6")
    latex = latex.replace(r"\d t", r"\mathrm{d}t")
    latex = latex.replace(r"\left|\left.", r"\left|")
    latex = latex.replace(r"\left[", "[").replace(r"\right]", "]")
    latex = latex.replace(r"\right.", "").replace(r"\lbrack", "[").replace(r"\rfloor", "]")
    missing_set_closers = max(0, latex.count(r"\{") - latex.count(r"\}"))
    latex += r"\}" * missing_set_closers
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


def strip_number(text: str) -> str:
    return re.sub(r"^\s*(?:（多选）)?\d+\s*[．.]?", "", text, count=1)


def render_paragraph(
    paragraph: dict,
    formulas: dict,
    source_assets: Path,
    stem: bool,
    first: bool,
) -> str:
    if paragraph["index"] in PARAGRAPH_OVERRIDES:
        return PARAGRAPH_OVERRIDES[paragraph["index"]]
    parts = paragraph["parts"]
    diagram_count = sum(
        part["type"] == "image" and not is_formula(part["name"], source_assets)
        for part in parts
    )
    output = []
    for position, part in enumerate(parts):
        if part["type"] == "text":
            text = strip_number(part["text"]) if first and position == 0 else part["text"]
            output.append(escape_text(text))
            continue

        name = part["name"]
        if is_formula(name, source_assets):
            entry = formulas.get(name)
            latex = FORMULA_OVERRIDES.get(
                name,
                clean_formula(entry["latex"] if entry else r"\text{公式待校}"),
            )
            previous = parts[position - 1].get("text", "") if position else ""
            following = parts[position + 1].get("text", "") if position + 1 < len(parts) else ""
            answer_image = stem and previous.endswith("　") and following.startswith("　")
            rendered = rf"\FormulaOCR{{{name}}}{{{latex}}}"
            output.append(rf"\AnswerBlank{{{rendered}}}" if answer_image else rendered)
        else:
            width = part.get("width_pt") or 180
            height = part.get("height_pt") or 120
            if diagram_count >= 4:
                width = min(width, 70)
            output.append(rf"\DocImage{{{name}}}{{{width:.2f}}}{{{height:.2f}}}")
    rendered = "".join(output).strip()
    rendered = rendered.replace("【解答】", "").replace("【分析】", "")
    return rendered


def summary() -> str:
    return r"""
\section{核心知识与方法梳理}

\subsection{函数模型与周期}
对 $y=A\sin(\omega x+\varphi)+b$ 与 $y=A\cos(\omega x+\varphi)+b$，振幅为
$|A|$，最小正周期为 $T=\frac{2\pi}{|\omega|}$；对
$y=A\tan(\omega x+\varphi)$，最小正周期为 $T=\frac{\pi}{|\omega|}$。
求周期时先化为同名、同角的一个三角函数，并特别注意绝对值可能使周期减半。

\subsection{图象与变换}
由 $y=f(x)$ 得到 $y=f(\omega x+\varphi)$ 时，横向变换应在自变量整体上进行：
先把横坐标缩短为原来的 $\frac1{|\omega|}$，再按相位确定平移量；也可以先平移，
但两种顺序对应的平移长度不同。由图象求解析式时，依次确定 $A$、$b$、$T$、
$\omega$，最后利用一个关键点确定 $\varphi$。

\subsection{单调性、对称性与零点}
把 $\omega x+\varphi$ 看成整体，代入基本函数的单调区间、对称轴、对称中心或零点通式，
再解关于 $x$ 的不等式或方程。处理给定区间内的零点、极值点个数时，五点作图法往往比
直接罗列通式更直观；涉及参数范围时，应同时检查端点是否取到。

\subsection{恒等变换与值域}
常用目标是把式子化为 $A\sin(\omega x+\varphi)+b$，或令
$t=\sin x$、$t=\cos x$ 转化为带有限制区间的二次函数。齐次分式可同除以
$\cos^2\alpha$ 或 $\sin^2\alpha$，转化为关于 $\tan\alpha$ 的有理式；
已知角的象限时，开方后必须结合符号取舍。
""".strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("structure", type=Path)
    parser.add_argument("formula_json", type=Path)
    parser.add_argument("source_assets", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("final_assets", type=Path)
    args = parser.parse_args()

    paragraphs = json.loads(args.structure.read_text(encoding="utf-8"))["paragraphs"]
    formulas = json.loads(args.formula_json.read_text(encoding="utf-8"))["formulas"]
    starts = [position for position, paragraph in enumerate(paragraphs) if is_question_start(paragraph)]
    args.final_assets.mkdir(parents=True, exist_ok=True)

    lines = [
        "% 由“8.专题八三角函数.doc”整理生成。",
        "% 公式经本地 pix2tex 初识别，并保留原图编号以便复核。",
        "",
        summary(),
        "",
    ]
    current_section = None
    included = 0
    copied_assets: set[str] = set()
    boundaries = starts + [len(paragraphs)]
    for ordinal, position in enumerate(starts):
        source_index = paragraphs[position]["index"]
        if source_index in EXCLUDED_DUPLICATES:
            continue
        section = max((name for start, name in SECTIONS if source_index >= start), default=SECTIONS[0][1])
        if section != current_section:
            lines.extend([rf"\subsection{{{section}}}", ""])
            current_section = section

        end = boundaries[ordinal + 1]
        for candidate in range(position + 1, end):
            if paragraphs[candidate]["index"] in HEADING_INDICES:
                end = candidate
                break
        group = paragraphs[position:end]
        solution_at = next(
            (
                i
                for i, paragraph in enumerate(group)
                if "【解答】" in plain_text(paragraph) or plain_text(paragraph).startswith("解：")
            ),
            len(group),
        )
        stem, solution = group[:solution_at], group[solution_at:]
        lines.append("\\begin{question}")
        for i, paragraph in enumerate(stem):
            rendered = render_paragraph(paragraph, formulas, args.source_assets, True, i == 0)
            if rendered:
                lines.append(rendered + r"\par")
        lines.append("\\begin{solution}")
        for paragraph in solution:
            rendered = render_paragraph(paragraph, formulas, args.source_assets, False, False)
            if rendered:
                lines.append(rendered + r"\par")
        lines.extend(["\\end{solution}", "\\end{question}", ""])
        included += 1

        for paragraph in group:
            for part in paragraph["parts"]:
                if part["type"] == "image" and not is_formula(part["name"], args.source_assets):
                    name = part["name"]
                    if name not in copied_assets:
                        shutil.copy2(args.source_assets / name, args.final_assets / name)
                        copied_assets.add(name)

    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"rendered {included} questions; copied {len(copied_assets)} diagram assets")


if __name__ == "__main__":
    main()
