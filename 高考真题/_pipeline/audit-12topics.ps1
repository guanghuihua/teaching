param(
    [Parameter(Mandatory=$true)][string]$InventoryPath,
    [Parameter(Mandatory=$true)][string]$ClassificationPath
)

$ErrorActionPreference='Stop'
$inventory=Get-Content -LiteralPath $InventoryPath -Raw -Encoding UTF8|ConvertFrom-Json
$classification=Get-Content -LiteralPath $ClassificationPath -Raw -Encoding UTF8|ConvertFrom-Json
$seen=@{};$textById=@{}
foreach($q in $inventory){
    if(-not $seen.ContainsKey($q.id)){$seen[$q.id]=0};$seen[$q.id]++
    $textById["$($q.id)::occ$($seen[$q.id])"]=$q.stem+' '+($q.choices -join ' ')
}
$corrections=[Collections.Generic.List[object]]::new()
foreach($item in $classification){
    $text=$textById[$item.id]
    if($item.primary_topic -eq '计数原理' -and $text -match '概率|随机抽样'){
        $old=$item.primary_topic
        $item.primary_topic='统计与概率'
        $item.secondary_topics=@(@($item.secondary_topics)+$old|Select-Object -Unique)
        $corrections.Add([pscustomobject]@{Id=$item.id;From=$old;To=$item.primary_topic;Reason='题目直接求概率或涉及随机抽样，按用户专题口径归入统计与概率。'})
    }
    if($text -match '导函数|f\s*''\s*\(' -and $item.primary_topic -eq '函数' -and $item.secondary_topics -notcontains '导数'){
        $item.secondary_topics=@(@($item.secondary_topics)+'导数'|Select-Object -Unique)
        $corrections.Add([pscustomobject]@{Id=$item.id;From='函数';To='函数（次专题：导数）';Reason='函数性质题中明确使用导函数，补充导数次专题标签。'})
    }
}
$classification|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $ClassificationPath -Encoding UTF8
$corrections|Export-Csv -LiteralPath (Join-Path (Split-Path $ClassificationPath -Parent) 'classification-corrections.csv') -NoTypeInformation -Encoding UTF8
Write-Output "CORRECTIONS $($corrections.Count)"
