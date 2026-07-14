param(
    [Parameter(Mandatory = $true)][string]$ManifestPath,
    [Parameter(Mandatory = $true)][int]$Index,
    [Parameter(Mandatory = $true)][string]$OutputRoot,
    [Parameter(Mandatory = $true)][string]$WorkRoot,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ManifestPath = [IO.Path]::GetFullPath($ManifestPath)
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$WorkRoot = [IO.Path]::GetFullPath($WorkRoot)
$pipeline = $PSScriptRoot
$rows = @(Import-Csv -LiteralPath $ManifestPath)
if ($Index -lt 0 -or $Index -ge $rows.Count) { throw "Manifest index out of range: $Index" }
$row = $rows[$Index]
$paperId = $row.PaperId
$outputDirectory = Join-Path (Join-Path $OutputRoot $row.Year) $paperId
$workDirectory = Join-Path $WorkRoot ("paper-{0:D3}" -f $Index)
$statusPath = Join-Path $outputDirectory "status.json"

if (-not $Force -and (Test-Path -LiteralPath $statusPath)) {
    $existing = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($existing.status -eq "complete") {
        Write-Output "SKIP $paperId"
        exit 0
    }
}

New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
if (Test-Path -LiteralPath $workDirectory) { Remove-Item -LiteralPath $workDirectory -Recurse -Force }
New-Item -ItemType Directory -Path $workDirectory -Force | Out-Null

function Export-SourcePdf {
    param([string]$SourcePath, [string]$PdfPath)
    if ([IO.Path]::GetExtension($SourcePath).ToLowerInvariant() -eq ".pdf") {
        Copy-Item -LiteralPath $SourcePath -Destination $PdfPath -Force
        return
    }

    $lastExit = 1
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pipeline "export-word-pdf.ps1") -InputPath $SourcePath -OutputPath $PdfPath
        $lastExit = $LASTEXITCODE
        if ($lastExit -eq 0 -and (Test-Path -LiteralPath $PdfPath)) { return }
        Start-Sleep -Seconds 2
    }
    throw "Word export failed after two attempts: $SourcePath (exit $lastExit)"
}

$started = Get-Date
try {
    $originalPdf = Join-Path $workDirectory "original.pdf"
    $solutionPdf = Join-Path $workDirectory "solution.pdf"
    Export-SourcePdf -SourcePath $row.OriginalPath -PdfPath $originalPdf
    if ($row.OriginalPath -eq $row.SolutionPath) {
        Copy-Item -LiteralPath $originalPdf -Destination $solutionPdf -Force
    }
    else {
        Export-SourcePdf -SourcePath $row.SolutionPath -PdfPath $solutionPdf
    }

    Copy-Item -LiteralPath $originalPdf -Destination (Join-Path $outputDirectory "source-original.pdf") -Force
    Copy-Item -LiteralPath $solutionPdf -Destination (Join-Path $outputDirectory "source-solution.pdf") -Force

    $originalText = Join-Path $workDirectory "original.txt"
    $solutionText = Join-Path $workDirectory "solution.txt"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pipeline "extract-pdf-text.ps1") -PdfPath $originalPdf -OutputPath $originalText
    if ($LASTEXITCODE -ne 0) { throw "Original PDF text extraction failed" }
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pipeline "extract-pdf-text.ps1") -PdfPath $solutionPdf -OutputPath $solutionText
    if ($LASTEXITCODE -ne 0) { throw "Solution PDF text extraction failed" }

    $combinedPath = Join-Path $workDirectory "deepseek-input.txt"
    $original = Get-Content -LiteralPath $originalText -Raw -Encoding UTF8
    $solution = Get-Content -LiteralPath $solutionText -Raw -Encoding UTF8
    "===== 原卷 =====`r`n$original`r`n===== 解析版 =====`r`n$solution" | Set-Content -LiteralPath $combinedPath -Encoding UTF8

    $jsonPath = Join-Path $outputDirectory "questions.json"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pipeline "invoke-deepseek.ps1") -InputPath $combinedPath -OutputPath $jsonPath
    if ($LASTEXITCODE -ne 0) { throw "DeepSeek conversion failed" }

    $data = Get-Content -LiteralPath $jsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $questions = @($data.sections.questions)
    if ($questions.Count -lt 5) { throw "DeepSeek returned too few questions: $($questions.Count)" }
    $data.title = $row.Title
    $data | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $jsonPath -Encoding UTF8

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pipeline "map-assets.ps1") -JsonPath $jsonPath -OriginalPdf $originalPdf -OutputDirectory $outputDirectory -WorkDirectory $workDirectory
    if ($LASTEXITCODE -ne 0) { throw "Asset mapping failed" }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pipeline "render-examzh.ps1") -JsonPath $jsonPath -OutputDirectory $outputDirectory -BaseName $paperId
    if ($LASTEXITCODE -ne 0) { throw "exam-zh rendering failed" }

    $compileOk = $true
    Push-Location $outputDirectory
    try {
        foreach ($variant in @("试卷版", "答案版")) {
            $texName = "$paperId-$variant.tex"
            for ($pass = 1; $pass -le 2; $pass++) {
                xelatex -interaction=nonstopmode -halt-on-error $texName *> (Join-Path $outputDirectory "$paperId-$variant.compile.txt")
                if ($LASTEXITCODE -ne 0) { $compileOk = $false; break }
            }
        }
    }
    finally { Pop-Location }

    $data = Get-Content -LiteralPath $jsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $usagePath = [IO.Path]::ChangeExtension($jsonPath, ".usage.json")
    $usage = if (Test-Path -LiteralPath $usagePath) { Get-Content -LiteralPath $usagePath -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }
    $status = [pscustomobject]@{
        paper_id = $paperId
        title = $row.Title
        status = if ($compileOk) { "complete" } else { "compile_failed" }
        question_count = @($data.sections.questions).Count
        review_count = @($data.review_notes).Count
        prompt_tokens = if ($usage) { $usage.prompt_tokens } else { 0 }
        completion_tokens = if ($usage) { $usage.completion_tokens } else { 0 }
        started_at = $started.ToString("s")
        finished_at = (Get-Date).ToString("s")
    }
    $status | ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding UTF8
    if (-not $compileOk) { throw "XeLaTeX compile failed: $paperId" }
    Write-Output "COMPLETE $paperId questions=$($status.question_count) review=$($status.review_count)"
}
catch {
    $failure = [pscustomobject]@{
        paper_id = $paperId
        title = $row.Title
        status = "failed"
        error = $_.Exception.Message
        started_at = $started.ToString("s")
        finished_at = (Get-Date).ToString("s")
    }
    $failure | ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding UTF8
    throw
}
