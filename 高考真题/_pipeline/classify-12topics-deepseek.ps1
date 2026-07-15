param(
    [Parameter(Mandatory=$true)][string]$InventoryPath,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [string]$Model='deepseek-v4-flash',
    [int]$BatchSize=80
)

$ErrorActionPreference='Stop'
if(-not $env:DEEPSEEK_API_KEY){throw 'DEEPSEEK_API_KEY is not set.'}
$InventoryPath=[IO.Path]::GetFullPath($InventoryPath)
$OutputDirectory=[IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Path $OutputDirectory -Force|Out-Null
$rawInventory=Get-Content -LiteralPath $InventoryPath -Raw -Encoding UTF8|ConvertFrom-Json
$seenIds=@{};$normalized=[Collections.Generic.List[object]]::new()
foreach($q in $rawInventory){
    $baseId=[string]$q.id
    if(-not $seenIds.ContainsKey($baseId)){$seenIds[$baseId]=0}
    $seenIds[$baseId]++
    $normalized.Add([pscustomobject]@{uid="$baseId::occ$($seenIds[$baseId])";original_id=$baseId;occurrence=$seenIds[$baseId];year=$q.year;paper_id=$q.paper_id;paper_title=$q.paper_title;number=$q.number;type=$q.type;stem=$q.stem;choices=$q.choices;source_json=$q.source_json;source_directory=$q.source_directory})
}
$inventory=@($normalized)
$topics=@(
    '集合与逻辑',
    '一元二次函数、方程和不等式',
    '函数',
    '三角函数',
    '平面向量与解三角形',
    '复数',
    '立体几何',
    '平面解析几何',
    '数列',
    '导数',
    '计数原理',
    '统计与概率'
)

$systemPrompt=@'
你是中国高中数学高考真题题库编辑。必须把每道题分类到下面 12 个专题之一，并可标记 0--3 个次专题：
1. 集合与逻辑：集合运算、命题、充分必要条件、量词、逻辑联结词。
2. 一元二次函数、方程和不等式：一元二次式、方程、不等式、基本不等式、线性规划、绝对值不等式及其他不等式基础。
3. 函数：函数概念、定义域值域、奇偶性、单调性、周期性、图象、零点、指数函数、对数函数、幂函数、函数模型；导数或三角函数是核心时不归此类。
4. 三角函数：任意角、三角函数、恒等变换、图象性质、三角方程、最值与周期；以导数证明为核心时主类归导数。
5. 平面向量与解三角形：平面向量概念运算、数量积、坐标表示，以及正弦定理、余弦定理、三角形面积和边角关系。空间向量主类归立体几何。
6. 复数：复数概念、运算、几何意义。
7. 立体几何：空间点线面关系、空间角与距离、空间向量、柱锥台球、立体体积表面积。
8. 平面解析几何：直线、圆、圆锥曲线、轨迹、极坐标与参数方程、几何证明选讲中的平面几何。
9. 数列：等差等比数列、递推数列、数列求和、数学归纳法及数列综合。
10. 导数：导数定义与运算、切线、单调性、极值最值、恒成立与不等式证明中以导数为主的方法。
11. 计数原理：排列组合、二项式定理、计数方法。
12. 统计与概率：概率、随机变量、分布列、期望方差、统计图表、抽样、回归、独立性检验、条件概率。

归类规则：
- 每题必须且只能有一个 primary_topic，不能遗漏。
- secondary_topics 只在综合题中填写，不能重复主专题。
- 按核心设问和主要解法定主类，不按偶然出现的符号分类。
- 圆锥曲线中使用向量，主类仍为平面解析几何；空间向量归立体几何。
- 三角函数与导数综合，若主要任务是求导、单调性、极值或导数证明，主类归导数。
- 数列、概率、解析几何等专题中的不等式只是工具时，不归不等式主类。
- 必须原样返回每个 id。

严格输出 JSON：{"items":[{"id":"原id","primary_topic":"十二个专题之一","secondary_topics":["专题"],"reason":"一句话说明主专题依据"}]}。
'@

$headers=@{Authorization="Bearer $($env:DEEPSEEK_API_KEY)";'Content-Type'='application/json'}
$results=[Collections.Generic.List[object]]::new();$usageRows=[Collections.Generic.List[object]]::new()
$batchCount=[math]::Ceiling($inventory.Count/[double]$BatchSize)
for($batchIndex=0;$batchIndex -lt $batchCount;$batchIndex++){
    $start=$batchIndex*$BatchSize;$end=[math]::Min($start+$BatchSize-1,$inventory.Count-1)
    $batch=@($inventory[$start..$end])
    $pending=@{};foreach($q in $batch){$pending[$q.uid]=$q}
    for($round=1;$round -le 4 -and $pending.Count -gt 0;$round++){
        $requestItems=@($pending.Values|%{[pscustomobject]@{id=$_.uid;year=$_.year;paper=$_.paper_id;number=$_.number;type=$_.type;stem=$_.stem;choices=$_.choices}})
        $body=@{model=$Model;messages=@(@{role='system';content=$systemPrompt},@{role='user';content=("请分类以下全部题目，不得漏项：`n"+($requestItems|ConvertTo-Json -Depth 8 -Compress))});response_format=@{type='json_object'};thinking=@{type='disabled'};temperature=0;max_tokens=20000;stream=$false}|ConvertTo-Json -Depth 12
        Write-Output "CLASSIFY $($batchIndex+1)/$batchCount round=$round pending=$($pending.Count)"
        $response=$null;$lastError=$null
        for($attempt=1;$attempt -le 3;$attempt++){
            try{$response=Invoke-RestMethod -Uri 'https://api.deepseek.com/chat/completions' -Method Post -Headers $headers -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 900;$lastError=$null;break}catch{$lastError=$_;if($attempt-lt3){Start-Sleep -Seconds(5*$attempt)}}
        }
        if($lastError){throw $lastError}
        $content=$response.choices[0].message.content
        if($content-match'Ã|å|æ|ç|è'){$latin1=[Text.Encoding]::GetEncoding(28591);$content=[Text.Encoding]::UTF8.GetString($latin1.GetBytes($content))}
        $parsed=$content|ConvertFrom-Json
        foreach($item in @($parsed.items)){
            $id=[string]$item.id;if(-not $pending.ContainsKey($id)){continue}
            $primary=[string]$item.primary_topic;if($primary -notin $topics){continue}
            $secondary=@($item.secondary_topics|?{$_ -in $topics -and $_ -ne $primary}|Select -Unique)
            $q=$pending[$id]
            $results.Add([pscustomobject]@{id=$id;original_id=$q.original_id;occurrence=$q.occurrence;year=$q.year;paper_id=$q.paper_id;paper_title=$q.paper_title;number=$q.number;type=$q.type;primary_topic=$primary;secondary_topics=$secondary;reason=[string]$item.reason;source_json=$q.source_json;source_directory=$q.source_directory})
            $pending.Remove($id)
        }
        $usageRows.Add([pscustomobject]@{prompt_tokens=[long]$response.usage.prompt_tokens;completion_tokens=[long]$response.usage.completion_tokens;cached_tokens=[long]$response.usage.prompt_cache_hit_tokens})
    }
    if($pending.Count -gt 0){throw "DeepSeek omitted $($pending.Count) questions in batch $($batchIndex+1): $($pending.Keys -join ', ')"}
    @($results)|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $OutputDirectory 'classification-12topics.partial.json') -Encoding UTF8
}

$final=@($results|Sort-Object year,paper_id,number)
if($final.Count-ne$inventory.Count){throw "Coverage mismatch: classified=$($final.Count), inventory=$($inventory.Count)"}
if(@($final.id|Group-Object|? Count -ne 1).Count){throw 'Duplicate classification ids found.'}
$final|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $OutputDirectory 'classification-12topics.json') -Encoding UTF8
$usage=[pscustomobject]@{model=$Model;questions=$final.Count;requests=$usageRows.Count;prompt_tokens=($usageRows|Measure prompt_tokens -Sum).Sum;completion_tokens=($usageRows|Measure completion_tokens -Sum).Sum;cached_tokens=($usageRows|Measure cached_tokens -Sum).Sum;generated_at=(Get-Date).ToString('s')}
$usage|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $OutputDirectory 'classification-usage.json') -Encoding UTF8
Write-Output "COMPLETE questions=$($final.Count) requests=$($usageRows.Count)"
