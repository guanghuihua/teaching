param([Parameter(Mandatory = $true)][string]$OutputDirectory)

$ErrorActionPreference='Stop'
$OutputDirectory=[IO.Path]::GetFullPath($OutputDirectory)
$inventory=Get-Content -LiteralPath (Join-Path $OutputDirectory 'question-inventory.json') -Raw -Encoding UTF8|ConvertFrom-Json
$selected=Get-Content -LiteralPath (Join-Path $OutputDirectory 'topic-classification.json') -Raw -Encoding UTF8|ConvertFrom-Json
$byId=@{};foreach($item in $selected){$byId[$item.id]=$item}
$supplements=[Collections.Generic.List[object]]::new()

foreach($q in $inventory){
    $text=$q.stem+' '+($q.choices -join ' ')
    $tags=[Collections.Generic.List[string]]::new()

    $hasTrig=$text -match '\\(?:sin|cos|tan|cot)(?![A-Za-z])|三角函数|正弦函数|余弦函数|正切函数|象限角'
    $isPureCoordinate=$text -match '参数方程|极坐标|极轴|\\rho' -and $text -notmatch '三角函数|周期|单调|最值|图象|零点|不等式|恒等|求值'
    if($hasTrig -and -not $isPureCoordinate){$tags.Add('三角函数')}

    if($text -match '向量|数量积|\\vec\{|\\overrightarrow\{|\\boldsymbol\{[a-zA-Z]'){ $tags.Add('向量') }

    $triangleCore=$text -match '正弦定理|余弦定理|解三角形|在\s*\$?\\triangle\s*[A-Z]{3}|在三角形\s*[A-Z]{3}|三角形的三边|三角形.*内角'
    $solidContext=$text -match '三棱锥|四棱锥|棱柱|四面体|球面|球的|圆锥|折起|折叠|平面.*(?:垂直|平行)'
    if($triangleCore -and -not $solidContext){$tags.Add('三角形')}

    $tags=@($tags|Select-Object -Unique)
    if($isPureCoordinate -and $byId.ContainsKey($q.id)){
        $byId[$q.id].tags=@($byId[$q.id].tags|Where-Object {$_ -ne '三角函数'})
    }
    if($tags.Count -eq 0){continue}
    if($byId.ContainsKey($q.id)){
        $item=$byId[$q.id]
        $newTags=@($item.tags)+$tags|Select-Object -Unique
        $item.tags=@($newTags)
    }else{
        $item=[pscustomobject]@{id=$q.id;year=$q.year;paper_id=$q.paper_id;paper_title=$q.paper_title;number=$q.number;type=$q.type;tags=$tags;reason='强规则兜底：题干直接命中专题核心符号或术语。';source_json=$q.source_json;source_directory=$q.source_directory}
        $byId[$q.id]=$item
        $supplements.Add($item)
    }

}

$merged=@($byId.Values|Where-Object {@($_.tags).Count -gt 0}|Sort-Object year,paper_id,number)
$merged|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $OutputDirectory 'topic-classification.json') -Encoding UTF8
$supplements|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $OutputDirectory 'rule-supplements.json') -Encoding UTF8
Write-Output "RULE_ADDED $($supplements.Count) TOTAL $($merged.Count)"
