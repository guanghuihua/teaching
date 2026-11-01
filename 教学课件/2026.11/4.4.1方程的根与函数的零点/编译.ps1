$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    if (-not (Get-Command xelatex -ErrorAction SilentlyContinue)) {
        throw '未找到 xelatex。请安装 TeX Live，并将其 bin 目录加入 PATH。'
    }
    New-Item -ItemType Directory -Force 'build' | Out-Null
    $variants = @(
        @{ Job = '放映版'; Input = '方程的根与函数的零点.tex' },
        @{ Job = '阅览版'; Input = '\def\PrintVersion{1}\input{方程的根与函数的零点.tex}' }
    )
    foreach ($variant in $variants) {
        foreach ($pass in 1..2) {
            & xelatex '-interaction=nonstopmode' '-halt-on-error' '-output-directory=build' "-jobname=$($variant.Job)" $variant.Input
            if ($LASTEXITCODE -ne 0) {
                throw "编译失败：$($variant.Job)，第 $pass 遍。请检查 build 中的日志。"
            }
        }
        $logText = Get-Content -Raw -LiteralPath "build/$($variant.Job).log"
        if ($logText -match 'Overfull \\[hv]box|Missing character:|Undefined control sequence') {
            throw "发现版面溢出、缺字或未定义命令，请检查 build/$($variant.Job).log。"
        }
        Copy-Item -LiteralPath "build/$($variant.Job).pdf" -Destination "方程的根与函数的零点_$($variant.Job).pdf" -Force
    }
    Write-Host '已生成放映版和阅览版 PDF。'
}
finally {
    Pop-Location
}
