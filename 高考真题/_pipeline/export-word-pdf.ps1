param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = "Stop"
$word = $null
$doc = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open($InputPath, $false, $true, $false)
    $doc.ExportAsFixedFormat($OutputPath, 17, $false, 0, 0, 1, 999, 0, $true, $true, 0, $true, $true, $false)
    $doc.Close(0)
    $doc = $null
}
finally {
    if ($doc) { try { $doc.Close(0) } catch {} }
    if ($word) {
        try { $word.Quit() } catch {}
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($word) } catch {}
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

if (-not (Test-Path -LiteralPath $OutputPath)) {
    throw "Word did not create PDF: $OutputPath"
}
