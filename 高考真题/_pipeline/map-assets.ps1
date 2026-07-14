param(
    [Parameter(Mandatory = $true)][string]$JsonPath,
    [Parameter(Mandatory = $true)][string]$OriginalPdf,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][string]$WorkDirectory
)

$ErrorActionPreference = "Stop"
$assetWork = Join-Path $WorkDirectory "pdf-assets"
if (Test-Path -LiteralPath $assetWork) { Remove-Item -LiteralPath $assetWork -Recurse -Force }
New-Item -ItemType Directory -Path $assetWork | Out-Null
$xmlPath = Join-Path $assetWork "document.xml"
pdftohtml -xml -hidden -nodrm $OriginalPdf $xmlPath | Out-Null

$images = [Collections.Generic.List[object]]::new()
$page = 0
foreach ($line in (Get-Content -LiteralPath $xmlPath -Encoding UTF8)) {
    if ($line -match '<page number="(\d+)"') {
        $page = [int]$matches[1]
    }
    elseif ($line -match '<image[^>]*width="(\d+)"[^>]*height="(\d+)"[^>]*src="([^"]+)"') {
        $width = [int]$matches[1]
        $height = [int]$matches[2]
        if ($width -ge 80 -and $height -ge 60 -and ($width * $height) -le 1200000) {
            $images.Add([pscustomobject]@{
                Page = $page
                Width = $width
                Height = $height
                Source = $matches[3]
                Used = $false
            })
        }
    }
}

$data = Get-Content -LiteralPath $JsonPath -Raw -Encoding UTF8 | ConvertFrom-Json
$review = [Collections.Generic.List[object]]::new()
foreach ($existing in @($data.review_notes)) { $review.Add($existing) }

foreach ($question in @($data.sections.questions)) {
    $assetIndex = 0
    foreach ($asset in @($question.assets)) {
        $assetIndex++
        $pageMatch = [regex]::Match("$($asset.source_page)", "\d+")
        if (-not $pageMatch.Success) {
            $review.Add([pscustomobject]@{
                question = $question.number
                issue = "题图页码无法识别：$($asset.source_page)，$($asset.description)"
            })
            continue
        }
        $sourcePage = [int]$pageMatch.Value
        $candidate = $images | Where-Object { -not $_.Used -and $_.Page -eq $sourcePage } | Select-Object -First 1
        if (-not $candidate) {
            $review.Add([pscustomobject]@{
                question = $question.number
                issue = "题图未能自动匹配：原卷第 $sourcePage 页，$($asset.description)"
            })
            continue
        }

        $candidate.Used = $true
        $extension = [IO.Path]::GetExtension($candidate.Source).ToLowerInvariant()
        if (-not $extension) { $extension = ".png" }
        $fileName = "question-$($question.number)-$assetIndex$extension"
        Copy-Item -LiteralPath $candidate.Source -Destination (Join-Path $OutputDirectory $fileName) -Force
        $asset | Add-Member -NotePropertyName file -NotePropertyValue $fileName -Force
    }
}

$data.review_notes = @($review)
$data | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $JsonPath -Encoding UTF8
