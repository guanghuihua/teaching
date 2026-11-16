$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    New-Item -ItemType Directory -Force -Path 'build' | Out-Null
    foreach ($entry in @('main', 'handout')) {
        for ($pass = 1; $pass -le 2; $pass++) {
            & xelatex -interaction=nonstopmode -halt-on-error -output-directory=build "$entry.tex"
            if ($LASTEXITCODE -ne 0) { throw "XeLaTeX failed: $entry" }
        }
    }
    Copy-Item -LiteralPath 'build/main.pdf' -Destination '函数复习_分步放映版.pdf' -Force
    Copy-Item -LiteralPath 'build/handout.pdf' -Destination '函数复习_静态版.pdf' -Force
} finally {
    Pop-Location
}
