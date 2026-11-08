# Compatible with Windows PowerShell 5.1. Keep this script ASCII (no BOM needed).
[CmdletBinding()]
param(
    [string]$RepoPath,
    [ValidateSet('Check', 'Once', 'Watch')][string]$Mode = 'Check',
    [string]$Remote = 'origin',
    [string]$Branch = 'main',
    [ValidateRange(1, 3600)][int]$QuietSeconds = 60,
    [ValidateRange(1, 60)][int]$PollSeconds = 10,
    [ValidateRange(10, 3600)][int]$RemotePollSeconds = 120,
    [ValidateRange(1, 10000)][int]$MaxChangedFiles = 200,
    [ValidateRange(0, 10000)][int]$MaxDeletedFiles = 20,
    [ValidateRange(5, 600)][int]$GitTimeoutSeconds = 120
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
if (-not $RepoPath) { $RepoPath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
$script:Utf8 = New-Object System.Text.UTF8Encoding($false)
$script:GitExe = (Get-Command git.exe -ErrorAction Stop).Source
$script:Repo = [IO.Path]::GetFullPath($RepoPath).TrimEnd('\', '/')
$script:LastStatus = ''

function Quote-Argument([string]$Value) {
    $escaped = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $escaped = [regex]::Replace($escaped, '(\\+)$', '$1$1')
    return '"' + $escaped + '"'
}

function Invoke-Git {
    param([string[]]$Arguments, [switch]$AllowFailure, [string]$IndexFile)
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName = $script:GitExe
    $info.WorkingDirectory = $script:Repo
    $nativeArgs = @('--no-optional-locks', '-c', 'core.quotepath=false') + $Arguments
    $info.Arguments = ($nativeArgs | ForEach-Object { Quote-Argument $_ }) -join ' '
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = $script:Utf8
    $info.StandardErrorEncoding = $script:Utf8
    $info.EnvironmentVariables['GIT_TERMINAL_PROMPT'] = '0'
    $info.EnvironmentVariables['GCM_INTERACTIVE'] = 'Never'
    if (-not $env:GIT_SSH_COMMAND) {
        $info.EnvironmentVariables['GIT_SSH_COMMAND'] = 'ssh -o BatchMode=yes -o ConnectTimeout=20'
    }
    if ($IndexFile) { $info.EnvironmentVariables['GIT_INDEX_FILE'] = $IndexFile }
    $process = New-Object Diagnostics.Process
    $process.StartInfo = $info
    try {
        [void]$process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($GitTimeoutSeconds * 1000)) {
            $process.Kill()
            throw 'Git timed out. Check the network or Git authentication.'
        }
        $result = [pscustomobject]@{
            Code = $process.ExitCode
            Out = $stdout.GetAwaiter().GetResult()
            Err = $stderr.GetAwaiter().GetResult()
        }
        if ($result.Code -ne 0 -and -not $AllowFailure) {
            # Avoid recording remote URLs, credentials, or file contents in logs.
            throw ('Git {0} failed (exit {1}). Check Git/network/authentication manually.' -f $Arguments[0], $result.Code)
        }
        return $result
    } finally { $process.Dispose() }
}

function Get-GitPath([string]$Name) {
    $value = (Invoke-Git -Arguments @('rev-parse', '--git-path', $Name)).Out.Trim()
    if (-not [IO.Path]::IsPathRooted($value)) { $value = Join-Path $script:Repo $value }
    return [IO.Path]::GetFullPath($value)
}

function Write-Status([string]$Code, [string]$Message) {
    $status = [ordered]@{
        Code = $Code; Message = $Message; UpdatedAt = (Get-Date).ToString('o')
        ProcessId = $PID; Repository = $script:Repo; Mode = $Mode
    }
    $temp = Join-Path $script:StateDir 'status.tmp'
    [IO.File]::WriteAllText($temp, ($status | ConvertTo-Json), $script:Utf8)
    Move-Item -LiteralPath $temp -Destination (Join-Path $script:StateDir 'status.json') -Force
    if ($script:LastStatus -ne ($Code + $Message)) {
        $line = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Code, $Message
        $log = Join-Path $script:StateDir 'sync.log'
        if ((Test-Path -LiteralPath $log) -and (Get-Item -LiteralPath $log).Length -gt 1MB) {
            Move-Item -LiteralPath $log -Destination ($log + '.1') -Force
        }
        [IO.File]::AppendAllText($log, $line + [Environment]::NewLine, $script:Utf8)
        Write-Host $line
        $script:LastStatus = $Code + $Message
    }
}

function Get-Snapshot {
    $raw = (Invoke-Git -Arguments @('status', '--porcelain=v1', '-z', '--untracked-files=all', '--no-renames', '--ignore-submodules=all')).Out
    $entries = @()
    $skipped = 0
    $allCount = 0
    $parts = @()
    foreach ($record in $raw.Split([char]0)) {
        if (-not $record) { continue }
        $allCount++
        $state = $record.Substring(0, 2)
        $path = $record.Substring(3)
        $leaf = [IO.Path]::GetFileName($path)
        $ext = [IO.Path]::GetExtension($path).ToLowerInvariant()
        $tracked = $state -ne '??'
        $secret = $leaf -match '^(APIKEY|DeepSeekAPI|deepseek_api_key\.md|\.env(\..*)?|id_(rsa|ed25519)|credentials.*|.*\.(pem|pfx|key))$'
        $temporary = $leaf -match '(?i)(\.(aux|bbl|bcf|blg|dvi|fdb_latexmk|fls|lof|log|lot|nav|out|snm|toc|vrb|xdv|pyc|pyo|tmp|temp)|\.synctex\.gz|\.run\.xml)$' -or $leaf.StartsWith('~$')
        $excluded = $path -match '(^|/)(\.git|\.codex-work|tmp|__pycache__|node_modules)(/|$)' -or $path -match '^AlJabr-1-master/' -or $path -match '^\.obsidian/workspace[^/]*\.json$'
        if ($secret) { throw 'A credential-like filename is pending. Exclude/review it manually before syncing.' }
        $allowedNew = $leaf -in @('.gitignore', '.gitattributes', '.editorconfig') -or $ext -in @(
            '.md', '.tex', '.sty', '.cls', '.bib', '.bst', '.bbx', '.cbx', '.cfg', '.def', '.txt',
            '.csv', '.tsv', '.json', '.yaml', '.yml', '.toml', '.xml', '.py', '.ps1', '.cmd', '.bat',
            '.js', '.mjs', '.cjs', '.ts', '.css', '.html', '.svg', '.png', '.jpg', '.jpeg', '.webp',
            '.gif', '.bmp', '.tif', '.tiff', '.ppt', '.pptx', '.doc', '.docx', '.xls', '.xlsx')
        if ($temporary -or $excluded -or (-not $tracked -and -not $allowedNew)) {
            $skipped++; continue
        }
        $full = Join-Path $script:Repo $path
        $stamp = 'deleted'
        if (Test-Path -LiteralPath $full -PathType Leaf) {
            $file = Get-Item -LiteralPath $full
            if ($file.Length -gt 95MB) { throw 'A pending file exceeds 95 MiB. Review large-file storage manually.' }
            $stamp = '{0}:{1}' -f $file.Length, $file.LastWriteTimeUtc.Ticks
        }
        $entries += [pscustomobject]@{ Path = $path; State = $state }
        $parts += ($state + ':' + $path + ':' + $stamp)
    }
    $hash = [Security.Cryptography.SHA256]::Create()
    try { $signature = [BitConverter]::ToString($hash.ComputeHash($script:Utf8.GetBytes(($parts -join "`n")))) }
    finally { $hash.Dispose() }
    return [pscustomobject]@{ Entries = @($entries); Signature = $signature; Skipped = $skipped; AllCount = $allCount }
}

function Assert-Idle {
    $currentBranch = (Invoke-Git -Arguments @('symbolic-ref', '--quiet', '--short', 'HEAD') -AllowFailure).Out.Trim()
    if ($currentBranch -ne $Branch) { throw ('Expected branch {0}; pause sync before switching branches.' -f $Branch) }
    foreach ($name in @('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply', 'sequencer', 'index.lock')) {
        if (Test-Path -LiteralPath (Get-GitPath $name)) { throw 'Another Git operation/lock is present. Finish it before syncing.' }
    }
    $staged = Invoke-Git -Arguments @('diff', '--cached', '--quiet', '--exit-code') -AllowFailure
    if ($staged.Code -ne 0) { throw 'Staged changes exist. Finish your manual commit before syncing.' }
}

function New-AutoCommit($Snapshot) {
    # Hold the real index lock, but stage in a separate index. A failed hook/add
    # leaves the user's original index intact; concurrent Git index writes block.
    $index = Get-GitPath 'index'
    $lockPath = $index + '.lock'
    $lock = [IO.File]::Open($lockPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    $ownsIndexLock = $true
    $token = [guid]::NewGuid().ToString('N')
    $tempIndex = Join-Path $script:StateDir ($token + '.index')
    $pathList = Join-Path $script:StateDir ($token + '.paths')
    $backupIndex = Join-Path $script:StateDir ($token + '.previous-index')
    try {
        $staged = Invoke-Git -Arguments @('diff', '--cached', '--quiet', '--exit-code') -AllowFailure
        if ($staged.Code -ne 0) { throw 'The index changed; manual staged changes were preserved.' }
        [void](Invoke-Git -Arguments @('read-tree', 'HEAD') -IndexFile $tempIndex)
        $paths = @($Snapshot.Entries | ForEach-Object { $_.Path })
        [IO.File]::WriteAllText($pathList, (($paths -join [char]0) + [char]0), $script:Utf8)
        [void](Invoke-Git -Arguments @('--literal-pathspecs', 'add', '--all', ('--pathspec-from-file=' + $pathList), '--pathspec-file-nul') -IndexFile $tempIndex)
        if ((Get-Snapshot).Signature -ne $Snapshot.Signature) {
            Write-Status 'WAITING' 'Files changed while staging; waiting for the next quiet interval.'
            return $false
        }
        $different = Invoke-Git -Arguments @('diff', '--cached', '--quiet', '--exit-code') -IndexFile $tempIndex -AllowFailure
        if ($different.Code -eq 0) { return $false }
        if ($different.Code -ne 1) { throw 'Could not inspect the temporary index.' }
        $machine = $env:COMPUTERNAME
        if (-not $machine) { $machine = [Environment]::MachineName }
        $message = 'auto-sync: {0} {1}' -f $machine, (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
        [void](Invoke-Git -Arguments @('commit', '-m', $message) -IndexFile $tempIndex)
        $bytes = [IO.File]::ReadAllBytes($tempIndex)
        $lock.Write($bytes, 0, $bytes.Length)
        $lock.Flush($true)
        $lock.Dispose()
        $lock = $null
        if ([IO.File]::Exists($index)) { [IO.File]::Replace($lockPath, $index, $backupIndex) }
        else { [IO.File]::Move($lockPath, $index) }
        $ownsIndexLock = $false
        Write-Status 'COMMITTED' ('Saved {0} changed file(s) in a local commit.' -f $paths.Count)
        return $true
    } finally {
        if ($null -ne $lock) { $lock.Dispose() }
        if ($ownsIndexLock -and (Test-Path -LiteralPath $lockPath)) { Remove-Item -LiteralPath $lockPath -Force }
        foreach ($temporaryPath in @($tempIndex, ($tempIndex + '.lock'), $pathList, $backupIndex)) {
            if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force }
        }
    }
}

function Invoke-SyncCycle([switch]$CheckOnly, [string]$ExpectedSignature) {
    Assert-Idle
    [void](Invoke-Git -Arguments @('fetch', '--no-tags', $Remote, ('+refs/heads/{0}:refs/remotes/{1}/{0}' -f $Branch, $Remote)))
    $upstream = 'refs/remotes/{0}/{1}' -f $Remote, $Branch
    $counts = (Invoke-Git -Arguments @('rev-list', '--left-right', '--count', ('HEAD...' + $upstream))).Out.Trim() -split '\s+'
    $ahead = [int]$counts[0]; $behind = [int]$counts[1]
    if ($ahead -gt 0 -and $behind -gt 0) {
        Write-Status 'BLOCKED' ('History diverged: {0} local / {1} remote commits. Manual reconciliation required; nothing committed or pushed.' -f $ahead, $behind)
        return 2
    }
    $snapshot = Get-Snapshot
    $deletions = @($snapshot.Entries | Where-Object { $_.State.Contains('D') }).Count
    if ($snapshot.Entries.Count -gt $MaxChangedFiles -or $deletions -gt $MaxDeletedFiles) {
        Write-Status 'BLOCKED' ('Large change batch: {0} eligible files, {1} deletions. Review it manually; nothing committed or pushed.' -f $snapshot.Entries.Count, $deletions)
        return 2
    }
    if ($behind -gt 0 -and $snapshot.AllCount -gt 0) {
        Write-Status 'BLOCKED' 'Remote updates and local uncommitted files coexist. Reconcile them manually before syncing.'
        return 2
    }
    if ($CheckOnly) {
        Write-Status 'READY' ('Check only: {0} local / {1} remote commits; {2} eligible file(s), {3} skipped. No commit, push, or checkout performed.' -f $ahead, $behind, $snapshot.Entries.Count, $snapshot.Skipped)
        return 0
    }
    if ($ExpectedSignature -and $ExpectedSignature -ne $snapshot.Signature) {
        Write-Status 'WAITING' 'Files changed during the network check; waiting for the next quiet interval.'
        return 0
    }
    if ($behind -gt 0) {
        [void](Invoke-Git -Arguments @('merge', '--ff-only', '--no-edit', '--no-overwrite-ignore', $upstream))
        Write-Status 'PULLED' ('Downloaded {0} remote commit(s).' -f $behind)
    }
    if ($snapshot.Entries.Count -gt 0) {
        if (-not (New-AutoCommit $snapshot)) { return 0 }
    }
    $remaining = [int](Invoke-Git -Arguments @('rev-list', '--count', ($upstream + '..HEAD'))).Out.Trim()
    if ($remaining -gt 0) {
        [void](Invoke-Git -Arguments @('-c', ('remote.' + $Remote + '.mirror=false'), '-c', 'push.followTags=false', 'push', '--porcelain', $Remote, ('HEAD:refs/heads/' + $Branch)))
        Write-Status 'SYNCED' ('Pushed {0} local commit(s) to {1}/{2}.' -f $remaining, $Remote, $Branch)
    } else {
        Write-Status 'SYNCED' ('Up to date. Skipped {0} temporary/unsupported file(s).' -f $snapshot.Skipped)
    }
    return 0
}

$workerLock = $null
try {
    $actualRoot = (Invoke-Git -Arguments @('rev-parse', '--show-toplevel')).Out.Trim().Replace('/', '\').TrimEnd('\')
    if ($actualRoot -ne $script:Repo.Replace('/', '\')) { throw 'RepoPath must be the repository root.' }
    $script:StateDir = Get-GitPath 'teaching-auto-sync'
    [void][IO.Directory]::CreateDirectory($script:StateDir)
    $workerLock = [IO.File]::Open((Join-Path $script:StateDir 'worker.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
    if ($Mode -ne 'Watch') {
        try { $code = Invoke-SyncCycle -CheckOnly:($Mode -eq 'Check') }
        catch { Write-Status 'BLOCKED' $_.Exception.Message; $code = 2 }
        exit $code
    }
    $stopFile = Join-Path $script:StateDir 'stop.request'
    $previous = ''
    $quietSince = [DateTime]::UtcNow
    $nextRemote = [DateTime]::MinValue
    $nextAttempt = [DateTime]::MinValue
    Write-Status 'WATCHING' ('Watching; quiet interval {0}s, poll {1}s, remote interval {2}s.' -f $QuietSeconds, $PollSeconds, $RemotePollSeconds)
    while (-not (Test-Path -LiteralPath $stopFile)) {
        try {
            $snapshot = Get-Snapshot
            $now = [DateTime]::UtcNow
            if ($snapshot.Signature -ne $previous) { $previous = $snapshot.Signature; $quietSince = $now }
            $hasChanges = $snapshot.Entries.Count -gt 0
            $ready = $hasChanges -and ($now - $quietSince).TotalSeconds -ge $QuietSeconds
            if ($now -ge $nextAttempt -and ($ready -or (-not $hasChanges -and $now -ge $nextRemote))) {
                $code = Invoke-SyncCycle -ExpectedSignature $snapshot.Signature
                $nextRemote = [DateTime]::UtcNow.AddSeconds($RemotePollSeconds)
                if ($code -ne 0) { $nextAttempt = $nextRemote }
                else { $nextAttempt = [DateTime]::MinValue }
            }
        } catch {
            Write-Status 'BLOCKED' $_.Exception.Message
            $nextAttempt = [DateTime]::UtcNow.AddSeconds($RemotePollSeconds)
        }
        Start-Sleep -Seconds $PollSeconds
    }
    Write-Status 'STOPPED' 'Stopped by request.'
} catch {
    Write-Error $_.Exception.Message -ErrorAction Continue
    exit 2
} finally {
    if ($null -ne $workerLock) { $workerLock.Dispose() }
}
