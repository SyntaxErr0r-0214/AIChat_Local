"""
配置模块 - 集中管理所有可配置参数

修改此文件即可调整 API 地址、模型名称、上下文长度等参数，
无需修改其他模块的代码。
"""

import os

# ══ 项目路径 ══
# 项目根目录（chat.py 所在位置）
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ══ LM Studio API 配置 ══
# 优先级: 环境变量 > 默认值
# 运行时可通过 /connect 命令修改
_DEFAULT_API_BASE = "http://localhost:1234"
API_BASE = os.environ.get("AICHAT_API_BASE", _DEFAULT_API_BASE)
MODEL_NAME = "google/gemma-4-e4b"            # 模型标识符（与 LM Studio 中一致）
API_ENDPOINT = f"{API_BASE}/v1/chat/completions"  # OpenAI 兼容聊天接口


def set_api_base(new_base):
    """运行时动态修改 API 地址"""
    global API_BASE, API_ENDPOINT
    API_BASE = new_base.rstrip("/")
    API_ENDPOINT = f"{API_BASE}/v1/chat/completions"

# ══ 生成参数 ══
MAX_HISTORY = 80          # 最大保留对话轮数（匹配 32768 token 上下文窗口）
MAX_TOKENS = 8192         # 单次生成的最大 token 数
TEMPERATURE = 0.7         # 生成多样性（0=确定性输出, 1=高随机性）
REQUEST_TIMEOUT = 300     # API 请求超时时间（秒）

# ══ 存储路径 ══
HISTORY_DIR = os.path.join(PROJECT_DIR, "chat_history")    # 历史会话存储目录（仅聊天记录）
MEMORY_DIR = os.path.join(PROJECT_DIR, "user_data")        # 用户数据目录（记忆等）
FIRST_LOVES_DIR = os.path.join(PROJECT_DIR, "first_loves") # 初恋角色数据目录

# ══ 默认系统提示词 ══
DEFAULT_SYSTEM_PROMPT = """你是一个有帮助的AI助手。请用中文回答问题，回答要准确、详细、有条理。

## 可用工具

你可以通过以下格式调用工具来操作本地文件和系统：

<tool_call>
{"name": "工具名", "arguments": {"参数名": "参数值"}}
</tool_call>

### 工具列表

1. **create_file** - 创建或覆写文件
   参数: path(文件路径), content(文件内容)

2. **read_file** - 读取文件内容
   参数: path(文件路径)

3. **edit_file** - 编辑文件（查找替换）
   参数: path(文件路径), old_text(要替换的原文), new_text(替换后的内容)

4. **list_dir** - 列出目录内容
   参数: path(目录路径)

5. **create_dir** - 创建目录（含中间目录）
   参数: path(目录路径)

6. **open_in_app** - 用系统默认应用打开文件
   参数: path(文件路径)

7. **run_command** - 执行 shell 命令
   参数: command(命令字符串)

### 使用规则
- 你可以操作整台电脑的文件系统，不限于项目目录
- 路径支持: 绝对路径(/Users/xxx)、~/xxx(用户主目录)、相对路径(基于用户主目录)
- 常用路径: ~/Desktop(桌面)、~/Documents(文档)、~/Downloads(下载)
- 一条消息中可以包含多个 tool_call
- 只在用户明确要求文件操作或任务需要时才使用工具
- 正常聊天时不要使用工具
- 写入和执行操作会先请求用户确认
- 工具执行结果会通过 <tool_result> 反馈给你"""
