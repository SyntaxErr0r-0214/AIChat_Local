"""
应用主循环模块 - 处理用户输入、命令分发、对话流程

这是 AIChat 的核心调度器:
  输入 → 命令识别 → 分发到对应处理函数 → 渲染结果 → 循环
"""

from datetime import datetime

from rich.panel import Panel
from rich.text import Text
from rich import box
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style as PStyle
from prompt_toolkit.formatted_text import HTML

from .config import MAX_HISTORY, DEFAULT_SYSTEM_PROMPT
from .api import stream_chat, check_connection
from .history import (
    gen_session_id, auto_title, save_session,
    load_session, list_sessions, delete_session,
)
from .memory import (
    build_memory_context, extract_memories_from_chat,
    add_memory, delete_memory_by_index, clear_all_memories,
    get_all_memories,
)
from .skills import (
    list_skills, load_skill_by_index, create_example_skills,
)
from .ui import (
    console, show_banner, show_help,
    show_sessions, show_status, show_history, show_memories, show_skills,
)


def main():
    """主程序入口: 初始化界面 → 进入交互循环"""

    # ─── 启动界面 ───
    console.clear()
    show_banner()
    console.print("[dim #444444]" + "─" * 60 + "[/]")
    console.print(
        "[dim]输入消息开始对话  •  [bold #00ff88]/help[/] 查看命令  •  "
        "[bold #00ff88]/sessions[/] 历史会话  •  [bold #00ff88]/bye[/] 退出[/]"
    )
    console.print()

    # ─── 初始化新会话 ───
    # 系统提示词 = 基础提示 + 记忆上下文（自动注入）
    system_prompt = DEFAULT_SYSTEM_PROMPT
    memory_ctx = build_memory_context()
    full_system = system_prompt + memory_ctx
    messages = [{"role": "system", "content": full_system}]

    # 启动时显示记忆状态
    mem_count = len(get_all_memories())
    if mem_count > 0:
        console.print(f"[dim #aa55ff]🧠 已加载 {mem_count} 条记忆[/]")
    session_id = gen_session_id()
    session_title = None
    cached_sessions = None  # 缓存 /sessions 结果供 /load 使用

    # ─── 技能系统初始化 ───
    active_skill = None       # 当前激活的技能（None = 普通模式）
    cached_skills = None      # 缓存技能列表
    create_example_skills()   # 首次运行时创建示例技能文件

    # prompt_toolkit 输入会话（支持上下键历史、Emacs 快捷键等）
    input_style = PStyle.from_dict({"prompt": "#00ddff bold", "": "#ffffff"})
    ps = PromptSession(style=input_style)

    # ─── 检查服务器连接 ───
    check_connection(console)

    # ════════════════════════════════════
    # 主交互循环
    # ════════════════════════════════════
    while True:
        try:
            # 获取用户输入（提示符根据技能模式变化）
            if active_skill:
                prompt_html = (
                    f'<style fg="#ff8800" bold="true">[{active_skill["name"]}]</style>'
                    ' <style fg="#00ddff" bold="true">❯ </style>'
                )
            else:
                prompt_html = '<style fg="#00ddff" bold="true">❯ </style>'

            inp = ps.prompt(HTML(prompt_html)).strip()

            if not inp:
                continue

            # ─── 斜杠命令处理 ───
            if inp.startswith("/"):
                parts = inp.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd in ("/exit", "/bye"):
                    # 退出前保存有内容的对话
                    if any(m["role"] == "user" for m in messages):
                        save_session(session_id, messages, system_prompt, session_title)
                        console.print("[dim]当前对话已保存。[/]")
                    console.print(Panel(
                        "[bold #00ddff]感谢使用 AIChat，再见！👋[/]",
                        border_style="#0088cc", box=box.ROUNDED,
                    ))
                    break

                elif cmd == "/clear":
                    # 保存旧对话 → 开始新会话
                    if any(m["role"] == "user" for m in messages):
                        save_session(session_id, messages, system_prompt, session_title)
                        console.print("[dim]旧对话已保存。[/]")
                    # 重建系统提示（含最新记忆）
                    memory_ctx = build_memory_context()
                    full_system = system_prompt + memory_ctx
                    messages = [{"role": "system", "content": full_system}]
                    session_id = gen_session_id()
                    session_title = None
                    console.clear()
                    show_banner()
                    console.print("[bold #00ff88]✓ 已开始新会话[/]\n")

                elif cmd == "/sessions":
                    cached_sessions = show_sessions()

                elif cmd == "/load":
                    if not arg:
                        console.print("[dim]用法: /load <序号> (先用 /sessions 查看列表)[/]")
                        continue
                    try:
                        idx = int(arg) - 1
                        if cached_sessions is None:
                            cached_sessions = list_sessions()
                        if 0 <= idx < len(cached_sessions):
                            # 先保存当前对话
                            if any(m["role"] == "user" for m in messages):
                                save_session(session_id, messages, system_prompt, session_title)
                            # 加载选中的历史会话
                            s = cached_sessions[idx]
                            sid = s["session_id"]
                            messages, system_prompt, session_title = load_session(sid)
                            session_id = sid
                            console.print(f"[bold #00ff88]✓ 已加载会话:[/] {session_title}")
                            show_history(messages)
                        else:
                            console.print(f"[red]序号超出范围 (1-{len(cached_sessions)})[/]")
                    except ValueError:
                        console.print("[red]请输入有效的数字序号[/]")

                elif cmd == "/delete":
                    if not arg:
                        console.print("[dim]用法: /delete <序号>[/]")
                        continue
                    try:
                        idx = int(arg) - 1
                        if cached_sessions is None:
                            cached_sessions = list_sessions()
                        if 0 <= idx < len(cached_sessions):
                            s = cached_sessions[idx]
                            if delete_session(s["session_id"]):
                                console.print(f"[bold #00ff88]✓ 已删除:[/] {s.get('title', '?')}")
                                cached_sessions = list_sessions()
                            else:
                                console.print("[red]删除失败[/]")
                        else:
                            console.print("[red]序号超出范围[/]")
                    except ValueError:
                        console.print("[red]请输入有效的数字序号[/]")

                elif cmd == "/help":
                    show_help()
                elif cmd == "/history":
                    show_history(messages)
                elif cmd == "/model":
                    show_status()

                # ─── 记忆相关命令 ───
                elif cmd == "/memory":
                    show_memories()

                elif cmd == "/remember":
                    if arg:
                        entry = add_memory(arg, source="manual")
                        console.print(f"[bold #00ff88]✓ 已记住:[/] {arg}")
                    else:
                        console.print("[dim]用法: /remember <要记住的内容>[/]")

                elif cmd == "/forget":
                    if arg.strip().lower() == "all":
                        clear_all_memories()
                        # 更新系统提示（移除记忆部分）
                        messages[0] = {"role": "system", "content": system_prompt}
                        console.print("[bold #00ff88]✓ 所有记忆已清除[/]")
                    elif arg:
                        try:
                            idx = int(arg) - 1
                            ok, content = delete_memory_by_index(idx)
                            if ok:
                                console.print(f"[bold #00ff88]✓ 已遗忘:[/] {content}")
                                # 更新系统提示中的记忆
                                memory_ctx = build_memory_context()
                                messages[0] = {"role": "system", "content": system_prompt + memory_ctx}
                            else:
                                console.print("[red]序号超出范围[/]")
                        except ValueError:
                            console.print("[red]请输入有效的序号或 'all'[/]")
                    else:
                        console.print("[dim]用法: /forget <序号> 或 /forget all[/]")

                # ─── 技能相关命令 ───
                elif cmd == "/skills":
                    cached_skills = show_skills(
                        active_skill["id"] if active_skill else None
                    )

                elif cmd == "/skill":
                    if arg.strip().lower() == "off":
                        # 关闭技能，回到普通模式
                        if active_skill:
                            old_name = active_skill["name"]
                            active_skill = None
                            # 恢复普通系统提示 + 记忆
                            memory_ctx = build_memory_context()
                            messages[0] = {"role": "system", "content": system_prompt + memory_ctx}
                            console.print(f"[bold #00ff88]✓ 已关闭技能: {old_name}，回到普通模式[/]")
                        else:
                            console.print("[dim]当前已是普通模式[/]")
                    elif arg:
                        try:
                            idx = int(arg) - 1
                            if cached_skills is None:
                                cached_skills = list_skills()
                            if 0 <= idx < len(cached_skills):
                                skill = cached_skills[idx]
                                active_skill = skill
                                # 技能模式: 用技能提示词替换系统提示，保留记忆
                                memory_ctx = build_memory_context()
                                messages[0] = {"role": "system", "content": skill["prompt"] + memory_ctx}
                                console.print(Panel(
                                    f"[bold #ffaa00]{skill['name']}[/]\n\n"
                                    f"[dim]{skill['description']}[/]",
                                    title="[bold #ff8800]🎯 技能已激活[/]",
                                    border_style="#ff8800",
                                    box=box.ROUNDED,
                                    padding=(1, 2),
                                ))
                            else:
                                console.print(f"[red]序号超出范围 (1-{len(cached_skills)})[/]")
                        except ValueError:
                            console.print("[red]请输入有效的序号，或使用 /skill off 关闭[/]")
                    else:
                        if active_skill:
                            console.print(f"[dim]当前技能: [bold #ffaa00]{active_skill['name']}[/]")
                        else:
                            console.print("[dim]当前未激活技能。使用 /skills 查看可用技能[/]")

                elif cmd == "/system":
                    if arg:
                        system_prompt = arg
                        memory_ctx = build_memory_context()
                        messages[0] = {"role": "system", "content": arg + memory_ctx}
                        # 如果在技能模式下修改 system，自动退出技能模式
                        if active_skill:
                            active_skill = None
                            console.print("[dim]已自动退出技能模式[/]")
                        console.print("[bold #00ff88]✓ 系统提示已更新[/]")
                    else:
                        console.print(f"[dim]当前: {system_prompt}[/]")
                else:
                    console.print(f"[dim]未知命令: {cmd}，输入 /help 查看帮助[/]")
                continue

            # ─── 发送用户消息 ───
            messages.append({"role": "user", "content": inp})
            if session_title is None:
                session_title = auto_title(messages)

            # 显示 AI 回复头
            console.print()
            ts = datetime.now().strftime("%H:%M:%S")
            h = Text()
            h.append("  🤖 AI  ", style="bold white on #0066aa")
            h.append(f"  {ts}", style="dim #666666")
            console.print(h)
            console.print()

            # 流式调用模型（带工具循环）
            # stream_chat 会在内部修改 messages（追加工具交互记录）
            from .tools import strip_tool_calls
            resp = stream_chat(messages, console, tools_enabled=True)

            if resp:
                # 提取纯文本（去掉 tool_call 标签）作为最终回复
                clean_resp = strip_tool_calls(resp)
                if clean_resp:
                    messages.append({"role": "assistant", "content": clean_resp})
                # 每轮自动保存
                save_session(session_id, messages, system_prompt, session_title)

                # ─── 自动记忆提取（仅在普通模式下执行） ───
                # 技能模式下跳过记忆提取，因为技能对话通常不包含个人信息
                if not active_skill and clean_resp:
                    new_mems = extract_memories_from_chat(inp, clean_resp)
                    if new_mems:
                        console.print()
                        for mem in new_mems:
                            console.print(f"  [dim #aa55ff]🧠 已记住: {mem}[/]")
                        # 更新系统提示中的记忆上下文
                        memory_ctx = build_memory_context()
                        messages[0] = {"role": "system", "content": system_prompt + memory_ctx}

            # 历史长度控制（防止超出上下文窗口）
            # 清理工具交互中间记录，只保留 user/assistant/system
            messages = [m for m in messages if not (
                m["role"] == "user" and "<tool_result>" in m.get("content", "")
            )]
            messages = [m for m in messages if not (
                m["role"] == "assistant" and (
                    "<tool_call>" in m.get("content", "") or
                    "<|tool_call>" in m.get("content", "")
                )
            )]
            non_sys = [m for m in messages if m["role"] != "system"]
            if len(non_sys) > MAX_HISTORY * 2:
                messages = [messages[0]] + non_sys[-(MAX_HISTORY * 2):]

            console.print()

        except KeyboardInterrupt:
            console.print("\n[dim]Ctrl+C 中断，输入 /bye 退出[/]")
        except EOFError:
            # Ctrl+D 退出
            if any(m["role"] == "user" for m in messages):
                save_session(session_id, messages, system_prompt, session_title)
            console.print("\n[bold #00ddff]再见！👋[/]")
            break
