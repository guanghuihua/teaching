$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    New-Item -ItemType Directory -Force -Path 'build' | Out-Null
    $lessons = @('4.1.1 有理指数幂.tex', '4.1.3 幂函数.tex', '4.2.2 指数函数的图象和性质.tex')
    foreach ($lesson in $lessons) {
        for ($pass = 1; $pass -le 2; $pass++) {
            & xelatex -interaction=nonstopmode -halt-on-error -output-directory=build $lesson
            if ($LASTEXITCODE -ne 0) { throw "编译失败：$lesson，第 $pass 遍。请查看 build 中的日志。" }
        }
    }
    Write-Host '三份课件已编译完成，PDF 位于 build 目录。'
} finally {
    Pop-Location
}
