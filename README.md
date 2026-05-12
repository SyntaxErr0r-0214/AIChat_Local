<p align="center">
  <pre>
     █████╗ ██╗     ██████╗██╗  ██╗ █████╗ ████████╗
    ██╔══██╗██║    ██╔════╝██║  ██║██╔══██╗╚══██╔══╝
    ███████║██║    ██║     ███████║███████║   ██║
    ██╔══██║██║    ██║     ██╔══██║██╔══██║   ██║
    ██║  ██║██║    ╚██████╗██║  ██║██║  ██║   ██║
    ╚═╝  ╚═╝╚═╝     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝
  </pre>
</p>

<p align="center">
  <strong>⚡ 本地大模型终端助手 — 流式对话 · 持久记忆 · 技能系统 · 工具调用</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/LM_Studio-Compatible-green?logo=data:image/svg+xml;base64," alt="LM Studio">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
  <img src="https://img.shields.io/badge/Platform-macOS-lightgrey?logo=apple" alt="macOS">
</p>

---

## 📖 简介

AIChat 是一个功能丰富的**本地大模型命令行客户端**，通过 LM Studio 的 OpenAI 兼容 API 与本地部署的大语言模型进行交互。

它不只是一个简单的聊天工具——它拥有 **持久化记忆系统**、**可切换技能模式**、**本地工具调用** 等高级功能，体验接近 ChatGPT / Gemini / Claude Code 等商业产品，但完全运行在本地，无需联网，隐私安全。

### ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🌊 **流式输出** | 逐 token 实时渲染，Markdown 格式美化，代码高亮 |
| 🧠 **持久化记忆** | 自动提取并记住你的个人信息，跨会话保留 |
| 💾 **会话管理** | 自动保存对话，支持加载/删除历史会话 |
| 🎯 **技能系统** | 可切换的 AI 角色/模式，放入 `.md` 文件即可添加 |
| 🔧 **工具调用** | AI 可创建文件、读取目录、打开应用、执行命令 |
| 🎨 **Rich 终端 UI** | ASCII Art 横幅、彩色面板、表格展示、实时动画 |
| 🔒 **安全确认** | 危险操作（写文件、执行命令）需用户手动批准 |

---

## 🚀 快速开始

### 前置要求

- **macOS**（工具调用使用 `open` 命令，其他系统需微调）
- **Python 3.8+**
- **LM Studio** 运行中，已开启远程服务

### 安装

```bash
# 1. 克隆项目
git clone <your-repo-url> AIChat
cd AIChat

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
```

### 配置

编辑 `aichat/config.py`，修改以下参数：

```python
API_BASE = "http://172.20.10.3:1234"    # 你的 LM Studio 地址
MODEL_NAME = "google/gemma-4-e4b"        # 你使用的模型名称
```

### 运行

```bash
python3 chat.py
```

> 💡 脚本会自动检测并激活虚拟环境，你不需要手动 `source venv/bin/activate`。

---

## 📁 项目结构

```
AIChat/
├── chat.py                 # 启动入口（venv 自动检测 + 启动主程序）
├── requirements.txt        # Python 依赖（rich, prompt_toolkit, requests）
├── aichat/                 # 核心代码包
│   ├── __init__.py         # 包描述
│   ├── config.py           # 集中配置（API 地址、模型、参数、系统提示词）
│   ├── api.py              # API 通信（流式 SSE + Agent 工具循环）
│   ├── app.py              # 主循环（用户输入 → 命令分发 → 对话流程）
│   ├── ui.py               # 终端 UI 渲染（横幅、帮助、表格、面板）
│   ├── history.py          # 会话持久化（JSON 格式保存/加载/列表/删除）
│   ├── memory.py           # 记忆系统（自动提取 + 持久化 + 系统提示注入）
│   ├── skills.py           # 技能系统（解析 .md 技能文件、切换模式）
│   └── tools.py            # 工具系统（7 个本地工具 + 多格式解析 + 安全确认）
├── skills/                 # 技能文件目录
│   ├── translator.md       # 内置技能：翻译助手
│   ├── code_review.md      # 内置技能：代码审查
│   ├── writer.md           # 内置技能：写作助手
│   ├── first_love.md       # 内置技能：初恋.skill 创建器
│   └── first-love-skill/   # 原始 first-love-skill 仓库（参考资料）
├── chat_history/           # 会话数据（自动生成）
│   ├── *.json              # 各会话记录
│   └── memory.json         # 持久化记忆存储
└── venv/                   # Python 虚拟环境
```

