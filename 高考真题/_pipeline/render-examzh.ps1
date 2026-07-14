param(
    [Parameter(Mandatory = $true)]
    [string]$JsonPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory,

    [Parameter(Mandatory = $true)]
    [string]$BaseName
)

$ErrorActionPreference = "Stop"
$data = Get-Content -LiteralPath $JsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

function Repair-LatexText {
    param([string]$Text)
    if ($null -eq $Text) { return "" }
    $value = $Text
    $value = $value -replace '#+', ''
    $value = $value -replace '\\(?=[一-龥])', ''
    $value = $value -replace '(?<!\\)_{2,}', ''
    $value = $value -replace '\\overgroup\{([^{}]*)\}', '\\overset{\\frown}{$1}'
    $value = $value -replace '\^\\frac\{([^{}]*)\}\{([^{}]*)\}', '^{\\frac{$1}{$2}}'
    $value = $value -replace '\\complement_\\mathbb\{R\}([A-Za-z])', '\\mathbb{R}\\setminus $1'
    $value = $value -replace '\]\$\$(?=[=<>+\-])', ']$，$'
    if ($value.Contains('\begin{array}') -and
        -not $value.Contains('$\begin{array}') -and
        -not $value.Contains('\[\begin{array}')) {
        $value = $value.Replace('\begin{array}', '$\begin{array}')
        $value = $value.Replace('\end{array}', '\end{array}$')
    }
    return $value
}

function Get-FillinContent {
    param([string]$Answer)
    $value = (Repair-LatexText $Answer).Trim()
    if ($value -match '^\$\$([^$]+)\$\$$') {
        return '$' + $matches[1].Trim() + '$'
    }
    if ($value -match '^\$[^$]+\$$' -or $value.Contains('$')) {
        return $value
    }
    if ($value.StartsWith('\(') -and $value.EndsWith('\)')) { return $value }
    return '$' + $value + '$'
}

function Convert-BareTableRows {
    param([string]$Text)
    if (-not $Text.Contains('&') -or
        $Text -match '\\begin\{(?:array|tabular|aligned|cases)\}') {
        return $Text
    }

    $lines = @($Text -split "`r?`n")
    $output = [Collections.Generic.List[string]]::new()
    $i = 0
    while ($i -lt $lines.Count) {
        if (-not $lines[$i].Contains('&')) {
            $output.Add($lines[$i])
            $i++
            continue
        }

        $rows = [Collections.Generic.List[string]]::new()
        while ($i -lt $lines.Count -and ($lines[$i].Contains('&') -or [string]::IsNullOrWhiteSpace($lines[$i]))) {
            if (-not [string]::IsNullOrWhiteSpace($lines[$i])) { $rows.Add($lines[$i].Trim()) }
            $i++
        }
        $columnCount = ($rows | ForEach-Object { ([regex]::Matches($_, '&').Count + 1) } | Measure-Object -Maximum).Maximum
        $output.Add('\begin{center}')
        $output.Add("\begin{tabular}{" + ('c' * $columnCount) + "}")
        for ($rowIndex = 0; $rowIndex -lt $rows.Count; $rowIndex++) {
            $row = $rows[$rowIndex] -replace '\\\\\s*$', ''
            if ($rowIndex -lt $rows.Count - 1) { $row += ' \\' }
            $output.Add($row)
        }
        $output.Add('\end{tabular}')
        $output.Add('\end{center}')
    }
    return ($output -join "`r`n")
}

$content = [Collections.Generic.List[string]]::new()
$content.Add("\title{$($data.title)}")
$content.Add("\date{}")
$content.Add("\maketitle")
$content.Add("")

foreach ($section in $data.sections) {
    $content.Add("\section*{$($section.title)}")
    if (-not [string]::IsNullOrWhiteSpace($section.instructions)) {
        $content.Add((Repair-LatexText $section.instructions))
    }
    $content.Add("")

    foreach ($question in $section.questions) {
        if ($question.points -and [double]$question.points -gt 0) {
            $content.Add("\begin{question}[points=$($question.points)]")
        }
        else {
            $content.Add("\begin{question}")
        }
        $stem = (Convert-BareTableRows (Repair-LatexText $question.stem_latex)) -replace "`r?`n", "`r`n`r`n"
        if ($question.type -eq "fill_blank") {
            $stem = $stem -replace '(?:\\_){2,}', ''
            $stem = $stem -replace '_{2,}', ''
            $stem = $stem -replace '\$\$', ''
        }
        $content.Add($stem)

        $assetFiles = @($question.assets | Where-Object { $_.file })
        if ($assetFiles.Count -gt 0) {
            foreach ($asset in $assetFiles) {
                $content.Add("")
                $content.Add("\begin{center}")
                $content.Add("  \includegraphics[width=.38\linewidth]{$($asset.file)}")
                $content.Add("\end{center}")
            }
        }

        if ($question.type -in @("single_choice", "multiple_choice")) {
            $content.Add("\begin{choices}")
            foreach ($choice in $question.choices) {
                $content.Add("  \item $(Repair-LatexText $choice)")
            }
            $content.Add("\end{choices}")
        }
        elseif ($question.type -eq "fill_blank") {
            $fillAnswer = Get-FillinContent $question.answer_latex
            $content.Add("\fillin[{$fillAnswer}]")
        }

        $content.Add("\begin{solution}")
        if (-not [string]::IsNullOrWhiteSpace($question.answer_latex)) {
            if ($question.type -eq "fill_blank") {
                $fillAnswer = Get-FillinContent $question.answer_latex
                $content.Add("\textbf{答案：}$fillAnswer")
            }
            else {
                $content.Add("\textbf{答案：}$(Repair-LatexText $question.answer_latex)")
            }
        }
        if (-not [string]::IsNullOrWhiteSpace($question.analysis_latex)) {
            $content.Add("")
            $content.Add("\textbf{分析：}$(Repair-LatexText $question.analysis_latex)")
        }
        if (-not [string]::IsNullOrWhiteSpace($question.solution_latex)) {
            $content.Add("")
            $content.Add("\textbf{详解：}$(Repair-LatexText $question.solution_latex)")
        }
        $content.Add("\end{solution}")
        $content.Add("\end{question}")
        $content.Add("")
    }
}

$contentPath = Join-Path $OutputDirectory "$BaseName-内容.tex"
$content | Set-Content -LiteralPath $contentPath -Encoding UTF8

$common = @"
% !TeX program = xelatex
\documentclass[zihao=-4]{exam-zh}
\usepackage{amsmath,graphicx,array,multirow,booktabs}
\geometry{a4paper,margin=2cm}
\setchoices{max-columns=4}
\questionsetup{show-points=true}
"@

$paper = @"
$common
\fillinsetup{no-answer-type=none,width=6em}
\examsetup{
  question/show-answer = false,
  solution/show-solution = hide,
}
\begin{document}
\input{$BaseName-内容.tex}
\end{document}
"@

$answer = @"
$common
\examsetup{
  question/show-answer = true,
  solution/show-solution = show-stay,
}
\begin{document}
\input{$BaseName-内容.tex}
\end{document}
"@

$paper | Set-Content -LiteralPath (Join-Path $OutputDirectory "$BaseName-试卷版.tex") -Encoding UTF8
$answer | Set-Content -LiteralPath (Join-Path $OutputDirectory "$BaseName-答案版.tex") -Encoding UTF8
