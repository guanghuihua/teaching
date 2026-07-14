param(
    [string]$ManifestPath = (Join-Path $PSScriptRoot "manifest-2016-2025.csv"),
    [string]$OutputRoot = (Join-Path (Join-Path $PSScriptRoot "..") "exam-zh-2016-2025"),
    [string]$WorkRoot = (Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) "_gaokao_batch_work"),
    [int]$StartIndex = 0,
    [int]$EndIndex = -1
)

$ErrorActionPreference = "Continue"
$rows = @(Import-Csv -LiteralPath $ManifestPath)
if ($EndIndex -lt 0 -or $EndIndex -ge $rows.Count) { $EndIndex = $rows.Count - 1 }
New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null
New-Item -ItemType Directory -Path $WorkRoot -Force | Out-Null
$runLog = Join-Path $OutputRoot "batch-run.log"

for ($index = $StartIndex; $index -le $EndIndex; $index++) {
    $paperId = $rows[$index].PaperId
    $message = "[$(Get-Date -Format s)] START $index/$EndIndex $paperId"
    Add-Content -LiteralPath $runLog -Value $message -Encoding UTF8
    Write-Output $message
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "process-one.ps1") -ManifestPath $ManifestPath -Index $index -OutputRoot $OutputRoot -WorkRoot $WorkRoot 2>&1 | Tee-Object -FilePath $runLog -Append
        if ($LASTEXITCODE -ne 0) { throw "process-one exit code $LASTEXITCODE" }
    }
    catch {
        $errorMessage = "[$(Get-Date -Format s)] FAILED $paperId $($_.Exception.Message)"
        Add-Content -LiteralPath $runLog -Value $errorMessage -Encoding UTF8
        Write-Output $errorMessage
    }
}

$statuses = Get-ChildItem -LiteralPath $OutputRoot -Recurse -File -Filter "status.json" | ForEach-Object {
    Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
}
$statuses | Export-Csv -LiteralPath (Join-Path $OutputRoot "batch-summary.csv") -NoTypeInformation -Encoding UTF8