---

## 💬 使用指南

### 基本对话

启动后直接输入消息即可开始对话，AI 会以 Markdown 格式流式输出回复：

```
❯ 什么是量子计算？

  🤖 AI  09:30:00

  ## 量子计算简介
  量子计算是一种利用量子力学原理进行信息处理的计算范式...

  ⏱ 3.2s  │  📝 456 字符
```

### 命令列表

所有命令以 `/` 开头：

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助菜单 |
| `/clear` | 清除当前对话，开始新会话 |
| `/bye` | 保存并退出 |

**会话管理：**

| 命令 | 说明 |
|------|------|
| `/sessions` | 查看所有历史会话 |
| `/load <序号>` | 加载指定会话继续对话 |
| `/delete <序号>` | 删除指定会话 |
| `/history` | 查看当前对话摘要 |

**记忆系统：**

| 命令 | 说明 |
|------|------|
| `/memory` | 查看 AI 记住的关于你的信息 |
| `/remember <内容>` | 手动添加一条记忆 |
| `/forget <序号>` | 删除指定记忆 |
| `/forget all` | 清除所有记忆 |

**技能系统：**

| 命令 | 说明 |
|------|------|
| `/skills` | 查看所有可用技能 |
| `/skill <序号>` | 激活指定技能 |
| `/skill off` | 关闭技能，回到普通模式 |

**其他：**

| 命令 | 说明 |
|------|------|
| `/model` | 查看模型与连接状态 |
| `/system <提示词>` | 修改系统提示词 |

---

## 🧠 记忆系统

AIChat 拥有类似 ChatGPT / Gemini 的**持久化记忆**功能。

### 工作原理

```
用户发消息 → AI 回复 → 自动分析对话 → 提取个人信息 → 保存到 memory.json
                                                          ↓
下次对话时 ← 自动注入到系统提示词 ← 从 memory.json 加载记忆
```

### 示例

```
❯ 我叫小明，是一名 Python 开发者，在上海工作

  🤖 AI  ...

  🧠 已记住: 用户的名字叫小明
  🧠 已记住: 用户是一名 Python 开发者
  🧠 已记住: 用户在上海工作
```

之后的每次对话（包括重启后），AI 都会记得这些信息。

### 数据存储

记忆保存在 `chat_history/memory.json`，格式：

```json
{
  "memories": [
    {
      "id": "a1b2c3d4",
      "content": "用户的名字叫小明",
      "source": "auto",
      "created_at": "2026-05-12T09:00:00"
    }
  ]
}
```

---

## 🎯 技能系统

技能让 AI 切换到不同的专业模式。

### 使用流程

```
❯ /skills                        # 查看可用技能

  🎯 可用技能
  ┌────┬──────────────┬─────────────────────┬────────┐
  │ 序号│    名称       │        说明          │  状态  │
  ├────┼──────────────┼─────────────────────┼────────┤
  │  1 │ 代码审查      │ 专业代码审查...       │   ○    │
  │  2 │ 初恋.skill    │ 把记忆里的初恋...     │   ○    │
  │  3 │ 翻译助手      │ 专业多语言翻译...     │   ○    │
  │  4 │ 写作助手      │ 帮助润色改写...       │   ○    │
  └────┴──────────────┴─────────────────────┴────────┘

❯ /skill 3                       # 激活翻译助手

  🎯 技能已激活
  翻译助手

[翻译助手] ❯ Hello World         # 提示符变化，进入技能模式
  你好，世界

[翻译助手] ❯ /skill off          # 关闭技能
❯                                # 恢复普通模式
```

### 添加自定义技能

在 `skills/` 目录创建 `.md` 文件：

```markdown
---
name: 你的技能名
description: 简短描述
---
这里写系统提示词...
AI 会按照这里的指令工作。
```

保存后，下次启动或执行 `/skills` 即可看到新技能。

---

## 🔧 工具调用

AI 可以操作本地文件系统和执行命令，类似 Claude Code / Codex。

### 可用工具

| 工具 | 功能 | 安全级别 |
|------|------|----------|
| `read_file` | 读取文件内容 | 🟢 自动执行 |
| `list_dir` | 列出目录文件 | 🟢 自动执行 |
| `create_file` | 创建/覆写文件 | 🟡 需确认 |
| `edit_file` | 查找替换编辑 | 🟡 需确认 |
| `create_dir` | 创建目录 | 🟡 需确认 |
| `open_in_app` | 用默认应用打开 | 🟡 需确认 |
| `run_command` | 执行 shell 命令 | 🟡 需确认 |

