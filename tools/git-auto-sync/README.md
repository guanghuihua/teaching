# 两台电脑定时同步备课资料

Windows 定时任务负责登录启动、每两分钟巡检和异常后重启；后台程序负责同步 `origin/main`。保存文件后连续 **60 秒没有新修改**，自动提交并上传；空闲时每 **120 秒**检查并下载另一台电脑的更新。断网后保留本地资料，联网后重试。

## 两台电脑各安装一次

1. 安装 Git for Windows，完成自己的 GitHub 登录，确认能手动访问仓库。
2. 使用同一个仓库的 `main` 分支。另一台电脑已有资料时先备份、合并，不能直接覆盖现有目录。
3. 双击本目录的 **`安装定时同步.cmd`**。它会创建 Windows 定时任务，并在桌面创建 **备课资料同步** 快捷方式。
4. 双击桌面入口或 `查看同步状态.cmd`，查看后台是否运行、最近状态及日志位置。

工具使用 Windows 自带 PowerShell 和任务计划，不安装新 EXE、不保存密码或令牌。注册任务是否允许取决于本机账户权限；失败时会报错，不会自动提升权限或修改系统安全设置。任务仅在当前 Windows 用户登录时运行，使用电池供电也继续运行，暂停后会保持暂停。

首次启用时，如果仓库尚有历史分叉或待核对的文件，程序会继续定期检查并说明原因，**不会把遗留改动直接上传**。确认工作目录干净且本地 `main` 与 `origin/main` 一致后，自动进入正常同步。

本机首次资料整理的备份、路径变化及待核对入口见[[tools/git-auto-sync/首次同步整理说明_20261117|2026-11-17 首次同步整理说明]]。

## 日常操作

| 入口 | 用途 |
| --- | --- |
| `安装定时同步.cmd` / `设置登录自启.cmd` | 安装并启动定时任务 |
| `查看同步状态.cmd` / 桌面“备课资料同步” | 查看是否已启用、后台进程、最近状态、日志 |
| `立即同步.cmd` | 请求立即同步；后台运行时通常 10 秒内开始处理 |
| `停止自动同步.cmd` | 禁用定时任务并安全停止后台，本次暂停会持续到手动恢复 |
| `启动自动同步.cmd` | 恢复定时任务并启动后台 |

换电脑前，保存并确认上一台显示 `已同步`。手动切换分支、暂存、合并或变基前，先暂停自动同步，完成后再恢复。关闭电脑不会把尚未上传的内容自动传到 GitHub。

## 同步范围

- 遵守各层 `.gitignore`。笔记、TeX、图片、Word、PPT 和其他已跟踪的教学资料正常同步。
- **新 PDF、ZIP、可执行文件，以及成绩单、家长会材料、个人课表不自动上传。** 已跟踪的正式 PDF 仍随修改同步。新 PDF 确认是正式教学交付物后，可人工 `git add -f -- "路径.pdf"` 并提交一次，之后进入跟踪。
- 书籍大 PDF、下载压缩包、原始软件安装程序保留本机；它们不是双机 GitHub 同步的内容，需要时单独传输。
- TeX 辅助文件、Office 临时文件、OCR/渲染工作输出、第三方 `AlJabr-1-master/` 本地修改不自动提交。
- 普通删除会同步；一次超过 **20 项删除**或 **200 项文件改动**时暂停，避免批量误删。已确认的大规模整理应先人工提交。
- 凭据、学生身份信息和成绩不能纳入上传。文件名检查不能代替内容核对；对已跟踪文件，仅增加忽略规则不会停止上传。

## 暂停原因

日志出现 `BLOCKED` 或 `SETUP` 时，本轮没有完成同步：

| 信息 | 处理方式 |
| --- | --- |
| `History diverged` | 两边都有独有提交，暂停程序并人工合并 |
| `Remote updates and local uncommitted files coexist` | 远端有更新且本地还有未提交资料，先核对并合并 |
| `Large change batch` | 人工检查并提交大批移动、删除或新增 |
| `Staged changes exist` / `Another Git operation/lock is present` | 完成人工暂存、合并、变基或其他 Git 操作，不直接删除来源不明的锁 |
| 网络、登录、钩子或推送失败 | 本地文件和已生成的本地提交保留，程序会重试；可暂停后手动执行 Git 查看原因 |

程序仅做快进拉取，不自动解决冲突、变基或强制推送。两台电脑离线期间都改过资料时，可能需要人工合并。状态为“已同步”表示允许纳入 Git 的文件已处理，不能理解为整个硬盘目录所有文件都已上传。

## 日志、暂停与卸载

日志及状态在本机 `.git/teaching-auto-sync/`（工作树情况下在对应的 Git 元数据目录）。这些内容不上传。日志只记录时间、状态和数量，不记录文件正文或认证信息。

取消登录启动、移除定时任务并停止后台：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\git-auto-sync\Periodic-Sync.ps1 -Mode Uninstall
```

备课文件和日志会保留；桌面状态入口也保留，方便查看“未安装”状态。暂停与恢复分别使用 `-Mode Pause` 和 `-Mode Resume`。

## 检查与测试

以下命令从仓库根目录运行。仅检查（获取远端引用，不提交、不推送、不更新工作文件）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\git-auto-sync\Sync-Teaching.ps1 -Mode Check
```

查看任务配置但不注册：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\git-auto-sync\Periodic-Sync.ps1 -Mode Plan
```

集成测试使用本地临时仓库和裸仓库，不操作备课文件，不连接真实 GitHub：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\git-auto-sync\tests\Test-AutoSync.ps1
```

同步的是仓库资料；TeX、字体、Obsidian 和其他软件环境仍需在两台电脑分别安装。
