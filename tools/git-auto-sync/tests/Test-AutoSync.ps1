# Integration tests: real Git, a local bare remote, and isolated temporary clones.
[CmdletBinding()]
param([switch]$ManagerOnly)
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$utf8 = New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
$worker = Join-Path (Split-Path -Parent $PSScriptRoot) 'Sync-Teaching.ps1'
$manager = Join-Path (Split-Path -Parent $PSScriptRoot) 'Manage-AutoSync.ps1'
$powerShellExe = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('teaching-autosync-tests-' + [guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($testRoot)
$script:Passed = 0
$script:WatchProcess = $null

function Assert($Condition, [string]$Message) {
    if (-not $Condition) { throw ('FAIL: ' + $Message) }
}

function Git([string]$Directory, [string[]]$Arguments) {
    $originalPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $output = @(& git.exe -C $Directory @Arguments 2>&1)
    $code = $LASTEXITCODE
    $ErrorActionPreference = $originalPreference
    if ($code -ne 0) { throw ('Test Git failed: ' + ($Arguments -join ' ') + ': ' + ($output -join "`n")) }
    return ($output -join "`n")
}

function Put([string]$Path, [string]$Text) {
    [void][IO.Directory]::CreateDirectory((Split-Path -Parent $Path))
    [IO.File]::WriteAllText($Path, $Text, $utf8)
}

function New-Fixture([string]$Name) {
    $root = Join-Path $testRoot $Name
    [void][IO.Directory]::CreateDirectory($root)
    $remote = Join-Path $root 'remote.git'
    [void](Git $root @('init', '--bare', '--initial-branch=main', $remote))
    $first = Join-Path $root 'computer one'
    [void](Git $root @('clone', $remote, $first))
    [void](Git $first @('config', 'user.name', 'AutoSync Test'))
    [void](Git $first @('config', 'user.email', 'test@example.invalid'))
    [void](Git $first @('config', 'commit.gpgsign', 'false'))
    Put (Join-Path $first 'lesson.md') 'original'
    Put (Join-Path $first '.gitignore') "*.aux`n.env`n/tmp/`n"
    [void](Git $first @('add', '.'))
    [void](Git $first @('commit', '-m', 'initial'))
    [void](Git $first @('push', '-u', 'origin', 'main'))
    $second = Join-Path $root 'computer two'
    [void](Git $root @('clone', $remote, $second))
    [void](Git $second @('config', 'user.name', 'AutoSync Test'))
    [void](Git $second @('config', 'user.email', 'test@example.invalid'))
    [void](Git $second @('config', 'commit.gpgsign', 'false'))
    return [pscustomobject]@{ Root = $root; A = $first; B = $second; Remote = $remote }
}

function Run-Worker([string]$Repository, [string]$Mode = 'Once') {
    $originalPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $output = @(& $powerShellExe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $worker -RepoPath $Repository -Mode $Mode 2>&1)
    $code = $LASTEXITCODE
    $ErrorActionPreference = $originalPreference
    Write-Host ($output -join "`n")
    return $code
}

function Remote-Head($Fixture) { return Git $Fixture.A @('ls-remote', 'origin', 'refs/heads/main') }
function Pass([string]$Name) { $script:Passed++; Write-Host ('PASS: ' + $Name) }

function Run-Manager([string]$Repository, [string]$Action) {
    $originalPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $output = @(& $powerShellExe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $manager -RepoPath $Repository -Action $Action 2>&1)
    $code = $LASTEXITCODE
    $ErrorActionPreference = $originalPreference
    Write-Host ($output -join "`n")
    return $code
}

try {
    if (-not $ManagerOnly) {
    $f = New-Fixture 'normal'
    $chineseName = ([string][char]0x96C6 + [char]0x5408) + ' [draft] #1.md'
    Put (Join-Path $f.A $chineseName) 'new lesson'
    Put (Join-Path $f.A 'lesson.md') 'updated'
    Put (Join-Path $f.A 'build.aux') 'ignored'
    Put (Join-Path $f.A '.env') 'not-a-real-secret'
    Put (Join-Path $f.A 'preview.pdf') 'reproducible output'
    $head = Remote-Head $f
    Assert ((Run-Worker $f.A 'Check') -eq 0) 'check succeeds'
    Assert ((Remote-Head $f) -eq $head) 'check never pushes'
    Assert ((Git $f.A @('log', '--format=%s', '-1')) -eq 'initial') 'check never commits'
    Pass 'check mode is non-publishing'
    Assert ((Run-Worker $f.A) -eq 0) 'normal sync succeeds'
    Assert ((Git $f.A @('diff', '--cached', '--name-only')) -eq '') 'real index is clean after auto-commit'
    $tracked = Git $f.A @('-c', 'core.quotepath=false', 'ls-files')
    Assert ($tracked.Contains($chineseName)) 'Chinese and special-character path is tracked'
    Assert (-not $tracked.Contains('preview.pdf')) 'new generated PDF is skipped'
    Assert (-not $tracked.Contains('.env')) 'ignored credentials stay untracked'
    Assert (-not $tracked.Contains('build.aux')) 'build output stays untracked'
    Assert ((Run-Worker $f.B) -eq 0) 'second computer pulls'
    Assert ([IO.File]::ReadAllText((Join-Path $f.B $chineseName), $utf8) -eq 'new lesson') 'remote file arrives intact'
    Pass 'push, fast-forward pull, Unicode paths, ignores, temporary index'

    Put (Join-Path $f.B 'formal.pdf') 'old formal PDF'
    [void](Git $f.B @('add', 'formal.pdf'))
    [void](Git $f.B @('commit', '-m', 'track intentional PDF'))
    [void](Git $f.B @('push', 'origin', 'main'))
    Put (Join-Path $f.B 'formal.pdf') 'updated formal PDF'
    Remove-Item -LiteralPath (Join-Path $f.B 'lesson.md')
    Assert ((Run-Worker $f.B) -eq 0) 'tracked PDF update and deletion sync'
    [void](Git $f.A @('clean', '-f', '--', 'preview.pdf'))
    Assert ((Run-Worker $f.A) -eq 0) 'first computer pulls deletion'
    Assert (-not (Test-Path -LiteralPath (Join-Path $f.A 'lesson.md'))) 'deletion is pulled'
    Assert ([IO.File]::ReadAllText((Join-Path $f.A 'formal.pdf'), $utf8) -eq 'updated formal PDF') 'tracked PDF is updated'
    Pass 'tracked formal PDF and ordinary deletion'

    $f = New-Fixture 'staged'
    Put (Join-Path $f.A 'lesson.md') 'manual staged work'
    [void](Git $f.A @('add', 'lesson.md'))
    $head = Remote-Head $f
    Assert ((Run-Worker $f.A) -ne 0) 'manual staged changes block sync'
    Assert ((Git $f.A @('diff', '--cached', '--name-only')) -eq 'lesson.md') 'manual staging survives'
    Assert ((Remote-Head $f) -eq $head) 'manual staging is not published'
    Pass 'manual staged work is preserved'

    $f = New-Fixture 'diverged'
    Put (Join-Path $f.A 'local.md') 'local commit'
    [void](Git $f.A @('add', '.'))
    [void](Git $f.A @('commit', '-m', 'local only'))
    Put (Join-Path $f.B 'remote.md') 'remote commit'
    [void](Git $f.B @('add', '.'))
    [void](Git $f.B @('commit', '-m', 'remote only'))
    [void](Git $f.B @('push', 'origin', 'main'))
    Put (Join-Path $f.A 'lesson.md') 'not committed'
    $head = Remote-Head $f
    Assert ((Run-Worker $f.A) -ne 0) 'divergence blocks sync'
    Assert ((Remote-Head $f) -eq $head) 'divergence does not force-push'
    Assert ((Git $f.A @('log', '--format=%s', '-1')) -eq 'local only') 'divergence does not auto-commit or rebase'
    Assert ([IO.File]::ReadAllText((Join-Path $f.A 'lesson.md'), $utf8) -eq 'not committed') 'dirty file survives divergence'
    Pass 'diverged histories preserve both sides'

    $f = New-Fixture 'behind-dirty'
    Put (Join-Path $f.B 'lesson.md') 'remote edit'
    [void](Git $f.B @('add', '.'))
    [void](Git $f.B @('commit', '-m', 'remote edit'))
    [void](Git $f.B @('push', 'origin', 'main'))
    Put (Join-Path $f.A 'lesson.md') 'local edit'
    Assert ((Run-Worker $f.A) -ne 0) 'dirty workspace plus incoming commits blocks'
    Assert ([IO.File]::ReadAllText((Join-Path $f.A 'lesson.md'), $utf8) -eq 'local edit') 'local edit is not overwritten'
    Pass 'incoming updates do not overwrite local uncommitted work'

    $f = New-Fixture 'large-delete'
    for ($i = 0; $i -lt 21; $i++) { Put (Join-Path $f.A ($i.ToString() + '.md')) 'delete test' }
    [void](Git $f.A @('add', '.'))
    [void](Git $f.A @('commit', '-m', 'many files'))
    [void](Git $f.A @('push', 'origin', 'main'))
    for ($i = 0; $i -lt 21; $i++) { Remove-Item -LiteralPath (Join-Path $f.A ($i.ToString() + '.md')) }
    $head = Remote-Head $f
    Assert ((Run-Worker $f.A) -ne 0) 'large deletion batch blocks'
    Assert ((Remote-Head $f) -eq $head) 'large deletion batch is not uploaded'
    Pass 'large deletion guard'

    $f = New-Fixture 'credential-name'
    Put (Join-Path $f.A 'APIKEY') 'not-a-real-secret'
    $head = Remote-Head $f
    Assert ((Run-Worker $f.A) -ne 0) 'unignored credential-like name blocks'
    Assert ((Remote-Head $f) -eq $head) 'credential-like file is not uploaded'
    Pass 'credential-like filename guard'

    $f = New-Fixture 'commit-hook'
    Put (Join-Path $f.A '.git/hooks/pre-commit') "#!/bin/sh`nexit 1`n"
    Put (Join-Path $f.A 'lesson.md') 'hook should reject'
    Assert ((Run-Worker $f.A) -ne 0) 'failed commit hook blocks'
    Assert ((Git $f.A @('diff', '--cached', '--name-only')) -eq '') 'failed hook leaves real index untouched'
    Assert (-not (Test-Path -LiteralPath (Join-Path $f.A '.git/index.lock'))) 'owned index lock is released'
    Remove-Item -LiteralPath (Join-Path $f.A '.git/hooks/pre-commit')
    Assert ((Run-Worker $f.A) -eq 0) 'retry after hook failure succeeds'
    Pass 'commit hook failure is recoverable'

    $f = New-Fixture 'offline'
    Put (Join-Path $f.A 'lesson.md') 'offline edit'
    [void](Git $f.A @('remote', 'set-url', 'origin', (Join-Path $f.Root 'missing.git')))
    Assert ((Run-Worker $f.A) -ne 0) 'network/remote failure blocks'
    Assert ((Git $f.A @('log', '--format=%s', '-1')) -eq 'initial') 'offline failure preserves uncommitted work'
    [void](Git $f.A @('remote', 'set-url', 'origin', $f.Remote))
    Assert ((Run-Worker $f.A) -eq 0) 'retry after reconnect succeeds'
    Pass 'offline and retry'

    $f = New-Fixture 'push-rejected'
    Put (Join-Path $f.Remote 'hooks/pre-receive') "#!/bin/sh`nexit 1`n"
    Put (Join-Path $f.A 'lesson.md') 'save before push failure'
    $head = Remote-Head $f
    Assert ((Run-Worker $f.A) -ne 0) 'remote rejection is reported'
    Assert ((Remote-Head $f) -eq $head) 'rejected push does not update remote'
    Assert ((Git $f.A @('diff', '--cached', '--name-only')) -eq '') 'failed push leaves a clean index'
    Assert ([int](Git $f.A @('rev-list', '--count', 'HEAD')) -eq 2) 'local commit survives push failure'
    Remove-Item -LiteralPath (Join-Path $f.Remote 'hooks/pre-receive')
    Assert ((Run-Worker $f.A) -eq 0) 'later retry publishes existing local commit'
    Assert ([int](Git $f.A @('rev-list', '--count', 'HEAD')) -eq 2) 'retry does not create a duplicate commit'
    Pass 'failed push preserves the local commit for retry'

    $f = New-Fixture 'large-addition'
    for ($i = 0; $i -lt 201; $i++) { Put (Join-Path $f.A ($i.ToString() + '.md')) 'batch' }
    Assert ((Run-Worker $f.A) -ne 0) 'large addition batch blocks'
    Assert ([int](Git $f.A @('rev-list', '--count', 'HEAD')) -eq 1) 'large batch is not committed'
    Pass 'large addition guard'

    $f = New-Fixture 'large-file'
    $largeFile = [IO.File]::OpenWrite((Join-Path $f.A 'large.pptx'))
    try { $largeFile.SetLength(96MB) } finally { $largeFile.Dispose() }
    Assert ((Run-Worker $f.A) -ne 0) 'oversized file blocks'
    Pass 'oversized file guard'

    $f = New-Fixture 'wrong-branch'
    [void](Git $f.A @('switch', '-c', 'draft'))
    Put (Join-Path $f.A 'lesson.md') 'draft work'
    Assert ((Run-Worker $f.A) -ne 0) 'wrong branch blocks'
    Pass 'branch switching guard'

    $f = New-Fixture 'watch'
    $launchArgs = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{0}" -RepoPath "{1}" -Mode Watch -QuietSeconds 3 -PollSeconds 1 -RemotePollSeconds 10' -f $worker, $f.A
    $script:WatchProcess = Start-Process -FilePath $powerShellExe -ArgumentList $launchArgs -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 2
    Put (Join-Path $f.A 'lesson.md') 'save 1'
    Start-Sleep -Seconds 1
    Put (Join-Path $f.A 'lesson.md') 'save 2'
    Start-Sleep -Seconds 1
    Assert ((Git $f.A @('log', '--format=%s', '-1')) -eq 'initial') 'watcher waits through repeated saves'
    $deadline = [DateTime]::UtcNow.AddSeconds(15)
    do {
        Start-Sleep -Seconds 1
        $commits = [int](Git $f.A @('rev-list', '--count', 'HEAD'))
    } while ($commits -eq 1 -and [DateTime]::UtcNow -lt $deadline)
    Assert ($commits -eq 2) 'watcher creates one debounced commit'
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        Start-Sleep -Seconds 1
        $remoteHead = (Git $f.A @('ls-remote', 'origin', 'refs/heads/main')) -split '\s+'
        $localHead = Git $f.A @('rev-parse', 'HEAD')
    } while ($remoteHead[0] -ne $localHead -and [DateTime]::UtcNow -lt $deadline)
    Assert ($remoteHead[0] -eq $localHead) 'watcher pushes after quiet interval'
    [void](Git $f.B @('pull', '--ff-only'))
    Put (Join-Path $f.B 'from-other-computer.md') 'incoming background update'
    [void](Git $f.B @('add', '.'))
    [void](Git $f.B @('commit', '-m', 'other computer'))
    [void](Git $f.B @('push', 'origin', 'main'))
    $deadline = [DateTime]::UtcNow.AddSeconds(15)
    do { Start-Sleep -Seconds 1 }
    while (-not (Test-Path -LiteralPath (Join-Path $f.A 'from-other-computer.md')) -and [DateTime]::UtcNow -lt $deadline)
    Assert ((Test-Path -LiteralPath (Join-Path $f.A 'from-other-computer.md'))) 'idle watcher pulls other computer updates'
    Put (Join-Path $f.A '.git/teaching-auto-sync/stop.request') 'stop'
    Assert ($script:WatchProcess.WaitForExit(10000)) 'watcher stops gracefully'
    Assert ($script:WatchProcess.ExitCode -eq 0) 'watcher exits cleanly'
    $script:WatchProcess.Dispose(); $script:WatchProcess = $null
    Pass 'background watcher debounce, idle pull, and graceful stop'
    }

    $f = New-Fixture 'manager'
    $defaultDirectory = Join-Path $f.A 'tools/git-auto-sync'
    [void][IO.Directory]::CreateDirectory($defaultDirectory)
    Copy-Item -LiteralPath $worker, $manager -Destination $defaultDirectory
    & $powerShellExe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $defaultDirectory 'Sync-Teaching.ps1') -Mode Check
    Assert ($LASTEXITCODE -eq 0) 'worker infers the repository from its own directory'
    & $powerShellExe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $defaultDirectory 'Manage-AutoSync.ps1') -Action Status
    Assert ($LASTEXITCODE -eq 0) 'manager infers the repository from its own directory'
    Pass 'default repository inference in Windows PowerShell 5.1'
    Put (Join-Path $f.A 'lesson.md') 'existing unreviewed work'
    Assert ((Run-Manager $f.A 'Start') -ne 0) 'first start refuses preexisting dirty work'
    Assert (-not (Test-Path -LiteralPath (Join-Path $f.A '.git/teaching-auto-sync/initialized.json'))) 'dirty first start is not initialized'
    [void](Git $f.A @('add', '.'))
    [void](Git $f.A @('commit', '-m', 'review existing work'))
    [void](Git $f.A @('push', 'origin', 'main'))
    Assert ((Run-Manager $f.A 'Start') -eq 0) 'manager starts hidden worker on reviewed clean repo'
    Assert ((Test-Path -LiteralPath (Join-Path $f.A '.git/teaching-auto-sync/initialized.json'))) 'successful first start is recorded locally'
    Assert ((Run-Manager $f.A 'Status') -eq 0) 'status command works'
    Assert ((Run-Manager $f.A 'Start') -eq 0) 'duplicate start is harmless'
    Assert ((Run-Manager $f.A 'Stop') -eq 0) 'manager stops worker safely'
    Pass 'manager first-start guard, hidden startup, status, duplicate start, stop'

    Write-Host ('All {0} integration scenarios passed.' -f $script:Passed)
} finally {
    if ($null -ne (Get-Variable -Name f -ErrorAction SilentlyContinue) -and $f.Root.EndsWith('manager')) {
        [void](Run-Manager $f.A 'Stop')
    }
    if ($null -ne $script:WatchProcess) {
        Put (Join-Path $f.A '.git/teaching-auto-sync/stop.request') 'stop'
        [void]$script:WatchProcess.WaitForExit(10000)
        $script:WatchProcess.Dispose()
    }
    # Verify the resolved recursive-delete target remains in this test's temp root.
    $resolved = [IO.Path]::GetFullPath($testRoot)
    $expectedParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if ($resolved.StartsWith($expectedParent, [StringComparison]::OrdinalIgnoreCase) -and [IO.Path]::GetFileName($resolved).StartsWith('teaching-autosync-tests-')) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    } else { throw 'Unsafe temporary cleanup path; test directory retained.' }
}
