#!/usr/bin/env python3
"""Select the cleaner result from two pix2tex OCR passes."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


OVERRIDES = {
    "image4.png": r"3\cdot\frac{\cos 2x+1}{2}+1",
    "image5.png": r"\frac{3}{2}\cos 2x+\frac{5}{2}",
    "image14.png": r"\frac{1}{2}\cdot\frac{2\pi}{1}",
    "image17.png": r"\frac{\tan x}{1+\tan^2 x}",
    "image20.png": r"\frac{\tan x}{1+\tan^2 x}",
    "image21.png": r"\frac{\sin x\cos x}{\cos^2 x+\sin^2 x}",
    "image24.png": r"f(x)=(1+\sqrt{3}\tan x)\cos x",
    "image31.png": r"\frac{2}{3}",
    "image33.png": r"\frac{11\pi}{12}",
    "image34.png": r"\frac{1}{3}",
    "image36.png": r"\frac{1}{3}",
    "image37.png": r"\frac{7\pi}{24}",
    "image38.png": r"\frac{2\pi}{\omega}",
    "image39.png": r">2\pi",
    "image42.png": r"\frac{T}{4}=\frac{11\pi}{8}-\frac{5\pi}{8}=\frac{3\pi}{4}",
    "image45.png": r"\frac{2}{3}",
    "image47.png": r"2\sin\left(\frac{2}{3}\cdot\frac{5\pi}{8}+\varphi\right)=2",
    "image65.png": r"f(x)=\frac{\sin x}{\sin x+2\sin\frac{x}{2}}",
    "image67.png": r"f(x)=2\sin\left(\frac{\pi}{3}x+\varphi\right)\quad\left(|\varphi|<\frac{\pi}{2}\right)",
    "image77.png": r"\frac{\frac{\pi}{2}+\frac{2\pi}{3}}{2}=\frac{7\pi}{12}",
    "image78.png": r"\frac{7\pi}{12}-\frac{\pi}{2}=\frac{\pi}{12}",
    "image82.png": r"\frac{\pi}{2}-\frac{\pi}{6}=\frac{\pi}{3}",
    "image83.png": r"\frac{1}{2}",
    "image85.png": r"\frac{7\pi}{12}-\frac{\pi}{3}",
    "image86.png": r"\frac{T}{4}",
    "image143.wmf": "T",
    "image213.png": r"f\left(\frac{\pi}{24}\right)",
    "image232.png": r"\frac{1}{2}",
    "image237.png": r"\frac{2}{3}",
    "image277.wmf": r"\sin\pi x-x",
    "image322.wmf": "n",
    "image338.wmf": "A",
    "image339.wmf": "B",
    "image435.png": r"\begin{aligned}y&=\tan x+\sin x-|\tan x-\sin x|\\&=\begin{cases}2\tan x,&\tan x<\sin x,\ x\in(\frac{\pi}{2},\pi),\\2\sin x,&\tan x\ge\sin x,\ x\in[\pi,\frac{3\pi}{2})\end{cases}\end{aligned}",
    "image460.png": r"\frac{\pi}{5}",
    "image524.png": r"\frac{\pi}{6}",
    "image545.png": r"\frac{\pi}{8}",
    "image576.png": r"\frac{2}{3}",
    "image489.png": r"\frac{\pi}{6}",
    "image490.png": r"\frac{1}{4}",
    "image608.wmf": "x",
    "image611.wmf": "x",
    "image615.wmf": "x",
    "image619.wmf": "x",
    "image745.png": r"\frac{2}{3}",
    "image768.png": r"\left[k\pi+\frac{\pi}{6},\ k\pi+\frac{2\pi}{3}\right]\quad(k\in\mathbb{Z})",
    "image805.png": r"f(x)=3\sin\left(\omega x-\frac{\pi}{6}\right)\quad(\omega>0)",
    "image812.wmf": "T",
    "image826.wmf": r"\frac{2\pi}{3}\right]",
    "image828.wmf": r"1\right]",
    "image846.wmf": r"\frac{2\pi}{3}\right]",
    "image848.wmf": r"\frac{2\pi}{3}\right]",
    "image920.wmf": r"\frac{2\pi}{3}\right]",
    "image901.png": r"f(x)=(1+\sqrt{3}\tan x)\cos x,\quad 0\leq x<\frac{\pi}{2}",
    "image925.png": r"\tan\alpha=\frac{1}{2}",
    "image926.png": r"\frac{(\sin\alpha+\cos\alpha)^2}{\cos 2\alpha}",
    "image927.png": r"\frac{(\sin\alpha+\cos\alpha)^2}{\cos 2\alpha}=\frac{(\sin\alpha+\cos\alpha)^2}{(\sin\alpha+\cos\alpha)(\cos\alpha-\sin\alpha)}=\frac{\sin\alpha+\cos\alpha}{\cos\alpha-\sin\alpha}=\frac{1+\tan\alpha}{1-\tan\alpha}",
    "image929.png": r"\frac{2\sin\alpha-\cos\alpha}{\sin\alpha+2\cos\alpha}",
    "image932.png": r"\frac{2\sin\alpha-\cos\alpha}{\sin\alpha+2\cos\alpha}=\frac{2\tan\alpha-1}{\tan\alpha+2}=\frac{3}{4}",
    "image947.wmf": r"\alpha",
    "image948.wmf": r"3\sin 2\alpha\cos\alpha=8\sin\alpha\cos 2\alpha",
    "image954.wmf": r"\alpha",
    "image955.wmf": r"3\sin 2\alpha\cos\alpha=8\sin\alpha\cos 2\alpha",
    "image966.wmf": r"|\overrightarrow{m}|",
    "image1070.wmf": r"\alpha",
    "image1072.wmf": r"\sin\frac{\alpha}{2}=",
    "image1115.wmf": r"=\frac{2}{5}",
    "image1117.wmf": r"\alpha",
    "image1184.wmf": r"-\frac{1}{2}",
    "image1251.wmf": r"-\frac{1}{2}",
    "image1136.wmf": r"\alpha",
    "image1138.wmf": r"\tan\alpha+\tan\beta=4",
    "image1141.wmf": r"\alpha",
    "image1181.wmf": r"\frac{\pi}{2}\right]",
    "image1203.wmf": r"\frac{\pi}{12}-\left(-\frac{5\pi}{12}\right)\leq\frac{T}{2}",
    "image1204.wmf": r"0<\omega\leq2",
    "image1206.wmf": r"\begin{cases}\varphi=2k\pi+\frac{\pi}{3},\\\varphi=m\pi-\frac{2\pi}{3}\end{cases}",
    "image1211.wmf": r"\frac{\pi}{2}\right]",
    "image1308.wmf": r"(\frac{3\pi}{2}",
    "image1309.wmf": r"2)",
    "image1326.wmf": "y",
    "image1338.wmf": "y",
    "image1374.wmf": r"g(x)",
    "image1376.wmf": r"g(x)",
    "image1378.wmf": r"g(x)",
    "image1380.wmf": r"g(x)",
    "image1389.wmf": r"g(x)",
    "image1391.wmf": r"g(x)",
    "image1397.wmf": r"1\right]",
    "image1399.wmf": r"1\right]",
    "image1412.wmf": r"g(x)",
    "image1523.wmf": "xOy",
    "image1524.wmf": r"\alpha",
    "image1526.wmf": "Ox",
    "image1528.wmf": r"\cos\beta",
    "image1529.wmf": r"\alpha",
    "image1542.wmf": r"\cos\beta",
    "image1543.wmf": r"-\frac{1}{2}",
    "image1544.wmf": r"-\frac{1}{2}",
    "image1561.wmf": "v",
    "image1562.wmf": "t",
    "image1563.wmf": r"v(t)=A\sin(\omega t+\varphi)+B\quad(A>0",
    "image1564.wmf": r"B\in\mathbb{R}",
    "image1565.wmf": r"\omega>0",
    "image1566.wmf": r"0<\varphi<2\pi)",
    "image1567.wmf": r"v(t)=0",
    "image1568.wmf": r"v(t)=4",
    "image1569.wmf": r"v(t)=",
    "image1590.wmf": r"-\frac{1}{2}",
    "image1591.wmf": r"\frac{1}{2}",
    "image1122.wmf": r"\alpha=",
    "image1124.wmf": r"\beta=",
    "image1296.wmf": r"(\frac{3\pi}{2}",
    "image1297.wmf": r"2)",
    "image1803.wmf": r"\left[-\frac{\pi}{3}",
    "image1804.wmf": r"\frac{2\pi}{3}\right]",
    "image1730.wmf": r"g(x)",
    "image1783.wmf": r"1\right]",
    "image1824.wmf": r"\frac{2\pi}{3}\right]",
    "image1830.wmf": r"\frac{2\pi}{3}\right]",
    "image1851.wmf": r"\frac{2\pi}{3}\right]",
}


SUSPICIOUS = {
    "mathbb": 4,
    "mathcal": 4,
    "mathfrak": 5,
    "mathsf": 4,
    "mathbf": 2,
    "operatorname": 2,
    "overline": 4,
    "underline": 4,
    "widehat": 4,
    "stackrel": 5,
    "overset": 5,
    "underbrace": 5,
    "lfloor": 4,
    "rfloor": 4,
    "nabla": 5,
    "partial": 4,
    "pounds": 5,
    "epsilon_": 5,
    "lambda_": 3,
    "Gamma": 3,
    "Upsilon": 5,
    "prod": 4,
    "sum": 3,
    "vec": 2,
    "dot": 2,
}


def score(latex: str) -> int:
    value = sum(latex.count(token) * weight for token, weight in SUSPICIOUS.items())
    value += abs(latex.count(r"\left") - latex.count(r"\right")) * 5
    value += len(re.findall(r"(?<![A-Za-z])\d{4,}(?![A-Za-z])", latex)) * 4
    value += len(re.findall(r"\\[A-Za-z]+\s+\\[A-Za-z]+\s+\\[A-Za-z]+", latex))
    value += latex.count("**") * 5 + latex.count("\\!")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("first", type=Path, help="Original-size OCR JSON")
    parser.add_argument("second", type=Path, help="Upscaled OCR JSON")
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--no-built-in-overrides",
        action="store_true",
        help="Do not apply overrides tied to the trigonometry source image names",
    )
    args = parser.parse_args()

    first = json.loads(args.first.read_text(encoding="utf-8"))["formulas"]
    second_data = json.loads(args.second.read_text(encoding="utf-8"))
    second = second_data["formulas"]
    selected = {"formulas": {}, "by_hash": second_data.get("by_hash", {})}
    counts = {"original": 0, "upscaled": 0, "manual": 0}
    for name in sorted(set(first) | set(second)):
        if not args.no_built_in_overrides and name in OVERRIDES:
            latex, method = OVERRIDES[name], "manual"
        elif name not in first:
            latex, method = second[name]["latex"], "upscaled"
        elif name not in second:
            latex, method = first[name]["latex"], "original"
        else:
            one, two = first[name]["latex"], second[name]["latex"]
            one_score, two_score = score(one), score(two)
            if two_score < one_score:
                latex, method = two, "upscaled"
            else:
                latex, method = one, "original"
        source = second.get(name, first.get(name, {}))
        selected["formulas"][name] = {
            **source,
            "latex": latex,
            "method": method,
            "candidate_scores": {
                "original": score(first[name]["latex"]) if name in first else None,
                "upscaled": score(second[name]["latex"]) if name in second else None,
            },
        }
        counts[method] += 1

    args.output.write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
