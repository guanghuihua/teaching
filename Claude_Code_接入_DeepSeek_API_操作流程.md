# Claude Code 接入 DeepSeek API 操作流程

本文档记录在 WSL 中使用 Claude Code，并把后端 API 改为 DeepSeek 的操作流程。

这样做的效果是：终端里仍然使用 `claude` 这个 coding agent，但实际请求会发往 DeepSeek 的 Anthropic-compatible API，而不是 Anthropic 官方 Claude 账号。

> 注意：这不是注册 Claude 账号，也不是解除 Claude 账号封禁。它只是把 Claude Code 的 API 后端切换为 DeepSeek。

## 一、准备条件

需要先准备：

- WSL 终端环境
- Node.js 18 或更高版本
- Claude Code CLI
- DeepSeek API Key

DeepSeek API Key 获取地址：

```text
https://platform.deepseek.com
```

DeepSeek 官方 Claude Code 集成文档：

```text
https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/
```

## 二、安装或更新 Claude Code

先检查 Node.js：

```bash
node -v
```

如果版本是 `v18` 或更高，可以继续。

安装 Claude Code：

```bash
npm install -g @anthropic-ai/claude-code
```

如果已经安装过，建议更新到最新版：

```bash
npm update -g @anthropic-ai/claude-code
```

检查 Claude Code 是否可用：

```bash
which claude
claude --version
```

在 WSL 中，`which claude` 应该尽量指向 Linux/WSL 环境里的路径，而不是 Windows 路径。

## 三、临时配置 DeepSeek 后端

在同一个 WSL 终端里执行下面命令。

把 `<你的 DeepSeek API Key>` 替换为自己的 key：

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="<你的 DeepSeek API Key>"
export ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"
export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
export CLAUDE_CODE_EFFORT_LEVEL="max"
```

说明：

- `ANTHROPIC_BASE_URL`：把请求地址改为 DeepSeek 的 Anthropic-compatible API。
- `ANTHROPIC_AUTH_TOKEN`：使用 DeepSeek API Key 鉴权。
- `ANTHROPIC_MODEL`：主模型。
- `ANTHROPIC_DEFAULT_OPUS_MODEL`、`ANTHROPIC_DEFAULT_SONNET_MODEL`、`ANTHROPIC_DEFAULT_HAIKU_MODEL`：让 Claude Code 内部不同模型档位都映射到 DeepSeek 模型。
- `CLAUDE_CODE_SUBAGENT_MODEL`：子 agent 使用的模型。
- `CLAUDE_CODE_EFFORT_LEVEL`：推理/工作强度设置。

模型名里有 `[1m]`，所以一定要加英文双引号。

## 四、验证环境变量

执行：

```bash
echo "$ANTHROPIC_BASE_URL"
echo "$ANTHROPIC_MODEL"
test -n "$ANTHROPIC_AUTH_TOKEN" && echo "DeepSeek key is set"
```

正常情况下应该看到：

```text
https://api.deepseek.com/anthropic
deepseek-v4-pro[1m]
DeepSeek key is set
```

不要直接执行下面命令：

```bash
echo "$ANTHROPIC_AUTH_TOKEN"
```

因为它会把完整 API key 打印出来，容易泄露。

## 五、启动 Claude Code

进入项目目录：

```bash
cd /mnt/d/guanghui/teaching
```

启动：

```bash
claude
```

如果配置成功，Claude Code 应该直接进入工作界面，而不是要求登录 Claude 账号。

## 六、如果出现登录菜单怎么办

如果出现类似下面界面：

```text
Login

Claude Code can be used with your Claude subscription or billed based on API usage through your Console account.

Select login method:

❯ 1. Claude account with subscription · Pro, Max, Team, or Enterprise
  2. Anthropic Console account · API usage billing
  3. 3rd-party platform · Amazon Bedrock, Microsoft Foundry, or Vertex AI
```

不要选 `1`、`2`、`3`。

直接按：

```text
Ctrl + C
```

退出。

这个登录菜单说明 Claude Code 没有识别到 DeepSeek 环境变量，或者当前终端里没有设置这些变量。

然后按顺序排查。

### 1. 确认变量是否存在

```bash
env | grep -E 'ANTHROPIC|CLAUDE_CODE'
```

至少应该能看到：

```text
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_AUTH_TOKEN=...
ANTHROPIC_MODEL=deepseek-v4-pro[1m]
```

### 2. 确认是在同一个终端里启动

`export` 只对当前终端会话有效。

如果你在一个终端里设置环境变量，却在另一个终端里执行 `claude`，变量不会自动生效。

正确顺序是：

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="<你的 DeepSeek API Key>"
export ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
claude
```

### 3. 清掉可能冲突的官方配置

如果之前配置过 Anthropic 官方 API 或第三方云平台，可以先临时清掉：

```bash
unset ANTHROPIC_API_KEY
unset CLAUDE_CODE_USE_BEDROCK
unset CLAUDE_CODE_USE_VERTEX
```

然后重新设置 DeepSeek 变量，再启动 `claude`。

### 4. 检查 Claude Code 安装位置

```bash
which claude
claude --version
```

如果 `which claude` 指向 Windows 路径，说明你可能不是在 WSL 里运行 WSL 版 Claude Code。

可以在 WSL 中重新安装：

```bash
npm install -g @anthropic-ai/claude-code@latest
```

## 七、做成永久配置

如果每次都手动 `export` 太麻烦，可以创建一个单独的环境文件。

创建文件：

```bash
nano ~/.deepseek_claude_env
```

写入：

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="<你的 DeepSeek API Key>"
export ANTHROPIC_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash"
export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash"
export CLAUDE_CODE_EFFORT_LEVEL="max"
```

保存后限制权限：

```bash
chmod 600 ~/.deepseek_claude_env
```

以后每次要使用 DeepSeek 版 Claude Code，只需要执行：

```bash
source ~/.deepseek_claude_env
cd /mnt/d/guanghui/teaching
claude
```

## 八、可选：写进 .bashrc

如果希望每次打开 WSL 都自动使用 DeepSeek 后端，可以把上面的 `export` 命令写入：

```bash
~/.bashrc
```

编辑：

```bash
nano ~/.bashrc
```

在文件末尾加入同样的环境变量。

保存后执行：

```bash
source ~/.bashrc
```

这种方式最方便，但 API key 会长期保存在 shell 配置文件里。个人电脑上可以接受；如果机器有多人使用，更建议使用上一节的 `~/.deepseek_claude_env`。

## 九、推荐日常启动方式

推荐使用单独环境文件：

```bash
source ~/.deepseek_claude_env
cd /mnt/d/guanghui/teaching
claude
```

如果想确认 key 已经加载：

```bash
test -n "$ANTHROPIC_AUTH_TOKEN" && echo "DeepSeek key is set"
```

## 十、最小排查命令

如果还是不能用，把下面命令的输出保存下来，方便继续定位：

```bash
which claude
claude --version
env | grep -E 'ANTHROPIC|CLAUDE_CODE'
```

注意：如果输出里出现完整 API key，发给别人之前要打码。

## 十一、关键结论

出现 Claude Code 登录菜单时，不要选择：

```text
1. Claude account with subscription
2. Anthropic Console account
3. 3rd-party platform
```

DeepSeek 不是 Anthropic Console，也不是 Bedrock、Vertex AI 或 Microsoft Foundry。

正确方式是：

```text
先退出登录菜单，再在启动 claude 之前设置 ANTHROPIC_BASE_URL 和 ANTHROPIC_AUTH_TOKEN。
```

