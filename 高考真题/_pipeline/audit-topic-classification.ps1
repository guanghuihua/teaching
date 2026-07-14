param(
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$Model = 'deepseek-v4-flash',
    [int]$BatchSize = 80
)

$ErrorActionPreference = 'Stop'
if (-not $env:DEEPSEEK_API_KEY) { throw 'DEEPSEEK_API_KEY is not set.' }
$OutputDirectory = [IO.Path]::GetFullPath($OutputDirectory)
$inventory = Get-Content -LiteralPath (Join-Path $OutputDirectory 'question-inventory.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$selected = Get-Content -LiteralPath (Join-Path $OutputDirectory 'topic-classification.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$selectedIds = @{}; foreach ($item in $selected) { $selectedIds[$item.id] = $true }
$pattern = '\\(?:sin|cos|tan|cot|vec|overrightarrow)|三角函数|正弦定理|余弦定理|向量|数量积|\\triangle|\\boldsymbol\{[abcuv]\}'
$candidates = @($inventory | Where-Object {
    -not $selectedIds.ContainsKey($_.id) -and (($_.stem + ' ' + ($_.choices -join ' ')) -match $pattern)
})

$systemPrompt = @'
你负责复核高中数学专题分类的漏项。候选题在首轮未入选，但命中了三角函数、三角形或向量关键词。请重新判断：
- 三角函数：只要三角函数的图象、性质、恒等变换、求导、零点、不等式、最值或周期是解题核心，即使与导数综合，也应标记“三角函数”。象限角和三角函数值也应纳入。仅用 sin/cos 写圆锥曲线参数方程、而题目核心是参数方程或解析几何的，不纳入。
- 三角形：正弦定理、余弦定理、三角形面积、边角关系或解三角形是核心才纳入。立体几何、圆锥曲线、球体中只出现三角形名称的不纳入。
- 向量：向量概念、运算、数量积、坐标、共线垂直或向量方法是核心才纳入。解析几何中只用向量写点的线性关系的不纳入。
一题可有多个标签。只输出应补入的题目，JSON 格式为 {"items":[{"id":"原id","tags":["三角形","三角函数","向量"],"reason":"一句话"}]}。
'@

$headers = @{ Authorization = "Bearer $($env:DEEPSEEK_API_KEY)"; 'Content-Type'='application/json' }
$added = [Collections.Generic.List[object]]::new()
$usageRows = [Collections.Generic.List[object]]::new()
$batchCount = [math]::Ceiling($candidates.Count / [double]$BatchSize)
for ($batchIndex=0; $batchIndex -lt $batchCount; $batchIndex++) {
    $start=$batchIndex*$BatchSize; $end=[math]::Min($start+$BatchSize-1,$candidates.Count-1)
    $batch=@($candidates[$start..$end] | ForEach-Object {[pscustomobject]@{id=$_.id;year=$_.year;paper=$_.paper_id;number=$_.number;stem=$_.stem;choices=$_.choices}})
    $valid=@{};foreach($q in $batch){$valid[$q.id]=$true}
    $body=@{model=$Model;messages=@(@{role='system';content=$systemPrompt},@{role='user';content=($batch|ConvertTo-Json -Depth 8 -Compress)});response_format=@{type='json_object'};thinking=@{type='disabled'};temperature=0;max_tokens=16000;stream=$false}|ConvertTo-Json -Depth 12
    Write-Output "AUDIT $($batchIndex+1)/$batchCount questions=$($batch.Count)"
    $response=Invoke-RestMethod -Uri 'https://api.deepseek.com/chat/completions' -Method Post -Headers $headers -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 900
    $content=$response.choices[0].message.content
    if($content -match 'Ã|å|æ|ç|è'){$latin1=[Text.Encoding]::GetEncoding(28591);$content=[Text.Encoding]::UTF8.GetString($latin1.GetBytes($content))}
    $parsed=$content|ConvertFrom-Json
    foreach($item in @($parsed.items)){
        if(-not $valid.ContainsKey([string]$item.id)){continue}
        $tags=@($item.tags|?{$_ -in @('三角形','三角函数','向量')}|Select -Unique)
        if($tags.Count){$added.Add([pscustomobject]@{id=[string]$item.id;tags=$tags;reason=[string]$item.reason})}
    }
    $usageRows.Add([pscustomobject]@{prompt_tokens=[long]$response.usage.prompt_tokens;completion_tokens=[long]$response.usage.completion_tokens;cached_tokens=[long]$response.usage.prompt_cache_hit_tokens})
}

$inventoryById=@{};foreach($q in $inventory){$inventoryById[$q.id]=$q}
$mergedRaw=@($selected)+@($added|%{$q=$inventoryById[$_.id];[pscustomobject]@{id=$q.id;year=$q.year;paper_id=$q.paper_id;paper_title=$q.paper_title;number=$q.number;type=$q.type;tags=$_.tags;reason=$_.reason;source_json=$q.source_json;source_directory=$q.source_directory}})
$merged=@($mergedRaw|Group id|%{$first=$_.Group[0];[pscustomobject]@{id=$first.id;year=$first.year;paper_id=$first.paper_id;paper_title=$first.paper_title;number=$first.number;type=$first.type;tags=@($_.Group.tags|%{$_}|Select -Unique);reason=($_.Group.reason|Select -First 1);source_json=$first.source_json;source_directory=$first.source_directory}}|Sort year,paper_id,number)
$merged|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $OutputDirectory 'topic-classification.json') -Encoding UTF8
$added|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $OutputDirectory 'audit-added.json') -Encoding UTF8
$priorUsage=Get-Content -LiteralPath (Join-Path $OutputDirectory 'classification-usage.json') -Raw -Encoding UTF8|ConvertFrom-Json
$usage=[pscustomobject]@{model=$Model;initial_selected=[int]$priorUsage.selected_questions;audit_candidates=$candidates.Count;audit_added=$added.Count;selected_questions=$merged.Count;prompt_tokens=[long]$priorUsage.prompt_tokens+($usageRows|Measure prompt_tokens -Sum).Sum;completion_tokens=[long]$priorUsage.completion_tokens+($usageRows|Measure completion_tokens -Sum).Sum;cached_tokens=[long]$priorUsage.cached_tokens+($usageRows|Measure cached_tokens -Sum).Sum}
$usage|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $OutputDirectory 'classification-usage.json') -Encoding UTF8
Write-Output "AUDIT_ADDED $($added.Count) TOTAL $($merged.Count)"
