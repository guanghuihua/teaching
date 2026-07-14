param(
    [string]$SourceRoot = (Join-Path $PSScriptRoot ".."),
    [string]$OutputPath = (Join-Path $PSScriptRoot "manifest-2016-2025.csv")
)

$ErrorActionPreference = "Stop"

function Get-PaperName {
    param([int]$Year, [string]$Name)

    $stream = ""
    if ($Name -match "文科|数学（文）|数学\(文\)|数学\（文") { $stream = "文科" }
    elseif ($Name -match "理科|数学（理）|数学\(理\)|数学\（理") { $stream = "理科" }

    $paper = $null
    if ($Name -match "北京") { $paper = "北京卷" }
    elseif ($Name -match "上海.*春") { $paper = "上海春季卷" }
    elseif ($Name -match "上海") { $paper = "上海卷" }
    elseif ($Name -match "天津") { $paper = "天津卷" }
    elseif ($Name -match "浙江") { $paper = "浙江卷" }
    elseif ($Year -ge 2021 -and $Name -match "新(?:高考|课标).*?(?:Ⅱ|ⅱ|II|2|二)") { $paper = "新高考II卷" }
    elseif ($Year -ge 2021 -and $Name -match "新(?:高考|课标).*?(?:Ⅰ|ⅰ|(?<!I)I(?!I)|1|一)") { $paper = "新高考I卷" }
    elseif ($Name -match "全国.*?(?:甲)") { $paper = "全国甲卷" }
    elseif ($Name -match "全国.*?(?:乙)") { $paper = "全国乙卷" }
    elseif ($Name -match "(?:全国|新课标).*?(?:Ⅲ|ⅲ|III|3|三)") { $paper = "全国III卷" }
    elseif ($Name -match "(?:全国|新课标).*?(?:Ⅱ|ⅱ|II|2|二)") { $paper = "全国II卷" }
    elseif ($Name -match "(?:全国|新课标).*?(?:Ⅰ|ⅰ|(?<!I)I(?!I)|1|一)") { $paper = "全国I卷" }

    if (-not $paper) { return $null }
    if ($stream) { return "$paper-$stream" }
    return $paper
}

$sourceFiles = Get-ChildItem -LiteralPath $SourceRoot -Recurse -File | Where-Object {
    $_.Extension -in ".doc", ".docx", ".pdf" -and
    $_.FullName -notmatch "exam-zh-converted|deepseek-examzh-pilot|\\_pipeline\\|\\exam-zh-2016-2025\\" -and
    $_.Name -match "20(1[6-9]|2[0-5])" -and
    $_.Name -notmatch "A3"
}

$classified = foreach ($file in $sourceFiles) {
    $yearMatch = [regex]::Match($file.Name, "20(1[6-9]|2[0-5])")
    if (-not $yearMatch.Success) { continue }
    $year = [int]$yearMatch.Value
    $paper = Get-PaperName -Year $year -Name $file.Name
    [pscustomobject]@{
        Year = $year
        Paper = $paper
        Path = $file.FullName
        Name = $file.Name
        Extension = $file.Extension
    }
}

$unresolved = $classified | Where-Object { -not $_.Paper }
if ($unresolved) {
    $unresolved | Export-Csv -LiteralPath ([IO.Path]::ChangeExtension($OutputPath, ".unresolved.csv")) -NoTypeInformation -Encoding UTF8
}

$manifest = foreach ($group in ($classified | Where-Object Paper | Group-Object Year, Paper)) {
    $items = @($group.Group)
    $year = $items[0].Year
    $paper = $items[0].Paper

    $original = $items | Sort-Object @{Expression={
        if ($_.Name -match "原卷") { 0 }
        elseif ($_.Name -match "含答案|答案版") { 1 }
        elseif ($_.Name -match "解析|含解析") { 3 }
        else { 2 }
    }}, @{Expression="Name"} | Select-Object -First 1

    $solution = $items | Sort-Object @{Expression={
        if ($_.Name -match "解析|含解析") { 0 }
        elseif ($_.Name -match "答案版|含答案") { 1 }
        else { 2 }
    }}, @{Expression="Name"} | Select-Object -First 1

    [pscustomobject]@{
        Year = $year
        PaperId = "$year-$paper"
        Title = "$year 年高考数学 $paper"
        OriginalPath = $original.Path
        SolutionPath = $solution.Path
        CandidateCount = $items.Count
        Status = "pending"
    }
}

$manifest | Sort-Object Year, PaperId | Export-Csv -LiteralPath $OutputPath -NoTypeInformation -Encoding UTF8
$manifest | Sort-Object Year, PaperId
