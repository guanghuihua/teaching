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
    Copy-Item -LiteralPath 'build/main.pdf' -Destination '3.2.2奇偶性的应用_第2课时_分步放映版.pdf' -Force
    Copy-Item -LiteralPath 'build/handout.pdf' -Destination '3.2.2奇偶性的应用_第2课时_静态版.pdf' -Force
} finally {
    Pop-Location
}
