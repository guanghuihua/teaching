# 两台电脑自动同步备课资料

这个工具在 Windows 后台监测当前备课库：保存文件后连续 **60 秒没有新修改**，便自动提交并推送到 `origin/main`；本地没有待处理的文件时，每 **120 秒**检查一次另一台电脑的更新。需要电脑开机、用户已登录且能访问 GitHub；断网后保留本地文件，联网后重试。

## 首次启用

两台电脑各做一次，目录可以都是 `D:\guanghui\teaching`：

1. 安装 Git for Windows，并用自己的账户完成 GitHub 登录。先确认在仓库中手动 `git fetch origin` 和 `git push origin main` 能成功，脚本不保存密码或令牌。
2. 两边都使用同一个仓库的 `main` 分支。另一台电脑若已有资料，先备份、核对并合并；不要覆盖已有文件夹。
3. **先人工处理已有的修改、删除与提交历史分叉，使本地工作目录干净，并与 `origin/main` 一致。** 首次启动检查不会把历史遗留改动直接上传。
4. 双击本目录的 `设置登录自启.cmd`。工具会立即隐藏运行，并在当前 Windows 用户以后登录时启动，不需要管理员权限。
5. 在仓库中新建或修改一份普通 Markdown 笔记，保存后等待约 60～80 秒。双击 `查看同步状态.cmd`，应看到 `SYNCED`；再在 GitHub 上确认该文件。

此后正常备课即可。换电脑前，保存文件并确认上一台已经显示 `SYNCED`；另一台空闲时会自动拉取。离线期间两边都修改过资料时，可能需要人工合并。

## 日常操作

| 文件 | 用途 |
| --- | --- |
| `启动自动同步.cmd` | 在本次登录期间启动后台监测 |
| `设置登录自启.cmd` | 启动监测，并设置当前用户登录后自动启动 |
| `查看同步状态.cmd` | 查看是否正在运行、最近一次状态与日志位置 |
| `停止自动同步.cmd` | 请求安全停止；正在执行的 Git 操作完成后退出 |

取消登录自启并停止监测，在仓库根目录的 PowerShell 执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\git-auto-sync\Manage-AutoSync.ps1 -Action Uninstall
```

手动切换分支、提交、变基或合并前先停止自动同步，完成后再启动。关闭电脑会中断监测，**尚未提交推送的内容不会因此自动上传**。

## 哪些文件会同步

- 遵守仓库各层 `.gitignore`。密钥、`.env`、已忽略的 OCR 与渲染输出不会因本脚本被强制加入。
- 自动加入常用笔记、TeX、代码、图片、Word、PPT、Excel 等文件。已有版本管理的正式 PDF 可以随修改同步。
- **新 PDF、ZIP、数据库、可执行文件和其他未列入白名单的文件不自动加入。** 尤其是 TeX 编译生成的新 PDF，需要先确认是正式交付物，再手动提交一次。白名单见 `Sync-Teaching.ps1` 中的 `$allowedNew`。
- 编译辅助文件、Office 临时文件、Obsidian 窗口状态、`AlJabr-1-master/` 第三方源码不自动提交。
- 普通删除会同步；一次超过 20 项删除或 200 项文件改动时暂停，留给教师人工检查。重命名按删除与新增处理。
- 自动化只能按文件名和路径筛选。含学生身份、成绩或其他隐私的文件应先匿名化或排除；已被 Git 跟踪的文件不能仅靠新增 `.gitignore` 规则停止上传。

## 暂停与重试

`BLOCKED` 表示本轮没有完成同步，原因写在日志中：

- `History diverged`：两边都有独有提交，需要人工合并；脚本不自动变基、解决冲突或强制推送。
- `Remote updates and local uncommitted files coexist`：远端有更新，同时本地还有未提交资料；先停止脚本并人工整理，避免覆盖。
- `Large change batch`：大量删除或改动，需要人工核对后提交。
- `Staged changes exist` 或 `Another Git operation/lock is present`：有人工暂存、合并、变基或锁；完成操作后重试，不要直接删除来源不明的锁文件。
- 网络、登录或提交钩子失败：本地资料和已生成的本地提交保留，后台会继续重试。必要时停止工具，在 PowerShell 手动执行 Git 命令查看详细错误。

脚本仅接受快进拉取，推送遭到远端新提交拒绝时不会覆盖远端历史。多次失败仍会定期重试，但不会替教师作合并决定。

日志和运行状态保存在本机 Git 元数据目录下的 `teaching-auto-sync/`，通常为 `.git/teaching-auto-sync/`；这些文件不会上传到 GitHub。日志只记录时间、状态和数量，不记录文件正文或认证信息。停止工具不会删除备课资料。

## 检查与测试

仅检查条件（会获取远端引用，不提交、推送或更新工作文件）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\git-auto-sync\Sync-Teaching.ps1 -Mode Check
```

立即执行一轮同步（跳过 60 秒等待，但保留其余检查）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\git-auto-sync\Sync-Teaching.ps1 -Mode Once
```

集成测试使用本地临时仓库和本地裸仓库，不连接真实 GitHub，不操作备课文件：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\git-auto-sync\tests\Test-AutoSync.ps1
```

同步的是仓库文件。另一台电脑的 TeX、字体、Obsidian 和其他软件环境仍需分别安装。
