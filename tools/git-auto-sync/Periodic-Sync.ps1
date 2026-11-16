[CmdletBinding()]
param(
    [ValidateSet('Install', 'Plan', 'Status', 'SyncNow', 'Pause', 'Resume', 'Uninstall')][string]$Mode = 'Status',
    [string]$RepoPath,
    [ValidateRange(1, 60)][int]$IntervalMinutes = 2,
    [switch]$WaitForKey
)
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$encoding = New-Object Text.UTF8Encoding($false)
[Console]::OutputEncoding = $encoding
if (-not $RepoPath) { $RepoPath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
$RepoPath = [IO.Path]::GetFullPath($RepoPath).TrimEnd('\', '/')
$gitDirectory = & git.exe -C $RepoPath rev-parse --absolute-git-dir
if ($LASTEXITCODE -ne 0) { throw '无法读取 Git 仓库，请确认备课目录和 Git 安装。' }
$stateDirectory = Join-Path $gitDirectory 'teaching-auto-sync'
[void][IO.Directory]::CreateDirectory($stateDirectory)
$hash = [Security.Cryptography.SHA256]::Create()
try { $repositoryId = ([BitConverter]::ToString($hash.ComputeHash($encoding.GetBytes($RepoPath.ToLowerInvariant())))).Replace('-', '').Substring(0, 12) }
finally { $hash.Dispose() }
$taskName = 'Teaching-Git-AutoSync-' + $repositoryId
$worker = Join-Path $PSScriptRoot 'Sync-Teaching.ps1'
$manager = Join-Path $PSScriptRoot 'Manage-AutoSync.ps1'
$powerShellExe = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$stopFile = Join-Path $stateDirectory 'stop.request'

function Test-WorkerRunning {
    try {
        $probe = [IO.File]::Open((Join-Path $stateDirectory 'worker.lock'), [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
        $probe.Dispose(); return $false
    } catch [IO.IOException] { return $true }
}

function New-SyncTask {
    $arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" -RepoPath "{1}" -Mode Watch -RequireInitialization -RemotePollSeconds {2}' -f $worker, $RepoPath, ($IntervalMinutes * 60)
    $action = New-ScheduledTaskAction -Execute $powerShellExe -Argument $arguments -WorkingDirectory $RepoPath
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-ScheduledTaskPrincipal -UserId $identity.User.Value -LogonType Interactive -RunLevel Limited
    $triggers = @(
        (New-ScheduledTaskTrigger -AtLogOn -User $identity.Name),
        (New-ScheduledTaskTrigger -Once -At (Get-Date).AddSeconds(10) -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes))
    )
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    return New-ScheduledTask -Action $action -Principal $principal -Trigger $triggers -Settings $settings -Description '备课资料与 GitHub 自动同步；后台检查、断网重试，冲突时保留两边资料。'
}

function Resume-Sync {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($null -eq $task) { throw '尚未安装定时任务，请先双击“安装定时同步.cmd”。' }
    Enable-ScheduledTask -TaskName $taskName | Out-Null
    if (Test-Path -LiteralPath $stopFile) { Remove-Item -LiteralPath $stopFile -Force }
    if (-not (Test-WorkerRunning)) { Start-ScheduledTask -TaskName $taskName }
    Write-Host '定时同步已启用。保存后安静 60 秒上传，空闲时定期检查 GitHub。'
}

function Show-SyncStatus {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Write-Host ('备课目录：' + $RepoPath)
    Write-Host ('定时任务：' + $(if ($null -eq $task) { '未安装' } elseif ($task.State -eq 'Disabled') { '已暂停' } else { '已启用' }))
    Write-Host ('后台程序：' + $(if (Test-WorkerRunning) { '正在运行' } else { '未运行' }))
    $statusFile = Join-Path $stateDirectory 'status.json'
    if (Test-Path -LiteralPath $statusFile) {
        $status = [IO.File]::ReadAllText($statusFile, $encoding) | ConvertFrom-Json
        $labels = @{ SYNCED='已同步'; BLOCKED='本轮同步暂停，需要检查原因'; SETUP='首次同步等待资料核对'; STOPPED='已停止'; WATCHING='后台监测中'; WAITING='等待文件保存完成'; COMMITTED='已本地提交，等待上传'; PULLED='已下载远端更新'; READY='检查完成' }
        $label = [string]$status.Code
        if ($labels.ContainsKey($label)) { $label = $labels[$label] }
        Write-Host ('最近状态：' + $label)
        Write-Host ('更新时间：' + $status.UpdatedAt)
        Write-Host ('详细信息：' + $status.Message)
    }
    Write-Host ('日志文件：' + (Join-Path $stateDirectory 'sync.log'))
}

try {
    switch ($Mode) {
        'Plan' {
            $task = New-SyncTask
            @{ TaskName=$taskName; Arguments=$task.Actions[0].Arguments; Triggers=@($task.Triggers).Count; ExecutionTimeLimit=$task.Settings.ExecutionTimeLimit; MultipleInstances=[string]$task.Settings.MultipleInstances; IntervalMinutes=$IntervalMinutes } | ConvertTo-Json -Compress
        }
        'Install' {
            $task = New-SyncTask
            Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null
            $shell = New-Object -ComObject WScript.Shell
            $desktopLink = Join-Path ([Environment]::GetFolderPath('Desktop')) '备课资料同步.lnk'
            if (Test-Path -LiteralPath $desktopLink) {
                $old = $shell.CreateShortcut($desktopLink)
                if (-not $old.Arguments.Contains($RepoPath)) { $desktopLink = Join-Path ([Environment]::GetFolderPath('Desktop')) ('备课资料同步-' + $repositoryId + '.lnk') }
            }
            $link = $shell.CreateShortcut($desktopLink)
            $link.TargetPath = $powerShellExe
            $link.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -RepoPath "{1}" -Mode Status -WaitForKey' -f $PSCommandPath, $RepoPath
            $link.WorkingDirectory = $RepoPath; $link.Description = '查看备课资料与 GitHub 的同步状态'; $link.Save()
            $legacyStartup = Join-Path ([Environment]::GetFolderPath('Startup')) ($taskName + '.lnk')
            if (Test-Path -LiteralPath $legacyStartup) {
                $legacy = $shell.CreateShortcut($legacyStartup)
                if ($legacy.Arguments.Contains($RepoPath)) { Remove-Item -LiteralPath $legacyStartup -Force }
            }
            Resume-Sync
            Write-Host ('已设置登录启动与每 {0} 分钟巡检。桌面入口：{1}' -f $IntervalMinutes, $desktopLink)
        }
        'Resume' { Resume-Sync }
        'Pause' {
            $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($null -ne $task) { Disable-ScheduledTask -TaskName $taskName | Out-Null }
            & $powerShellExe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $manager -RepoPath $RepoPath -Action Stop
            Write-Host '已暂停自动同步；不会在下次巡检时自动恢复。'
        }
        'SyncNow' {
            if (Test-WorkerRunning) {
                [IO.File]::WriteAllText((Join-Path $stateDirectory 'sync.request'), 'sync', $encoding)
                Write-Host '已请求立即同步，通常在 10 秒内处理；冲突和文件检查仍然有效。'
            } else {
                & $powerShellExe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $worker -RepoPath $RepoPath -Mode Once -RequireInitialization
                if ($LASTEXITCODE -ne 0) { throw '本轮未完成同步，请查看上方原因或同步日志。' }
            }
        }
        'Uninstall' {
            $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($null -ne $task) { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false }
            & $powerShellExe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $manager -RepoPath $RepoPath -Action Stop
            Write-Host '已移除定时任务。备课文件与日志保留。'
        }
        'Status' { Show-SyncStatus }
    }
} catch { Write-Error $_.Exception.Message -ErrorAction Continue; exit 2 }
if ($WaitForKey) { [void](Read-Host '按回车关闭此窗口') }
