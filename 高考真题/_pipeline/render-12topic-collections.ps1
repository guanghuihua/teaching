param(
    [Parameter(Mandatory=$true)][string]$ClassificationPath,
    [Parameter(Mandatory=$true)][string]$OutputRoot
)

$ErrorActionPreference='Stop'
$ClassificationPath=[IO.Path]::GetFullPath($ClassificationPath)
$OutputRoot=[IO.Path]::GetFullPath($OutputRoot)
$classification=Get-Content -LiteralPath $ClassificationPath -Raw -Encoding UTF8|ConvertFrom-Json
$topicOrder=@(
    '集合与逻辑','一元二次函数、方程和不等式','函数','三角函数','平面向量与解三角形','复数',
    '立体几何','平面解析几何','数列','导数','计数原理','统计与概率'
)

function Repair-LatexText {
    param([string]$Text)
    if($null -eq $Text){return ''};$value=$Text
    $value=$value-replace'#+',''
    $value=$value-replace'\\+(?=[一-龥])',''
    $value=$value.Replace('∵','因为').Replace('∴','所以')
    $value=$value-replace'(?<!\\)_{2,}',''
    $value=$value-replace'\\overgroup\{([^{}]*)\}','\\overset{\\frown}{$1}'
    $value=$value-replace'\^\\frac\{([^{}]*)\}\{([^{}]*)\}','^{\\frac{$1}{$2}}'
    $value=$value-replace'\\complement_\\mathbb\{R\}([A-Za-z])','\\mathbb{R}\\setminus $1'
    $value=$value-replace'\]\$\$(?=[=<>+\-])',']$，$'
    $value=$value.Replace('$\left\{$\begin{array}','$\left\{\begin{array}').Replace('\end{array}$\right.$','\end{array}\right.$')
    if($value.Contains('\begin{array}') -and -not $value.Contains('$\begin{array}') -and -not $value.Contains('\[\begin{array}') -and -not $value.Contains('\left\{\begin{array}')){$value=$value.Replace('\begin{array}','$\begin{array}').Replace('\end{array}','\end{array}$')}
    return $value
}

function Convert-BareTableRows {
    param([string]$Text)
    if(-not $Text.Contains('&') -or $Text -match '\\begin\{(?:array|tabular|aligned|cases)\}'){return $Text}
    $lines=@($Text-split"`r?`n");$output=[Collections.Generic.List[string]]::new();$i=0
    while($i -lt $lines.Count){
        if(-not $lines[$i].Contains('&')){$output.Add($lines[$i]);$i++;continue}
        $rows=[Collections.Generic.List[string]]::new()
        while($i -lt $lines.Count -and ($lines[$i].Contains('&') -or [string]::IsNullOrWhiteSpace($lines[$i]))){if(-not [string]::IsNullOrWhiteSpace($lines[$i])){$rows.Add($lines[$i].Trim())};$i++}
        $columns=($rows|%{[regex]::Matches($_,'&').Count+1}|Measure -Maximum).Maximum
        $output.Add('\begin{center}');$output.Add("\begin{tabular}{"+('c'*$columns)+'}')
        for($j=0;$j -lt $rows.Count;$j++){$row=$rows[$j] -replace '\\\\\s*$','';if($j -lt $rows.Count-1){$row+=' \\'};$output.Add($row)}
        $output.Add('\end{tabular}');$output.Add('\end{center}')
    }
    return $output -join "`r`n"
}

function Get-FillinContent {
    param([string]$Answer)
    $value=(Repair-LatexText $Answer).Trim()
    if($value -match '^\$\$([^$]+)\$\$$'){return '$'+$matches[1].Trim()+'$'}
    if($value -match '^\$[^$]+\$$' -or $value.Contains('$')){return $value}
    if($value.StartsWith('\(') -and $value.EndsWith('\)')){return $value}
    return '$'+$value+'$'
}

