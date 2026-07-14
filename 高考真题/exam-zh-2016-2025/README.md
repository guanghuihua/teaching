# 2016--2025 高考数学真题（exam-zh）

本目录整理了 2016--2025 十个年份的高考数学真题，共 71 份、1577 道题。每份试卷均包含试卷版与答案版的 LaTeX 源码和 XeLaTeX 编译 PDF，共 142 个成品 PDF。

## 文件说明

- index.csv：全部试卷索引、题数、页数及成品路径。
- eview-items.csv：自动识别过程中需要人工复核的题目，共 446 条。
- pi-usage.json：本批次 API token 用量与费用估算。
- 各年份子目录：每份试卷包含 questions.json、源卷 PDF、插图、exam-zh 内容文件、试卷版和答案版的 .tex/.pdf。

## 编译

进入某份试卷目录后运行：

`powershell
xelatex -interaction=nonstopmode "试卷文件名.tex"
xelatex -interaction=nonstopmode "试卷文件名.tex"
`

需要本机已安装 exam-zh 及 XeLaTeX。

## 复核说明

这些文件由源卷、解析版和视觉素材自动整理生成。所有文件已通过编译检查，但“可编译”不等于题面与答案完全无误。正式组卷或发给学生前，应优先核对 eview-items.csv 中列出的项目，并与各目录下的 source-original.pdf、source-solution.pdf 对照。
