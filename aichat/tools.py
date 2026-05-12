"""
工具系统模块 - 让 AI 能执行本地操作

支持的工具:
  - create_file: 创建文件
  - read_file: 读取文件
  - edit_file: 编辑文件（替换内容）
  - list_dir: 列出目录内容
  - open_in_app: 用系统默认应用打开文件
  - run_command: 执行 shell 命令（需用户确认）
  - create_dir: 创建目录

工具调用格式（模型输出中嵌入）:
  <tool_call>
  {"name": "create_file", "arguments": {"path": "test.txt", "content": "hello"}}
  </tool_call>

安全机制:
  - 读取类操作自动执行
  - 写入/执行类操作需用户确认
"""

import os
import re
import json
import subprocess

from .config import PROJECT_DIR


# ════════════════════════════════════════
# 工具定义（供系统提示词注入）
# ════════════════════════════════════════

TOOLS_DESCRIPTION = """
## 可用工具

你可以通过以下格式调用工具来操作文件和系统：

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

7. **run_command** - 执行 shell 命令（需用户确认）
   参数: command(命令字符串)

### 使用规则
- 路径可以是相对路径（相对于项目目录）或绝对路径
- 一条消息中可以包含多个 tool_call
- 工具调用会自动执行，结果会反馈给你
- 写入和命令执行会先请求用户确认
- 正常对话时不要使用工具格式
"""

# 安全分类：哪些操作需要用户确认
SAFE_TOOLS = {"read_file", "list_dir"}  # 自动执行
UNSAFE_TOOLS = {"create_file", "edit_file", "create_dir", "open_in_app", "run_command"}  # 需确认


def _resolve_path(path):
    """将相对路径解析为基于项目目录的绝对路径"""
    if os.path.isabs(path):
        return path
    return os.path.join(PROJECT_DIR, path)


# ════════════════════════════════════════
# 工具实现
# ════════════════════════════════════════