### 使用示例

```
❯ 帮我创建一个 hello.py 文件，写一个打印九九乘法表的程序

  🤖 AI
  🔧 create_file
  ⚠ AI 请求执行操作:
    create_file → hello.py
  允许执行? (y/n): y  ✓

  文件已创建！你可以运行 python3 hello.py 查看结果。
```

### 安全机制

- **读取操作**（read_file、list_dir）自动执行，不会修改任何内容
- **写入操作**（create_file、edit_file 等）会显示操作详情并**等待用户确认**
- **命令执行**（run_command）同样需要确认，且有 30 秒超时保护

---

## 🌸 初恋.skill

一个特殊的内置技能，改编自 [first-love-skill](https://github.com/z969081067-commits/first-love-skill)。

### 功能

通过 3 轮温柔的引导问答，收集你关于初恋的记忆，然后：

1. 在 `first_loves/` 目录生成完整的人格文件（memory.md、persona.md、meta.json 等）
2. 切换为 ta 的人格与你对话
3. 支持追加记忆和纠正人格

### 使用

```
❯ /skills
❯ /skill 2                          # 激活初恋.skill
[初恋.skill 创建器] ❯               # 按引导回答 3 轮问题
[初恋.skill 创建器] ❯ /skill off    # 结束后关闭
```

> ⚠️ 本功能仅用于个人回忆与情感整理，不用于骚扰、跟踪、冒充或侵犯隐私。

---

## ⚙️ 配置参数

所有配置集中在 `aichat/config.py`：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `API_BASE` | `http://172.20.10.3:1234` | LM Studio 服务地址 |
| `MODEL_NAME` | `google/gemma-4-e4b` | 模型标识符 |
| `MAX_HISTORY` | `80` | 最大保留对话轮数 |
| `MAX_TOKENS` | `8192` | 单次生成最大 token 数 |
| `TEMPERATURE` | `0.7` | 生成多样性 (0~1) |
| `REQUEST_TIMEOUT` | `300` | API 请求超时（秒） |

---

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────┐
│                    chat.py (入口)                     │
│              venv 检测 → 启动 app.main()              │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  app.py (主循环)                      │
│         用户输入 → 命令分发 → 对话管理                  │
├─────────┬────────┬────────┬─────────┬───────────────┤
│  api.py │  ui.py │history │ memory  │   skills.py   │
│  流式API │  终端UI │ 会话存储 │ 记忆系统 │   技能管理    │
│ +Agent  │  渲染   │  JSON  │ 自动提取 │  .md 解析     │
│  循环    │        │        │         │               │
├─────────┴────────┴────────┴─────────┴───────────────┤
│                    tools.py (工具系统)                 │
│   create_file · read_file · edit_file · list_dir     │
│   create_dir · open_in_app · run_command             │
├─────────────────────────────────────────────────────┤
│                    config.py (配置)                    │
│            API 地址 · 模型 · 参数 · 提示词              │
└─────────────────────────────────────────────────────┘
```

### Agent 工具循环

当 AI 需要使用工具时，系统会自动进入循环：

```
模型生成 → 检测 tool_call → 执行工具 → 反馈结果 → 模型继续生成
                ↑                                       │
                └───────── 最多 8 轮 ──────────────────┘
```

---

## 🔧 技术细节

- **流式传输**: 使用 SSE (Server-Sent Events) 协议，逐 token 接收
- **Markdown 渲染**: Rich 库的 `Live` + `Markdown` 实时渲染，支持代码高亮（Monokai 主题）
- **编码处理**: 强制 UTF-8 解码，解决 LM Studio 响应中文乱码问题
- **venv 自动激活**: 通过 `os.execv` 替换进程，无需手动 source
- **多格式工具解析**: 同时支持标准 `<tool_call>` 格式和 Gemma 原生 `<|tool_call>` 格式
- **输入体验**: prompt_toolkit 提供历史记录、Emacs 快捷键支持

---

## 📋 依赖

```
rich            # 终端 UI 渲染（面板、表格、Markdown、动画）
prompt_toolkit  # 高级命令行输入（历史、快捷键）
requests        # HTTP 通信（流式 SSE）
```

---

## 📄 License

MIT

---

<p align="center">
  <em>后来这么多年，我又迎过了无数盛夏。但只有那年的盛夏最耀眼。</em>
</p>
