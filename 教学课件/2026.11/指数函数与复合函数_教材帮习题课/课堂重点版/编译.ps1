$ErrorActionPreference='Stop'
$focusDir=Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location -LiteralPath $focusDir
try {
    New-Item -ItemType Directory -Path 'build/slide','build/handout' -Force | Out-Null
    for ($pass=1; $pass -le 2; $pass++) {
        & xelatex -interaction=nonstopmode -halt-on-error -output-directory=build/slide '复合函数单调性_课堂重点版.tex' | Out-File -LiteralPath 'build/slide/console.txt' -Encoding utf8
        if ($LASTEXITCODE -ne 0) { throw '分步版编译失败，请检查 build/slide/console.txt' }
    }
    for ($pass=1; $pass -le 2; $pass++) {
        & xelatex -interaction=nonstopmode -halt-on-error -jobname=handout -output-directory=build/handout '\def\PrintVersion{1}\input{复合函数单调性_课堂重点版.tex}' | Out-File -LiteralPath 'build/handout/console.txt' -Encoding utf8
        if ($LASTEXITCODE -ne 0) { throw '静态版编译失败，请检查 build/handout/console.txt' }
    }
    Copy-Item -LiteralPath 'build/slide/复合函数单调性_课堂重点版.pdf' -Destination '复合函数单调性_课堂重点版_分步放映.pdf' -Force
    Copy-Item -LiteralPath 'build/handout/handout.pdf' -Destination '复合函数单调性_课堂重点版_静态阅览.pdf' -Force
    if (Test-Path -LiteralPath '使用说明.md') {
        $focusFiles=@('复合函数单调性_课堂重点版.tex','编译.ps1','使用说明.md','复合函数单调性_课堂重点版_分步放映.pdf','复合函数单调性_课堂重点版_静态阅览.pdf')
        Compress-Archive -LiteralPath $focusFiles -DestinationPath '复合函数单调性_课堂重点版_课件包.zip' -Force
    }
    Write-Output '已生成课堂重点版。'
} finally { Pop-Location }
