"""
API 调用模块 - 处理与 LM Studio 的通信

核心功能:
  1. 流式调用 OpenAI 兼容接口，逐 token 渲染 Markdown
  2. Agent 循环：检测工具调用 → 执行 → 反馈结果 → 继续生成

LM Studio 以 SSE (Server-Sent Events) 格式推送数据块，
每个数据块包含一个生成的 token，我们实时拼接并用 Rich 渲染。
"""

import json
import time
import requests

from rich.text import Text
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
from rich import box

from .config import API_BASE, API_ENDPOINT, MODEL_NAME, MAX_TOKENS, TEMPERATURE, REQUEST_TIMEOUT
from .tools import parse_tool_calls, execute_tool, strip_tool_calls

# Agent 循环最大轮次（防止无限循环）
MAX_TOOL_ROUNDS = 8


def check_connection(console):
    """
    检查 LM Studio 服务器连接状态。

    向 /v1/models 端点发送 GET 请求，
    成功则显示已加载的模型列表。
    """
    console.print("[dim]正在检查服务器连接...[/]", end=" ")
    try:
        r = requests.get(f"{API_BASE}/v1/models", timeout=5)
        if r.status_code == 200:
            loaded = [m.get("id", "?") for m in r.json().get("data", [])]
            console.print(f"[bold #00ff88]✓ 已连接[/]  [dim]{', '.join(loaded)}[/]")
        else:
            console.print(f"[yellow]⚠ HTTP {r.status_code}[/]")
    except Exception:
        console.print("[bold red]✗ 无法连接[/]")
    console.print()


def _stream_once(messages, console):
    """
    单次流式调用（内部方法）。

    返回:
        str: 模型完整响应文本，失败返回空字符串
    """
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }
    full = ""

    try:
        resp = requests.post(
            API_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        resp.encoding = "utf-8"

        with Live(
            Text("▌", style="bold #00ddff"),
            console=console,
            refresh_per_second=8,
            vertical_overflow="visible",
        ) as live:
            for line in resp.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                d = line[6:]
                if d.strip() == "[DONE]":
                    break
                try:
                    tok = json.loads(d)["choices"][0].get("delta", {}).get("content", "")
                    if tok:
                        full += tok
                        # 渲染时隐藏 tool_call 标签，只显示文本部分
                        display = strip_tool_calls(full)
                        if display:
                            live.update(Markdown(display + " ▌", code_theme="monokai"))
                        else:
                            live.update(Text("⚙ 正在调用工具...", style="dim #ff9900"))
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
            # 最终渲染
            display = strip_tool_calls(full)
            if display:
                live.update(Markdown(display, code_theme="monokai"))

    except requests.ConnectionError:
        console.print(Panel(
            f"[bold red]无法连接到 {API_BASE}[/]\n请检查 LM Studio 远程服务是否已启动",
            title="[bold red]❌ 连接失败[/]",
            border_style="red",
            box=box.ROUNDED,
        ))
        return ""
    except requests.Timeout:
        console.print("[bold red]⏰ 请求超时，请稍后重试。[/]")
        return ""
    except Exception as e:
        console.print(f"[bold red]❌ {type(e).__name__}: {e}[/]")
        return ""

    return full


def stream_chat(messages, console, tools_enabled=True):
    """
    带 Agent 循环的流式聊天。

    流程:
        1. 流式调用模型
        2. 检查响应中是否包含 <tool_call>
        3. 如果有 → 执行工具 → 把结果作为新消息追加 → 再次调用模型
        4. 重复直到模型不再调用工具，或达到最大轮次

    参数:
        messages: 消息列表（会被原地修改以追加工具交互记录）
        console: Rich Console 实例
        tools_enabled: 是否启用工具调用

    返回:
        str: 模型最终的纯文本响应
    """
    t0 = time.time()
    final_text = ""

    for round_num in range(MAX_TOOL_ROUNDS):
        # 流式调用
        raw_response = _stream_once(messages, console)
        if not raw_response:
            break

        # 检查是否包含工具调用
        tool_calls = parse_tool_calls(raw_response) if tools_enabled else []

        if not tool_calls:
            # 没有工具调用，这是最终回复
            final_text = raw_response
            break

        # ─── 有工具调用，执行 Agent 循环 ───
        # 先把模型的完整响应（含 tool_call）加入消息历史
        messages.append({"role": "assistant", "content": raw_response})

        # 逐个执行工具
        tool_results = []
        for tc in tool_calls:
            console.print(f"\n  [bold #ff9900]🔧 {tc['name']}[/]", end="")
            success, result = execute_tool(tc["name"], tc["arguments"], console)
            status = "[#00ff88]✓[/]" if success else "[red]✗[/]"
            console.print(f"  {status}")
            tool_results.append(f"工具 {tc['name']} 执行结果:\n{result}")

        # 把工具结果作为系统/用户消息反馈给模型
        combined_results = "\n\n---\n\n".join(tool_results)
        messages.append({
            "role": "user",
            "content": f"<tool_result>\n{combined_results}\n</tool_result>\n\n请根据工具执行结果继续回复。如果所有操作已完成，直接告诉用户结果即可，不需要再调用工具。"
        })

        console.print()  # 换行，准备下一轮输出

    # 如果最后一轮仍有 tool_calls（达到上限），提取纯文本
    if not final_text:
        final_text = strip_tool_calls(raw_response) if raw_response else ""

    # ─── 显示统计信息 ───
    elapsed = time.time() - t0
    st = Text()
    st.append(f"  ⏱ {elapsed:.1f}s", style="dim #888888")
    st.append(f"  │  📝 {len(final_text)} 字符", style="dim #888888")
    console.print(st)

    return final_text
