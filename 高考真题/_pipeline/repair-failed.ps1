param(
    [Parameter(Mandatory = $true)][string]$OutputRoot,
    [Parameter(Mandatory = $true)][string]$WorkRoot
)

$ErrorActionPreference = "Continue"
$OutputRoot = [IO.Path]::GetFullPath($OutputRoot)
$WorkRoot = [IO.Path]::GetFullPath($WorkRoot)
$pipeline = $PSScriptRoot
New-Item -ItemType Directory -Path $WorkRoot -Force | Out-Null

$statuses = @(Get-ChildItem -LiteralPath $OutputRoot -Recurse -Filter status.json | Where-Object {
    try { (Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json).status -ne "complete" }
    catch { $false }
} | Sort-Object FullName)

$counter = 0
foreach ($statusFile in $statuses) {
    $counter++
    $directory = $statusFile.DirectoryName
    $status = Get-Content -LiteralPath $statusFile.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    $paperId = $status.paper_id
    $jsonPath = Join-Path $directory "questions.json"
    $originalPdf = Join-Path $directory "source-original.pdf"
    $workDirectory = Join-Path $WorkRoot ("repair-{0:D3}" -f $counter)
    if (Test-Path -LiteralPath $workDirectory) { Remove-Item -LiteralPath $workDirectory -Recurse -Force }
    New-Item -ItemType Directory -Path $workDirectory -Force | Out-Null
    $started = Get-Date

    Write-Output "REPAIR $counter/$($statuses.Count) $paperId"
    try {
        if (-not (Test-Path -LiteralPath $jsonPath)) { throw "questions.json is missing" }
        if (-not (Test-Path -LiteralPath $originalPdf)) { throw "source-original.pdf is missing" }

        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pipeline "map-assets.ps1") `
            -JsonPath $jsonPath -OriginalPdf $originalPdf -OutputDirectory $directory -WorkDirectory $workDirectory
        if ($LASTEXITCODE -ne 0) { throw "Asset mapping failed" }

        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $pipeline "render-examzh.ps1") `
            -JsonPath $jsonPath -OutputDirectory $directory -BaseName $paperId
        if ($LASTEXITCODE -ne 0) { throw "exam-zh rendering failed" }

        $compileOk = $true
        Push-Location $directory
        try {
            foreach ($variant in @("试卷版", "答案版")) {
                $texName = "$paperId-$variant.tex"
                $logPath = Join-Path $directory "$paperId-$variant.compile.txt"
                for ($pass = 1; $pass -le 2; $pass++) {
                    & xelatex -interaction=nonstopmode -halt-on-error $texName *> $logPath
                    if ($LASTEXITCODE -ne 0) { $compileOk = $false; break }
                }
            }
        }
        finally { Pop-Location }

        $data = Get-Content -LiteralPath $jsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $usagePath = [IO.Path]::ChangeExtension($jsonPath, ".usage.json")
        $usage = if (Test-Path -LiteralPath $usagePath) { Get-Content -LiteralPath $usagePath -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }
        $newStatus = [pscustomobject]@{
            paper_id = $paperId
            title = $data.title
            status = if ($compileOk) { "complete" } else { "compile_failed" }
            question_count = @($data.sections.questions).Count
            review_count = @($data.review_notes).Count
            prompt_tokens = if ($usage) { $usage.prompt_tokens } else { 0 }
            completion_tokens = if ($usage) { $usage.completion_tokens } else { 0 }
            started_at = $started.ToString("s")
            finished_at = (Get-Date).ToString("s")
        }
        $newStatus | ConvertTo-Json | Set-Content -LiteralPath $statusFile.FullName -Encoding UTF8
        if (-not $compileOk) { throw "XeLaTeX compile failed" }
        Write-Output "COMPLETE $paperId"
    }
    catch {
        $failure = [pscustomobject]@{
            paper_id = $paperId
            title = $status.title
            status = "failed"
            error = $_.Exception.Message
            started_at = $started.ToString("s")
            finished_at = (Get-Date).ToString("s")
        }
        $failure | ConvertTo-Json | Set-Content -LiteralPath $statusFile.FullName -Encoding UTF8
        Write-Warning "$paperId : $($_.Exception.Message)"
    }
}
