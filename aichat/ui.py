"""
终端 UI 模块 - 负责所有视觉渲染

包含:
  - ASCII Art 启动横幅
  - 帮助菜单表格
  - 历史会话列表
  - 当前对话摘要
  - 模型状态面板
"""

import requests

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich import box

from . import config
from .history import list_sessions
from .memory import get_all_memories
from .skills import list_skills

# 全局 Console 实例，供所有模块共享
console = Console()


def show_banner():
    """显示启动横幅 - ASCII Art + 蓝色渐变"""
    lines = [
        "     █████╗ ██╗     ██████╗██╗  ██╗ █████╗ ████████╗",
        "    ██╔══██╗██║    ██╔════╝██║  ██║██╔══██╗╚══██╔══╝",
        "    ███████║██║    ██║     ███████║███████║   ██║   ",
        "    ██╔══██║██║    ██║     ██╔══██║██╔══██║   ██║   ",
        "    ██║  ██║██║    ╚██████╗██║  ██║██║  ██║   ██║   ",
        "    ╚═╝  ╚═╝╚═╝     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ",
    ]
    colors = ["#00d4ff", "#00c8ff", "#00bcff", "#00b0ff", "#00a4ff", "#0098ff"]
    text = Text()
    for i, line in enumerate(lines):
        text.append(line + "\n", style=colors[i % len(colors)])
    console.print()
    console.print(Align.center(text))

    # 副标题信息栏
    sub = Text()
    sub.append("  ⚡ 本地大模型终端助手  ", style="bold white on #0055aa")
    sub.append("  ", style="")
    sub.append(f" 🔗 {config.API_BASE} ", style="dim white on #333333")
    sub.append("  ", style="")
    sub.append(f" 🧠 {config.MODEL_NAME} ", style="dim white on #333333")
    console.print(Align.center(sub))
    console.print()


def show_help():
    """显示帮助菜单 - 所有可用斜杠命令"""
    t = Table(
        title="💡 命令列表",
        box=box.DOUBLE_EDGE,
        border_style="#00aaff",
        title_style="bold #00ddff",
        header_style="bold #ff9900",
        show_lines=True,
    )
    t.add_column("命令", style="bold #00ff88", min_width=16)
    t.add_column("说明", style="white", min_width=36)
    for cmd, desc in [
        ("/help",          "显示此帮助菜单"),
        ("/clear",         "清除当前对话，开始新会话"),
        ("/sessions",      "查看所有历史会话列表"),
        ("/load <序号>",    "加载指定历史会话继续对话"),
        ("/delete <序号>",  "删除指定历史会话"),
        ("/history",       "查看当前对话记录摘要"),
        ("/memory",        "查看 AI 记住的关于你的信息"),
        ("/remember <内容>","手动添加一条记忆"),
        ("/forget <序号>",  "删除指定记忆条目"),
        ("/forget all",    "清除所有记忆"),
        ("/skills",        "查看所有可用技能"),
        ("/skill <序号>",   "激活指定技能（切换到技能模式）"),
        ("/skill off",     "关闭技能，回到普通对话模式"),
        ("/model",         "显示模型与连接信息"),
        ("/system <词>",    "设置系统提示词"),
        ("/bye",           "退出程序"),
    ]:
        t.add_row(cmd, desc)
    console.print()
    console.print(t)
    console.print()


def show_sessions():
    """
    显示历史会话列表表格。

    返回:
        list[dict]: 会话元数据列表（供 /load、/delete 使用）
    """
    sessions = list_sessions()
    if not sessions:
        console.print("[dim]暂无历史会话。[/]")
        return []

    t = Table(
        title=f"📂 历史会话 ({len(sessions)} 个)",
        box=box.ROUNDED,
        border_style="#0088cc",
        title_style="bold #00ddff",
        header_style="bold #ff9900",
        show_lines=True,
    )
    t.add_column("序号", style="bold #00ff88", width=4, justify="center")
    t.add_column("标题", style="white", max_width=40)
    t.add_column("消息数", style="dim", width=6, justify="center")
    t.add_column("最后更新", style="dim #888888", width=16)

    for i, s in enumerate(sessions, 1):
        updated = s.get("updated_at", "?")[:16].replace("T", " ")
        t.add_row(str(i), s.get("title", "?"),
                  str(s.get("message_count", 0)), updated)

    console.print()
    console.print(t)
    console.print("[dim]使用 /load <序号> 加载会话  •  /delete <序号> 删除会话[/]")
    console.print()
    return sessions


