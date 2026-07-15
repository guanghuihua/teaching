param(
    [Parameter(Mandatory=$true)][string]$ClassificationPath,
    [Parameter(Mandatory=$true)][string]$OutputRoot
)

$ErrorActionPreference='Stop'
$ClassificationPath=[IO.Path]::GetFullPath($ClassificationPath);$OutputRoot=[IO.Path]::GetFullPath($OutputRoot)
$classification=Get-Content -LiteralPath $ClassificationPath -Raw -Encoding UTF8|ConvertFrom-Json
$usage=Get-Content -LiteralPath(Join-Path $OutputRoot 'classification-usage.json')-Raw -Encoding UTF8|ConvertFrom-Json
$topicOrder=@('集合与逻辑','一元二次函数、方程和不等式','函数','三角函数','平面向量与解三角形','复数','立体几何','平面解析几何','数列','导数','计数原理','统计与概率')
$stats=[Collections.Generic.List[object]]::new();$readmeRows=[Collections.Generic.List[string]]::new();$reviewRows=[Collections.Generic.List[object]]::new();$jsonCache=@{}
$topicNumber=0
foreach($topic in $topicOrder){
    $topicNumber++;$folderName=('{0:D2}-{1}'-f$topicNumber,$topic);$directory=Join-Path $OutputRoot $folderName
    $paperPdf=Get-ChildItem -LiteralPath $directory -Filter '*试卷版.pdf'|Select-Object -First 1;$answerPdf=Get-ChildItem -LiteralPath $directory -Filter '*答案版.pdf'|Select-Object -First 1
    $paperPages=[int]((pdfinfo $paperPdf.FullName|Select-String '^Pages:').Line-replace'^Pages:\s*','');$answerPages=[int]((pdfinfo $answerPdf.FullName|Select-String '^Pages:').Line-replace'^Pages:\s*','')
    $items=@($classification|Where-Object primary_topic -eq $topic)
    $stats.Add([pscustomobject]@{Number=$topicNumber;Topic=$topic;Questions=$items.Count;PaperPages=$paperPages;AnswerPages=$answerPages;Assets=@(Get-ChildItem(Join-Path $directory 'assets')-File).Count;Folder=$folderName})
    $readmeRows.Add("| $topicNumber | $topic | $($items.Count) | $paperPages | $answerPages | [$folderName]($folderName/) |")
    foreach($item in $items){
        if(-not $jsonCache.ContainsKey($item.source_json)){$jsonCache[$item.source_json]=Get-Content -LiteralPath $item.source_json -Raw -Encoding UTF8|ConvertFrom-Json}
        foreach($review in @($jsonCache[$item.source_json].review_notes|Where-Object question -eq $item.number)){
            $reviewRows.Add([pscustomobject]@{Topic=$topic;Year=$item.year;Paper=($item.paper_id-replace'^\d{4}-','');Question=$item.number;Occurrence=$item.occurrence;Issue=$review.issue;Id=$item.id})
        }
    }
}
$stats|Export-Csv -LiteralPath(Join-Path $OutputRoot '专题统计.csv')-NoTypeInformation -Encoding UTF8
$reviewRows|Export-Csv -LiteralPath(Join-Path $OutputRoot '需复核题目.csv')-NoTypeInformation -Encoding UTF8

$yearRows=[Collections.Generic.List[object]]::new()
foreach($year in 2016..2025){
    foreach($topic in $topicOrder){$yearRows.Add([pscustomobject]@{Year=$year;Topic=$topic;Questions=@($classification|Where-Object{$_.year -eq $year -and $_.primary_topic -eq $topic}).Count})}
}
$yearRows|Export-Csv -LiteralPath(Join-Path $OutputRoot '按年份统计.csv')-NoTypeInformation -Encoding UTF8
$estimated=[math]::Round(([long]$usage.prompt_tokens/1000000.0)+2*([long]$usage.completion_tokens/1000000.0),4)
$usage|Add-Member -NotePropertyName estimated_cost_cny -NotePropertyValue $estimated -Force
$usage|ConvertTo-Json|Set-Content -LiteralPath(Join-Path $OutputRoot 'classification-usage.json')-Encoding UTF8
$totalPaperPages=($stats|Measure PaperPages -Sum).Sum;$totalAnswerPages=($stats|Measure AnswerPages -Sum).Sum
$table=$readmeRows-join"`r`n"
$readme=@"
# 2016--2025 高考数学真题十二专题分类

本目录将 2016--2025 年 71 份高考数学试卷中的 1577 道题全部分类到 12 个主专题。每题只有一个主专题，综合题另保留次专题标签，因此主专题题数合计严格等于 1577。

| 序号 | 专题 | 题数 | 试卷版页数 | 答案版页数 | 目录 |
|---:|---|---:|---:|---:|---|
$table

12 套试卷版合计 $totalPaperPages 页，12 套答案版合计 $totalAnswerPages 页。所有 24 个 PDF 均已通过 XeLaTeX 编译。

## 索引文件

- `全部题目索引.csv`：1577 道题的专题、年份、卷名、原题号、次专题和分类理由。
- `专题统计.csv`：各专题题数、页数和图片数。
- `按年份统计.csv`：各年份在 12 个专题中的题量分布。
- `需复核题目.csv`：原始数字化过程中存在公式缺字、图片匹配或依据解析版补全记录的题目，共 $($reviewRows.Count) 条。
- `classification-corrections.csv`：强特征审计后的人工规则校正记录。
- `classification-12topics.json`：完整结构化分类结果。

## 分类原则

分类以核心设问和主要解法为准。圆锥曲线中使用向量仍归平面解析几何；空间向量归立体几何；以导数研究三角函数单调性或不等式的题归导数；直接求概率的排列组合题归统计与概率，并把计数原理保留为次专题。

最终有效分类调用 DeepSeek 使用 $($usage.prompt_tokens) 个输入 token、$($usage.completion_tokens) 个输出 token，按当前记录价格估算约 $estimated 元。此前因 9 个重复题号而废弃的一轮分类未计入本数值。

正式用于学生试卷前，请先检查 `需复核题目.csv`，并与原题目录内的源卷和解析版 PDF 对照。
"@
$readme|Set-Content -LiteralPath(Join-Path $OutputRoot 'README.md')-Encoding UTF8
Write-Output "SUMMARY questions=$($classification.Count) reviews=$($reviewRows.Count) paper_pages=$totalPaperPages answer_pages=$totalAnswerPages cost=$estimated"