def tool_create_file(path, content):
    """创建文件，自动创建中间目录"""
    path = _resolve_path(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ 文件已创建: {path} ({len(content)} 字符)"


def tool_read_file(path):
    """读取文件内容"""
    path = _resolve_path(path)
    if not os.path.exists(path):
        return f"❌ 文件不存在: {path}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # 限制返回长度，防止上下文溢出
    if len(content) > 8000:
        return content[:8000] + f"\n\n... (文件过长，已截断，共 {len(content)} 字符)"
    return content


def tool_edit_file(path, old_text, new_text):
    """编辑文件：查找 old_text 并替换为 new_text"""
    path = _resolve_path(path)
    if not os.path.exists(path):
        return f"❌ 文件不存在: {path}"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if old_text not in content:
        return f"❌ 未找到要替换的内容"
    new_content = content.replace(old_text, new_text, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return f"✅ 文件已编辑: {path}"


def tool_list_dir(path):
    """列出目录内容"""
    path = _resolve_path(path)
    if not os.path.isdir(path):
        return f"❌ 目录不存在: {path}"
    items = []
    for name in sorted(os.listdir(path)):
        full = os.path.join(path, name)
        if os.path.isdir(full):
            items.append(f"📁 {name}/")
        else:
            size = os.path.getsize(full)
            items.append(f"📄 {name} ({size} bytes)")
    return "\n".join(items) if items else "(空目录)"


def tool_create_dir(path):
    """创建目录"""
    path = _resolve_path(path)
    os.makedirs(path, exist_ok=True)
    return f"✅ 目录已创建: {path}"


def tool_open_in_app(path):
    """用 macOS 默认应用打开文件"""
    path = _resolve_path(path)
    if not os.path.exists(path):
        return f"❌ 文件不存在: {path}"
    subprocess.Popen(["open", path])
    return f"✅ 已打开: {path}"


def tool_run_command(command):
    """执行 shell 命令"""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True,
            text=True, timeout=30, cwd=PROJECT_DIR,
        )
        output = result.stdout
        if result.stderr:
            output += "\n[stderr] " + result.stderr
        if len(output) > 4000:
            output = output[:4000] + "\n... (输出过长，已截断)"
        return output or "(无输出)"
    except subprocess.TimeoutExpired:
        return "❌ 命令执行超时 (30s)"
    except Exception as e:
        return f"❌ 执行失败: {e}"


# 工具注册表
TOOL_REGISTRY = {
    "create_file": lambda args: tool_create_file(args["path"], args["content"]),
    "read_file": lambda args: tool_read_file(args["path"]),
    "edit_file": lambda args: tool_edit_file(args["path"], args["old_text"], args["new_text"]),
    "list_dir": lambda args: tool_list_dir(args["path"]),
    "create_dir": lambda args: tool_create_dir(args["path"]),
    "open_in_app": lambda args: tool_open_in_app(args["path"]),
    "run_command": lambda args: tool_run_command(args["command"]),
}


# ════════════════════════════════════════
# 工具调用解析与执行
# ════════════════════════════════════════

def parse_tool_calls(text):
    """
    从模型输出中解析工具调用。

    支持多种格式：
      1. 标准格式: <tool_call>{"name": "...", "arguments": {...}}</tool_call>
      2. Gemma 原生格式: <|tool_call>call:tool_name{json_args}<tool_call|>
      3. 变体: ```tool_call ... ``` 代码块格式

    返回:
        list[dict]: [{"name": "...", "arguments": {...}, "raw": "原始匹配文本"}, ...]
    """
    calls = []

    # ─── 格式 1: 标准格式 <tool_call>...</tool_call> ───
    pattern1 = r"<tool_call>\s*(\{.*?\})\s*</tool_call>"
    for match in re.findall(pattern1, text, re.DOTALL):
        try:
            data = json.loads(match)
            calls.append({
                "name": data.get("name", ""),
                "arguments": data.get("arguments", {}),
                "raw": f"<tool_call>\n{match}\n</tool_call>",
            })
        except json.JSONDecodeError:
            continue

    # ─── 格式 2: Gemma 原生格式 <|tool_call>call:name{...}<tool_call|> ───
    pattern2 = r"<\|tool_call>call:(\w+)(\{.*?\})<tool_call\|>"
    for match in re.finditer(pattern2, text, re.DOTALL):
        tool_name = match.group(1)
        try:
            args = json.loads(match.group(2))
            calls.append({
                "name": tool_name,
                "arguments": args,
                "raw": match.group(0),
            })
        except json.JSONDecodeError:
            continue

    # ─── 格式 3: 代码块格式 ```tool_call ... ``` ───
    pattern3 = r"```(?:tool_call)?\s*(\{.*?\})\s*```"
    for match in re.findall(pattern3, text, re.DOTALL):
        try:
            data = json.loads(match)
            if "name" in data:
                calls.append({
                    "name": data.get("name", ""),
                    "arguments": data.get("arguments", {}),
                    "raw": f"```\n{match}\n```",
                })
        except json.JSONDecodeError:
            continue

    return calls


def execute_tool(name, arguments, console):
    """
    执行单个工具调用。

    对于不安全的操作，会先请求用户确认。

    返回:
        tuple: (成功与否, 结果文本)
    """
    if name not in TOOL_REGISTRY:
        return False, f"❌ 未知工具: {name}"

    # 不安全操作需要用户确认
    if name in UNSAFE_TOOLS:
        console.print(f"\n[bold #ff9900]⚠ AI 请求执行操作:[/]")
        console.print(f"  [bold]{name}[/]", end="")
        # 显示关键参数
        if name == "create_file":
            console.print(f" → [dim]{arguments.get('path', '?')}[/]")
        elif name == "edit_file":
            console.print(f" → [dim]{arguments.get('path', '?')}[/]")
        elif name == "run_command":
            console.print(f" → [dim]{arguments.get('command', '?')}[/]")
        elif name == "open_in_app":
            console.print(f" → [dim]{arguments.get('path', '?')}[/]")
        elif name == "create_dir":
            console.print(f" → [dim]{arguments.get('path', '?')}[/]")
        else:
            console.print()

        # 请求确认
        try:
            confirm = console.input("[bold #00ddff]允许执行? (y/n): [/]").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return False, "❌ 用户取消"

        if confirm not in ("y", "yes", "是"):
            return False, "❌ 用户拒绝执行"

    # 执行工具
    try:
        result = TOOL_REGISTRY[name](arguments)
        return True, result
    except Exception as e:
        return False, f"❌ 工具执行出错: {type(e).__name__}: {e}"


def strip_tool_calls(text):
    """从文本中移除所有格式的 tool_call 标签，返回纯文本部分"""
    # 标准格式
    text = re.sub(r"<tool_call>\s*\{.*?\}\s*</tool_call>", "", text, flags=re.DOTALL)
    # Gemma 原生格式
    text = re.sub(r"<\|tool_call>call:\w+\{.*?\}<tool_call\|>", "", text, flags=re.DOTALL)
    # 代码块格式（包含 "name" 字段的 JSON 代码块）
    text = re.sub(r'```(?:tool_call)?\s*\{[^`]*\}\s*```', "", text, flags=re.DOTALL)
    return text.strip()