$jsonCache=@{};$globalIndex=[Collections.Generic.List[object]]::new();$topicNumber=0
foreach($topic in $topicOrder){
    $topicNumber++;$items=@($classification|Where-Object primary_topic -eq $topic|Sort-Object year,paper_id,number,occurrence)
    $folderName=('{0:D2}-{1}'-f$topicNumber,$topic);$directory=Join-Path $OutputRoot $folderName;$assetsDirectory=Join-Path $directory 'assets'
    New-Item -ItemType Directory -Path $assetsDirectory -Force|Out-Null
    $baseName="$folderName-2016-2025高考真题汇编";$content=[Collections.Generic.List[string]]::new();$topicIndex=[Collections.Generic.List[object]]::new()
    $content.Add("\title{$topic（2016--2025 高考真题）}");$content.Add('\author{}');$content.Add('\date{}');$content.Add('\maketitle');$content.Add("\noindent 本专题共 $($items.Count) 道题，按年份排列。每题标注原卷与原题号。");$content.Add('')
    $currentYear=0;$collectionNumber=0
    foreach($item in $items){
        if($item.year -ne $currentYear){$currentYear=$item.year;$content.Add("\section*{$currentYear 年}");$content.Add('')}
        if(-not $jsonCache.ContainsKey($item.source_json)){$jsonCache[$item.source_json]=Get-Content -LiteralPath $item.source_json -Raw -Encoding UTF8|ConvertFrom-Json}
        $paperData=$jsonCache[$item.source_json]
        $matches=@($paperData.sections.questions|Where-Object number -eq $item.number)
        $question=$matches[([int]$item.occurrence-1)]
        if($null -eq $question){throw "Question not found: $($item.id)"}
        $collectionNumber++;$points=if($question.points -and [double]$question.points -gt 0){"[points=$($question.points)]"}else{''}
        $content.Add("\begin{question}$points")
        $paperLabel=$item.paper_id-replace'^\d{4}-','';$secondary=if(@($item.secondary_topics).Count){'；次专题：'+(@($item.secondary_topics)-join'、')}else{''}
        $content.Add("\textbf{来源：}$($item.year) 年 $paperLabel，第 $($item.number) 题$secondary\par")
        $stem=(Convert-BareTableRows(Repair-LatexText $question.stem_latex))-replace"`r?`n","`r`n`r`n"
        if($question.type -eq 'fill_blank'){$stem=$stem -replace '(?:\\_){2,}','';$stem=$stem -replace '_{2,}','';$stem=$stem -replace '\$\$',''}
        $content.Add($stem)
        $assetNumber=0
        foreach($asset in @($question.assets|Where-Object{$_.file})){
            $sourceAsset=Join-Path $item.source_directory $asset.file;if(-not(Test-Path -LiteralPath $sourceAsset)){continue}
            $assetNumber++;$extension=[IO.Path]::GetExtension($sourceAsset).ToLowerInvariant();$assetName=('asset-{0:D3}-{1:D2}{2}'-f$collectionNumber,$assetNumber,$extension)
            Copy-Item -LiteralPath $sourceAsset -Destination(Join-Path $assetsDirectory $assetName)-Force
            $content.Add('');$content.Add('\begin{center}');$content.Add("  \includegraphics[width=.42\linewidth]{assets/$assetName}");$content.Add('\end{center}')
        }
        if($question.type -in @('single_choice','multiple_choice')){$content.Add('\begin{choices}');foreach($choice in $question.choices){$content.Add("  \item $(Repair-LatexText $choice)")};$content.Add('\end{choices}')}
        elseif($question.type -eq 'fill_blank'){$fill=Get-FillinContent $question.answer_latex;$content.Add("\fillin[{$fill}]")}
        $content.Add('\begin{solution}')
        if(-not [string]::IsNullOrWhiteSpace($question.answer_latex)){if($question.type -eq 'fill_blank'){$fill=Get-FillinContent $question.answer_latex;$content.Add("\textbf{答案：}$fill")}else{$content.Add("\textbf{答案：}$(Repair-LatexText $question.answer_latex)")}}
        if(-not [string]::IsNullOrWhiteSpace($question.analysis_latex)){$content.Add('');$content.Add("\textbf{分析：}$(Repair-LatexText $question.analysis_latex)")}
        if(-not [string]::IsNullOrWhiteSpace($question.solution_latex)){$content.Add('');$content.Add("\textbf{详解：}$(Repair-LatexText $question.solution_latex)")}
        $content.Add('\end{solution}');$content.Add('\end{question}');$content.Add('')
        $row=[pscustomobject]@{Topic=$topic;CollectionNumber=$collectionNumber;Year=$item.year;Paper=$paperLabel;OriginalQuestion=$item.number;Occurrence=$item.occurrence;Type=$question.type;SecondaryTopics=(@($item.secondary_topics)-join'、');Reason=$item.reason;Id=$item.id}
        $topicIndex.Add($row);$globalIndex.Add($row)
    }
    $contentPath=Join-Path $directory "$baseName-内容.tex";$content|Set-Content -LiteralPath $contentPath -Encoding UTF8
    $common=@"
% !TeX program = xelatex
\documentclass[zihao=-4]{exam-zh}
\usepackage{amsmath,graphicx,array,multirow,booktabs}
\geometry{a4paper,margin=2cm}
\setchoices{max-columns=4}
\questionsetup{show-points=true}
"@
    @"
$common
\fillinsetup{no-answer-type=none,width=6em}
\examsetup{question/show-answer=false,solution/show-solution=hide}
\begin{document}
\input{$baseName-内容.tex}
\end{document}
"@|Set-Content -LiteralPath(Join-Path $directory "$baseName-试卷版.tex")-Encoding UTF8
    @"
$common
\examsetup{question/show-answer=true,solution/show-solution=show-stay}
\begin{document}
\input{$baseName-内容.tex}
\end{document}
"@|Set-Content -LiteralPath(Join-Path $directory "$baseName-答案版.tex")-Encoding UTF8
    $topicIndex|Export-Csv -LiteralPath(Join-Path $directory '题目索引.csv')-NoTypeInformation -Encoding UTF8
    Write-Output "RENDERED $folderName questions=$($items.Count) assets=$((Get-ChildItem $assetsDirectory -File).Count)"
}
$globalIndex|Export-Csv -LiteralPath(Join-Path $OutputRoot '全部题目索引.csv')-NoTypeInformation -Encoding UTF8
