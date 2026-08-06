# 圆锥曲线图片资料导入

本目录是 `E:\Guanghui\ai读取\圆锥曲线` 中 47 张教材照片的结构化识别结果。
原图保持只读，所有识别结果均为教师复核前草稿。

## 主要文件

- `conic_image_bank.tex`：按源图顺序整理的完整 LaTeX 文档。
- `pages/001.json` 至 `pages/047.json`：逐页识别结果、结构化题目、不确定项和模型信息。
- `question_candidates.json`：125 道题目候选，供后续教师审核和题库导入。
- `import_reports/conic_image_inventory.json`：原图路径、大小和 SHA256。
- `import_reports/conic_image_ocr_report.md`：识别统计、风险和低置信度页面。

## 重跑方式

程序位于 `E:\Guanghui\mindduet-math`，提取后的教师资产默认写入
`E:\Guanghui\teaching\题目积累\圆锥曲线\图片资料整理`。在项目根目录设置临时环境变量后运行：

```powershell
$env:PACKY_API_KEY="<PackyAPI key>"
$env:MINDDUET_CONIC_OUTPUT="E:\Guanghui\teaching\题目积累\圆锥曲线\图片资料整理"
.\.venv\Scripts\python.exe scripts\import_conic_images.py --workers 3
Remove-Item Env:PACKY_API_KEY
Remove-Item Env:MINDDUET_CONIC_OUTPUT
```

只根据已有 JSON 重新生成 TeX、题目候选和报告：

```powershell
.\.venv\Scripts\python.exe scripts\import_conic_images.py --skip-ocr
```

脚本默认断点续跑；已有逐页 JSON 会被跳过。使用 `--force` 才会覆盖识别结果。

## 审核顺序

优先检查低置信度页面：`002`、`011`、`012`、`017`、`025`、`029`、`030`、`041`、
`042`、`046`、`047`。

随后检查所有带有以下标记的内容：

- `[待人工核对]`
- `[图形见原图]`
- `diagram_required: true`
- 空答案或空解析

识别内容不能直接作为自动判题标准答案。教师确认后，才能转换为正式的 MindDuet Math
题目清单和评分规则。
