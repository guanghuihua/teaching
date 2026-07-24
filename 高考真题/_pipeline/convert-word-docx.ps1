param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = "Stop"
$app = $null
$doc = $null
try {
    $app = New-Object -ComObject KWPS.Application
    $app.Visible = $false
    $app.DisplayAlerts = 0
    $doc = $app.Documents.Open($InputPath, $false, $true, $false)
    try {
        $doc.SaveAs2($OutputPath, 16)
    }
    catch {
        $doc.SaveAs($OutputPath, 16)
    }
    $doc.Close(0)
    $doc = $null
}
finally {
    if ($doc) { try { $doc.Close(0) } catch {} }
    if ($app) {
        try { $app.Quit() } catch {}
        try { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($app) } catch {}
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

if (-not (Test-Path -LiteralPath $OutputPath)) {
    throw "WPS did not create DOCX: $OutputPath"
}
