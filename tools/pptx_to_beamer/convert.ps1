param(
    [string]$Python,
    [Parameter(ValueFromRemainingArguments=$true)][string[]]$Sources
)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
if (-not $Sources) {
    Add-Type -AssemblyName System.Windows.Forms
    $picker = New-Object System.Windows.Forms.OpenFileDialog
    $picker.Filter = 'PowerPoint (*.pptx)|*.pptx'
    $picker.Multiselect = $true
    $picker.Title = '选择要转成 Beamer 的课件'
    if ($picker.ShowDialog() -ne 'OK') { exit 0 }
    $Sources = $picker.FileNames
    $picker.Dispose()
}
if (-not $Python) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    if (Test-Path -LiteralPath $bundledPython) { $Python = $bundledPython }
    else {
        $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
        if (-not $pythonCommand) { throw '未找到 Python 3。请安装后重试，或传入 -Python 路径。' }
        $Python = $pythonCommand.Source
    }
}
$failed = $false
foreach ($source in $Sources) {
    $sourcePath = (Resolve-Path -LiteralPath $source).Path
    $output = Join-Path ([IO.Path]::GetDirectoryName($sourcePath)) ([IO.Path]::GetFileNameWithoutExtension($sourcePath) + '_Beamer')
    if (Test-Path -LiteralPath $output) { $output += '_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') }
    & $Python (Join-Path $PSScriptRoot 'pptx_to_beamer.py') $sourcePath --output $output --compile
    if ($LASTEXITCODE -ne 0) { $failed = $true }
}
if ($failed) { exit 1 }
