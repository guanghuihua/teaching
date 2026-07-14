param([Parameter(Mandatory = $true)][string]$OutputRoot)

$ErrorActionPreference = 'Stop'
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$statusFiles = @(Get-ChildItem -LiteralPath $OutputRoot -Recurse -Filter status.json | Sort-Object FullName)
$index = [Collections.Generic.List[object]]::new()
$reviewItems = [Collections.Generic.List[object]]::new()
$promptTokens = 0L
$completionTokens = 0L
$cachedTokens = 0L

foreach ($statusFile in $statusFiles) {
    $directory = $statusFile.DirectoryName
    $status = Get-Content -LiteralPath $statusFile.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    $jsonPath = Join-Path $directory 'questions.json'
    $data = Get-Content -LiteralPath $jsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $usagePath = [IO.Path]::ChangeExtension($jsonPath, '.usage.json')
    if (Test-Path -LiteralPath $usagePath) {
        $usage = Get-Content -LiteralPath $usagePath -Raw -Encoding UTF8 | ConvertFrom-Json
        $promptTokens += [long]$usage.prompt_tokens
        $completionTokens += [long]$usage.completion_tokens
        if ($usage.prompt_cache_hit_tokens) { $cachedTokens += [long]$usage.prompt_cache_hit_tokens }
    }

    foreach ($review in @($data.review_notes)) {
        $reviewItems.Add([pscustomobject]@{
            Year = Split-Path (Split-Path $directory -Parent) -Leaf
            PaperId = $status.paper_id
            Question = $review.question
            Issue = $review.issue
        })
    }

    $paperPdf = Join-Path $directory "$($status.paper_id)-试卷版.pdf"
    $answerPdf = Join-Path $directory "$($status.paper_id)-答案版.pdf"
    $paperPages = if (Test-Path $paperPdf) { [int]((pdfinfo $paperPdf | Select-String '^Pages:').Line -replace '^Pages:\s*','') } else { 0 }
    $answerPages = if (Test-Path $answerPdf) { [int]((pdfinfo $answerPdf | Select-String '^Pages:').Line -replace '^Pages:\s*','') } else { 0 }
    $relative = $directory.Substring($OutputRoot.TrimEnd('\').Length).TrimStart('\')
    $index.Add([pscustomobject]@{
        Year = Split-Path (Split-Path $directory -Parent) -Leaf
        PaperId = $status.paper_id
        Title = $data.title
        Questions = @($data.sections.questions).Count
        ReviewItems = @($data.review_notes).Count
        PaperPages = $paperPages
        AnswerPages = $answerPages
        PaperTex = Join-Path $relative "$($status.paper_id)-试卷版.tex"
        PaperPdf = Join-Path $relative "$($status.paper_id)-试卷版.pdf"
        AnswerTex = Join-Path $relative "$($status.paper_id)-答案版.tex"
        AnswerPdf = Join-Path $relative "$($status.paper_id)-答案版.pdf"
        Status = $status.status
    })
}

$index | Export-Csv -LiteralPath (Join-Path $OutputRoot 'index.csv') -NoTypeInformation -Encoding UTF8
$reviewItems | Export-Csv -LiteralPath (Join-Path $OutputRoot 'review-items.csv') -NoTypeInformation -Encoding UTF8

$estimatedCost = [math]::Round(($promptTokens / 1000000.0) * 1.0 + ($completionTokens / 1000000.0) * 2.0, 4)
$usageSummary = [pscustomobject]@{
    papers = $index.Count
    questions = ($index | Measure-Object Questions -Sum).Sum
    review_items = $reviewItems.Count
    prompt_tokens = $promptTokens
    completion_tokens = $completionTokens
    cached_prompt_tokens = $cachedTokens
    total_tokens = $promptTokens + $completionTokens
    estimated_cost_cny = $estimatedCost
    estimate_basis = 'deepseek-v4-flash: input CNY 1/M tokens, output CNY 2/M tokens; excludes retries outside this output set'
    generated_at = (Get-Date).ToString('s')
}
$usageSummary | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputRoot 'api-usage.json') -Encoding UTF8

$readme = @"
# 2016--2025 高考数学真题（exam-zh）

本目录整理了 2016--2025 十个年份的高考数学真题，共 $($index.Count) 份、$($usageSummary.questions) 道题。每份试卷均包含试卷版与答案版的 LaTeX 源码和 XeLaTeX 编译 PDF，共 $($index.Count * 2) 个成品 PDF。

## 文件说明

- `index.csv`：全部试卷索引、题数、页数及成品路径。
- `review-items.csv`：自动识别过程中需要人工复核的题目，共 $($reviewItems.Count) 条。
- `api-usage.json`：本批次 API token 用量与费用估算。
- 各年份子目录：每份试卷包含 `questions.json`、源卷 PDF、插图、exam-zh 内容文件、试卷版和答案版的 `.tex/.pdf`。

## 编译

进入某份试卷目录后运行：

```powershell
xelatex -interaction=nonstopmode "试卷文件名.tex"
xelatex -interaction=nonstopmode "试卷文件名.tex"
```

需要本机已安装 `exam-zh` 及 XeLaTeX。

## 复核说明

这些文件由源卷、解析版和视觉素材自动整理生成。所有文件已通过编译检查，但“可编译”不等于题面与答案完全无误。正式组卷或发给学生前，应优先核对 `review-items.csv` 中列出的项目，并与各目录下的 `source-original.pdf`、`source-solution.pdf` 对照。
"@
$readme | Set-Content -LiteralPath (Join-Path $OutputRoot 'README.md') -Encoding UTF8
