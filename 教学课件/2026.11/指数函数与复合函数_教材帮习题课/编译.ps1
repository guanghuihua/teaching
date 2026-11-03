$ErrorActionPreference='Stop'
$lessonDir=Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location -LiteralPath $lessonDir
try {
    New-Item -ItemType Directory -Path 'build/slide','build/handout' -Force | Out-Null
    for ($pass=1; $pass -le 2; $pass++) {
        & xelatex -interaction=nonstopmode -halt-on-error -output-directory=build/slide '指数函数与复合函数.tex' | Out-File -LiteralPath 'build/slide/console.txt' -Encoding utf8
        if ($LASTEXITCODE -ne 0) { throw '分步放映版编译失败，请检查 build/slide/console.txt' }
    }
    for ($pass=1; $pass -le 2; $pass++) {
        & xelatex -interaction=nonstopmode -halt-on-error -jobname=handout -output-directory=build/handout '\def\PrintVersion{1}\input{指数函数与复合函数.tex}' | Out-File -LiteralPath 'build/handout/console.txt' -Encoding utf8
        if ($LASTEXITCODE -ne 0) { throw '静态阅览版编译失败，请检查 build/handout/console.txt' }
    }
    Copy-Item -LiteralPath 'build/slide/指数函数与复合函数.pdf' -Destination '指数函数与复合函数_分步放映.pdf' -Force
    Copy-Item -LiteralPath 'build/handout/handout.pdf' -Destination '指数函数与复合函数_静态阅览.pdf' -Force
    $packageFiles=@('指数函数与复合函数.tex','内容_指数比较与方程.tex','内容_单调性补充.tex','内容_复合函数.tex','内容_奇偶综合.tex','编译.ps1','使用与核查说明.md','指数函数与复合函数_分步放映.pdf','指数函数与复合函数_静态阅览.pdf')
    Compress-Archive -LiteralPath $packageFiles -DestinationPath '指数函数与复合函数_完整课件包.zip' -Force
    Write-Output '已生成分步放映版、静态阅览版及完整课件包。'
} finally { Pop-Location }
