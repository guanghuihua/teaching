param(
    [Parameter(Mandatory = $true)][string]$PdfPath,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$ErrorActionPreference = "Stop"
$pageLine = pdfinfo $PdfPath | Select-String "^Pages:"
if (-not $pageLine) { throw "Cannot determine PDF page count: $PdfPath" }
$pages = [int](($pageLine.Line -split ":")[1].Trim())
$parts = [Collections.Generic.List[string]]::new()
$temp = [IO.Path]::GetTempFileName()
try {
    for ($page = 1; $page -le $pages; $page++) {
        pdftotext -f $page -l $page -layout -enc UTF-8 $PdfPath $temp
        $parts.Add("===== PAGE $page =====")
        $parts.Add((Get-Content -LiteralPath $temp -Raw -Encoding UTF8))
    }
}
finally {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
}
$parts | Set-Content -LiteralPath $OutputPath -Encoding UTF8
