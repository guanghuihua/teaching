param(
    [Parameter(Mandatory = $true)][string]$SourceRoot,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$Model = 'deepseek-v4-flash',
    [int]$BatchSize = 100
)

$ErrorActionPreference = 'Stop'
if (-not $env:DEEPSEEK_API_KEY) { throw 'DEEPSEEK_API_KEY is not set.' }
$SourceRoot = [IO.Path]::GetFullPath($SourceRoot)
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

$questions = [Collections.Generic.List[object]]::new()
foreach ($jsonFile in @(Get-ChildItem -LiteralPath $SourceRoot -Recurse -Filter questions.json | Sort-Object FullName)) {
    $data = Get-Content -LiteralPath $jsonFile.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    $paperDirectory = $jsonFile.DirectoryName
    $paperId = Split-Path $paperDirectory -Leaf
    $year = [int](Split-Path (Split-Path $paperDirectory -Parent) -Leaf)
    foreach ($section in $data.sections) {
        foreach ($question in $section.questions) {
            $questions.Add([pscustomobject]@{
                id = "$paperId::$($question.number)"
                year = $year
                paper_id = $paperId
                paper_title = $data.title
                number = $question.number
                type = $question.type
                stem = $question.stem_latex
                choices = @($question.choices)
                source_json = $jsonFile.FullName
                source_directory = $paperDirectory
            })
        }
    }
}
$questions | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'question-inventory.json') -Encoding UTF8

$systemPrompt = @'
你是中国高中数学高考真题的专题分类编辑。任务是判断每道题是否以以下知识为核心考点：
1. 三角形：解三角形、正弦定理、余弦定理、三角形面积、边角关系等。普通解析几何或立体几何中仅偶然出现三角形，不归入此类。
2. 三角函数：三角函数定义、图象与性质、恒等变换、诱导公式、三角方程、不等式、最值与周期等。
3. 向量：平面向量或空间向量的概念、运算、数量积、坐标表示、共线垂直、向量方法等。仅在解析中偶然写了一个向量符号而核心是其他专题，不归入此类。

一题可以有多个标签。请宁可保留真正的综合题，但不要仅因为出现“角”“三角形”或图形名称就误收。只返回至少有一个标签的题目。
严格输出 JSON：{"items":[{"id":"原id","tags":["三角形","三角函数","向量"],"reason":"一句话说明核心考点"}]}。tags 只能使用给定的三个标签。
'@

$headers = @{ Authorization = "Bearer $($env:DEEPSEEK_API_KEY)"; 'Content-Type' = 'application/json' }
$allItems = [Collections.Generic.List[object]]::new()
$usageRows = [Collections.Generic.List[object]]::new()
$batchCount = [math]::Ceiling($questions.Count / [double]$BatchSize)

for ($batchIndex = 0; $batchIndex -lt $batchCount; $batchIndex++) {
    $start = $batchIndex * $BatchSize
    $end = [math]::Min($start + $BatchSize - 1, $questions.Count - 1)
    $batch = @($questions[$start..$end] | ForEach-Object {
        [pscustomobject]@{ id=$_.id; year=$_.year; paper=$_.paper_id; number=$_.number; stem=$_.stem; choices=$_.choices }
    })
    $validIds = @{}; foreach ($item in $batch) { $validIds[$item.id] = $true }
    $body = @{
        model = $Model
        messages = @(
            @{ role='system'; content=$systemPrompt }
            @{ role='user'; content=("请分类以下题目：`n" + ($batch | ConvertTo-Json -Depth 8 -Compress)) }
        )
        response_format = @{ type='json_object' }
        thinking = @{ type='disabled' }
        temperature = 0
        max_tokens = 20000
        stream = $false
    } | ConvertTo-Json -Depth 12

    Write-Output "CLASSIFY $($batchIndex + 1)/$batchCount questions=$($batch.Count)"
    $lastError = $null
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            $response = Invoke-RestMethod -Uri 'https://api.deepseek.com/chat/completions' -Method Post -Headers $headers -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 900
            $content = $response.choices[0].message.content
            if ($content -match 'Ã|å|æ|ç|è') {
                $latin1 = [Text.Encoding]::GetEncoding(28591)
                $content = [Text.Encoding]::UTF8.GetString($latin1.GetBytes($content))
            }
            $parsed = $content | ConvertFrom-Json
            foreach ($item in @($parsed.items)) {
                if (-not $validIds.ContainsKey([string]$item.id)) { continue }
                $tags = @($item.tags | Where-Object { $_ -in @('三角形','三角函数','向量') } | Select-Object -Unique)
                if ($tags.Count -eq 0) { continue }
                $allItems.Add([pscustomobject]@{ id=[string]$item.id; tags=$tags; reason=[string]$item.reason })
            }
            $usageRows.Add([pscustomobject]@{
                batch = $batchIndex + 1
                prompt_tokens = [long]$response.usage.prompt_tokens
                completion_tokens = [long]$response.usage.completion_tokens
                cached_tokens = [long]$response.usage.prompt_cache_hit_tokens
            })
            $lastError = $null
            break
        }
        catch {
            $lastError = $_
            if ($attempt -lt 3) { Start-Sleep -Seconds (5 * $attempt) }
        }
    }
    if ($lastError) { throw $lastError }
}

$byId = @{}; foreach ($q in $questions) { $byId[$q.id] = $q }
$selected = @($allItems | Group-Object id | ForEach-Object {
    $classification = $_.Group[0]
    $q = $byId[$_.Name]
    [pscustomobject]@{
        id = $q.id
        year = $q.year
        paper_id = $q.paper_id
        paper_title = $q.paper_title
        number = $q.number
        type = $q.type
        tags = @($_.Group.tags | ForEach-Object { $_ } | Select-Object -Unique)
        reason = ($_.Group.reason | Select-Object -First 1)
        source_json = $q.source_json
        source_directory = $q.source_directory
    }
} | Sort-Object year,paper_id,number)

$selected | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'topic-classification.json') -Encoding UTF8
$usage = [pscustomobject]@{
    model = $Model
    batches = $usageRows.Count
    prompt_tokens = ($usageRows | Measure-Object prompt_tokens -Sum).Sum
    completion_tokens = ($usageRows | Measure-Object completion_tokens -Sum).Sum
    cached_tokens = ($usageRows | Measure-Object cached_tokens -Sum).Sum
    selected_questions = $selected.Count
}
$usage | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputDirectory 'classification-usage.json') -Encoding UTF8
Write-Output "SELECTED $($selected.Count)/$($questions.Count)"
