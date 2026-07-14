param([Parameter(Mandatory = $true)][string]$OutputDirectory)

$ErrorActionPreference='Stop'
$OutputDirectory=[IO.Path]::GetFullPath($OutputDirectory)
$classification=Get-Content -LiteralPath (Join-Path $OutputDirectory 'topic-classification.json') -Raw -Encoding UTF8|ConvertFrom-Json
$usage=Get-Content -LiteralPath (Join-Path $OutputDirectory 'classification-usage.json') -Raw -Encoding UTF8|ConvertFrom-Json
$reviewRows=[Collections.Generic.List[object]]::new();$cache=@{}
foreach($item in $classification){
    if(-not $cache.ContainsKey($item.source_json)){$cache[$item.source_json]=Get-Content -LiteralPath $item.source_json -Raw -Encoding UTF8|ConvertFrom-Json}
    foreach($review in @($cache[$item.source_json].review_notes|Where-Object {$_.question -eq $item.number})){
        $reviewRows.Add([pscustomobject]@{Year=$item.year;Paper=($item.paper_id -replace '^\d{4}-','');Question=$item.number;Tags=(@($item.tags)-join '、');Issue=$review.issue})
    }
}
$reviewRows|Export-Csv -LiteralPath (Join-Path $OutputDirectory '需复核题目.csv') -NoTypeInformation -Encoding UTF8

$stats=[Collections.Generic.List[object]]::new()
foreach($year in 2016..2025){$items=@($classification|? year -eq $year);$stats.Add([pscustomobject]@{Year=$year;Total=$items.Count;Triangle=@($items|?{$_.tags -contains '三角形'}).Count;Trigonometry=@($items|?{$_.tags -contains '三角函数'}).Count;Vector=@($items|?{$_.tags -contains '向量'}).Count})}
$stats|Export-Csv -LiteralPath (Join-Path $OutputDirectory '专题统计.csv') -NoTypeInformation -Encoding UTF8

$triangle=@($classification|?{$_.tags -contains '三角形'}).Count
$trig=@($classification|?{$_.tags -contains '三角函数'}).Count
$vector=@($classification|?{$_.tags -contains '向量'}).Count
$estimated=[math]::Round(([long]$usage.prompt_tokens/1000000.0)+2*([long]$usage.completion_tokens/1000000.0),4)
$usage|Add-Member -NotePropertyName estimated_cost_cny -NotePropertyValue $estimated -Force
$usage|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $OutputDirectory 'classification-usage.json') -Encoding UTF8
$readme=@"
# 近十年高考数学：三角形、三角函数与向量专题汇编

范围为 2016--2025 年，共收录 $($classification.Count) 道题：三角形 $triangle 道、三角函数 $trig 道、向量 $vector 道。综合题可同时具有多个标签，因此三个专题计数之和大于总题数。

## 成品

- `近十年高考数学三角形三角函数与向量专题汇编-试卷版.tex/.pdf`：只保留题目，共 48 页。
- `近十年高考数学三角形三角函数与向量专题汇编-答案版.tex/.pdf`：包含答案、分析与详解，共 138 页。
- `题目索引.csv`：汇编题号、年份、卷名、原题号、专题标签与分类理由。
- `专题统计.csv`：按年份统计三个专题题量。
- `需复核题目.csv`：原批次中存在公式缺字、图片匹配或依据解析版补全记录的入选题目，共 $($reviewRows.Count) 条。

## 分类口径

题目先由 DeepSeek 对全部 1577 道题进行专题判断，再对关键词漏项进行二次模型复核，最后用强规则补入明确含三角函数运算、向量运算或解三角形条件的题目。仅以 `sin/cos` 表示曲线的参数方程题不计入三角函数专题；立体几何中只出现三角形名称、但不以解三角形为核心的题不计入三角形专题。

本次分类调用 DeepSeek 共使用 $($usage.prompt_tokens) 个输入 token、$($usage.completion_tokens) 个输出 token，按当前记录价格估算约 $estimated 元。

正式用于学生试卷前，请先检查 `需复核题目.csv`，并与原题目录中的 `source-original.pdf` 和 `source-solution.pdf` 对照。
"@
$readme|Set-Content -LiteralPath (Join-Path $OutputDirectory 'README.md') -Encoding UTF8
Write-Output "SUMMARY reviews=$($reviewRows.Count) cost=$estimated"