def show_status():
    """显示模型与连接状态面板"""
    ok, models = False, []
    try:
        r = requests.get(f"{config.API_BASE}/v1/models", timeout=5)
        if r.status_code == 200:
            ok = True
            models = [m.get("id", "?") for m in r.json().get("data", [])]
    except Exception:
        pass

    console.print(Panel(
        f"[bold #00ddff]服务地址:[/] {config.API_BASE}\n"
        f"[bold #00ddff]模型名称:[/] {config.MODEL_NAME}\n"
        f"[bold #00ddff]上下文长度:[/] 32768 tokens\n"
        f"[bold #00ddff]已加载模型:[/] {', '.join(models) or '无法获取'}\n"
        f"[bold #00ddff]连接状态:[/] {'🟢 已连接' if ok else '🔴 无法连接'}",
        title="[bold #ff9900]🧠 模型信息[/]",
        border_style="#0088cc",
        box=box.ROUNDED,
        padding=(1, 2),
    ))


def show_history(messages):
    """显示当前对话的消息摘要表格"""
    pairs = [(m["role"], m["content"]) for m in messages if m["role"] != "system"]
    if not pairs:
        console.print("[dim]暂无对话记录。[/]")
        return

    t = Table(
        title=f"📜 当前对话 ({len(pairs)} 条)",
        box=box.SIMPLE_HEAVY,
        border_style="#555555",
        title_style="bold #00ddff",
    )
    t.add_column("#", style="dim", width=4)
    t.add_column("角色", width=6)
    t.add_column("内容摘要", max_width=60)

    for i, (role, content) in enumerate(pairs, 1):
        label = "[#00ff88]You[/]" if role == "user" else "[#ff9900]AI[/]"
        s = content[:60].replace("\n", " ") + ("..." if len(content) > 60 else "")
        t.add_row(str(i), label, s)
    console.print(t)


def show_memories():
    """显示所有持久化记忆"""
    memories = get_all_memories()
    if not memories:
        console.print("[dim]🧠 暂无记忆。AI 会在对话中自动记住关于你的重要信息。[/]")
        return

    t = Table(
        title=f"🧠 AI 记忆 ({len(memories)} 条)",
        box=box.ROUNDED,
        border_style="#aa55ff",
        title_style="bold #cc77ff",
        header_style="bold #ff9900",
        show_lines=True,
    )
    t.add_column("序号", style="bold #00ff88", width=4, justify="center")
    t.add_column("记忆内容", style="white", max_width=50)
    t.add_column("来源", style="dim", width=6, justify="center")
    t.add_column("时间", style="dim #888888", width=16)

    for i, m in enumerate(memories, 1):
        source_label = "自动" if m.get("source") == "auto" else "手动"
        created = m.get("created_at", "?")[:16].replace("T", " ")
        t.add_row(str(i), m["content"], source_label, created)

    console.print()
    console.print(t)
    console.print("[dim]使用 /remember <内容> 手动添加  •  /forget <序号> 删除  •  /forget all 全部清除[/]")
    console.print()


def show_skills(active_skill_id=None):
    """
    显示所有可用技能列表。

    参数:
        active_skill_id: 当前激活的技能 ID（用于标记）

    返回:
        list[dict]: 技能列表
    """
    skills = list_skills()
    if not skills:
        console.print("[dim]skills/ 目录下没有技能文件。[/]")
        console.print("[dim]创建 .md 文件即可添加技能，格式参见已有示例。[/]")
        return []

    t = Table(
        title="🎯 可用技能",
        box=box.ROUNDED,
        border_style="#ff8800",
        title_style="bold #ffaa00",
        header_style="bold #ff9900",
        show_lines=True,
    )
    t.add_column("序号", style="bold #00ff88", width=4, justify="center")
    t.add_column("名称", style="white", min_width=12)
    t.add_column("说明", style="dim", max_width=40)
    t.add_column("状态", width=8, justify="center")

    for i, s in enumerate(skills, 1):
        is_active = (s["id"] == active_skill_id) if active_skill_id else False
        status = "[bold #00ff88]● 激活[/]" if is_active else "[dim]○[/]"
        t.add_row(str(i), s["name"], s["description"], status)

    console.print()
    console.print(t)
    console.print("[dim]使用 /skill <序号> 激活  •  /skill off 关闭技能回到普通模式[/]")
    console.print()
    return skills
