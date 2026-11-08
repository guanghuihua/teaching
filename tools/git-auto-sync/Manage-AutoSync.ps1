# Per-user startup installation; no administrator permissions or stored passwords.
[CmdletBinding()]
param(
    [ValidateSet('Install', 'Start', 'Status', 'Stop', 'Uninstall')][string]$Action = 'Status',
    [string]$RepoPath
)
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
if (-not $RepoPath) { $RepoPath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
$encoding = New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding = $encoding
$RepoPath = [IO.Path]::GetFullPath($RepoPath).TrimEnd('\', '/')
$worker = Join-Path $PSScriptRoot 'Sync-Teaching.ps1'
$powerShellExe = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$gitDirectory = (& git -C $RepoPath rev-parse --absolute-git-dir)
if ($LASTEXITCODE -ne 0) { throw 'Cannot find the Git repository.' }
$stateDirectory = Join-Path $gitDirectory 'teaching-auto-sync'
[void][IO.Directory]::CreateDirectory($stateDirectory)
$approvalFile = Join-Path $stateDirectory 'initialized.json'
$stopFile = Join-Path $stateDirectory 'stop.request'
$hash = [Security.Cryptography.SHA256]::Create()
try { $repositoryId = ([BitConverter]::ToString($hash.ComputeHash($encoding.GetBytes($RepoPath.ToLowerInvariant())))).Replace('-', '').Substring(0, 12) }
finally { $hash.Dispose() }
$startupLink = Join-Path ([Environment]::GetFolderPath('Startup')) ('Teaching-Git-AutoSync-' + $repositoryId + '.lnk')

function Test-Running {
    $lockPath = Join-Path $stateDirectory 'worker.lock'
    try {
        $probe = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
        $probe.Dispose()
        return $false
    } catch [IO.IOException] { return $true }
}

function Start-Worker {
    if (Test-Running) { Write-Host 'Auto-sync is already running.'; return }
    if (-not (Test-Path -LiteralPath $approvalFile)) {
        # Never sweep an existing dirty folder into its first automatic upload.
        & $powerShellExe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $worker -RepoPath $RepoPath -Mode Check
        if ($LASTEXITCODE -ne 0) { throw 'First-start checks failed. Review sync.log; no startup entry was installed.' }
        $pending = @(& git -C $RepoPath status --porcelain=v1 --untracked-files=all)
        $counts = (& git -C $RepoPath rev-list --left-right --count HEAD...refs/remotes/origin/main).Trim() -split '\s+'
        if ($LASTEXITCODE -ne 0 -or $pending.Count -gt 0 -or [int]$counts[0] -ne 0 -or [int]$counts[1] -ne 0) {
            throw 'First start requires a clean main branch matching origin/main. Review existing changes manually first.'
        }
        [IO.File]::WriteAllText($approvalFile, (@{ Repository = $RepoPath; InitializedAt = (Get-Date).ToString('o') } | ConvertTo-Json), $encoding)
    }
    if (Test-Path -LiteralPath $stopFile) { Remove-Item -LiteralPath $stopFile -Force }
    $launchArgs = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" -RepoPath "{1}" -Mode Watch' -f $worker, $RepoPath
    $process = Start-Process -FilePath $powerShellExe -ArgumentList $launchArgs -WindowStyle Hidden -PassThru
    try {
        $deadline = [DateTime]::UtcNow.AddSeconds(5)
        do {
            if (Test-Running) {
                Write-Host ('Started hidden worker (PID {0}). Log: {1}' -f $process.Id, (Join-Path $stateDirectory 'sync.log'))
                return
            }
            $process.Refresh()
            if ($process.HasExited) { throw 'Background worker exited during startup. Review sync.log.' }
            Start-Sleep -Milliseconds 250
        } while ([DateTime]::UtcNow -lt $deadline)
        throw 'Could not confirm background startup. Check status and sync.log.'
    } finally { $process.Dispose() }
}

function Stop-Worker {
    if (-not (Test-Running)) { Write-Host 'Auto-sync is not running.'; return }
    [IO.File]::WriteAllText($stopFile, 'stop', $encoding)
    for ($attempt = 0; $attempt -lt 15; $attempt++) {
        Start-Sleep -Seconds 1
        if (-not (Test-Running)) { Write-Host 'Auto-sync stopped.'; return }
    }
    Write-Host 'Stop requested. An active Git operation will finish before the worker exits.'
}

try {
    switch ($Action) {
        'Start' { Start-Worker }
        'Install' {
            Start-Worker
            $shell = New-Object -ComObject WScript.Shell
            $shortcut = $shell.CreateShortcut($startupLink)
            $shortcut.TargetPath = $powerShellExe
            $shortcut.Arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" -RepoPath "{1}" -Action Start' -f $PSCommandPath, $RepoPath
            $shortcut.WorkingDirectory = $RepoPath
            $shortcut.WindowStyle = 7
            $shortcut.Description = 'Sync teaching materials after sign-in'
            $shortcut.Save()
            Write-Host ('Installed for this Windows user at sign-in: {0}' -f $startupLink)
        }
        'Stop' { Stop-Worker }
        'Uninstall' {
            Stop-Worker
            if (Test-Path -LiteralPath $startupLink) { Remove-Item -LiteralPath $startupLink -Force }
            Write-Host 'Removed the sign-in startup entry. Teaching files and local logs were preserved.'
        }
        'Status' {
            Write-Host ('Running: {0}; start at sign-in: {1}' -f (Test-Running), (Test-Path -LiteralPath $startupLink))
            $statusFile = Join-Path $stateDirectory 'status.json'
            if (Test-Path -LiteralPath $statusFile) { Write-Host ([IO.File]::ReadAllText($statusFile, $encoding)) }
            Write-Host ('Log: {0}' -f (Join-Path $stateDirectory 'sync.log'))
        }
    }
} catch { Write-Error $_.Exception.Message -ErrorAction Continue; exit 2 }
