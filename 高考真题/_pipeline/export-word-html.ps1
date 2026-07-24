param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject KWPS.Application
$word.Visible = $false

try {
    $inputFull = [System.IO.Path]::GetFullPath($InputPath)
    $outputFull = [System.IO.Path]::GetFullPath($OutputPath)
    $document = $word.Documents.Open($inputFull)
    try {
        # 10 is wdFormatFilteredHTML. WPS/Word also writes a sibling asset directory.
        try {
            $document.SaveAs2($outputFull, 10)
        }
        catch {
            $document.SaveAs($outputFull, 10)
        }
    }
    finally {
        $document.Close($false)
    }
}
finally {
    $word.Quit()
}
