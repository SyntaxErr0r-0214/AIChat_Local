"""
Terminal UI Module - All visual rendering

Contains:
  - ASCII Art startup banner with gradient
  - Help menu table
  - Session history list
  - Conversation summary
  - Model status panel
  - Memory & skills display
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

# Global Console instance, shared across all modules
console = Console()


def show_banner():
    """Display startup banner - gradient ASCII Art"""
    lines = [
        # --- Row 1: HELLO, SIR. ---
        "██╗  ██╗███████╗██╗     ██╗      ██████╗       ███████╗██╗██████╗  ",
        "██║  ██║██╔════╝██║     ██║     ██╔═══██╗      ██╔════╝██║██╔══██╗ ",
        "███████║█████╗  ██║     ██║     ██║   ██║      ███████╗██║██████╔╝ ",
        "██╔══██║██╔══╝  ██║     ██║     ██║   ██║      ╚════██║██║██╔══██╗ ",
        "██║  ██║███████╗███████╗███████╗╚██████╔╝██╗   ███████║██║██║  ██║██╗",
        "╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝ ╚═════╝ ╚═╝   ╚══════╝╚═╝╚═╝  ╚═╝╚═╝",
        
        # --- Row 2: FRIDAY IS ---
        "███████╗██████╗ ██╗██████╗  █████╗ ██╗   ██╗    ██╗███████╗",
        "██╔════╝██╔══██╗██║██╔══██╗██╔══██╗╚██╗ ██╔╝    ██║██╔════╝",
        "█████╗  ██████╔╝██║██║  ██║███████║ ╚████╔╝     ██║███████╗",
        "██╔══╝  ██╔══██╗██║██║  ██║██╔══██║  ╚██╔╝      ██║╚════██║",
        "██║     ██║  ██║██║██████╔╝██║  ██║   ██║       ██║███████║",
        "╚═╝     ╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝  ╚═╝   ╚═╝       ╚═╝╚══════╝",
        
        # --- Row 3: ONLINE ---
        " ██████╗ ███╗   ██╗██╗     ██╗███╗   ██╗███████╗",
        "██╔═══██╗████╗  ██║██║     ██║████╗  ██║██╔════╝",
        "██║   ██║██╔██╗ ██║██║     ██║██╔██╗ ██║█████╗  ",
        "██║   ██║██║╚██╗██║██║     ██║██║╚██╗██║██╔══╝  ",
        "╚██████╔╝██║ ╚████║███████╗██║██║ ╚████║███████╗",
        " ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝"
    ]

    # 18步长渐变：青色 -> 深蓝 -> 霓虹紫 -> 赛博粉
    gradient = [
        "#00ffff", # 1: 高亮青色
        "#00eeff", # 2
        "#00ddff", # 3
        "#00ccff", # 4
        "#00bbff", # 5
        "#00aaff", # 6: 渐渐变蓝
        "#0088ff", # 7
        "#1166ff", # 8
        "#3344ff", # 9: 深海蓝
        "#5522ff", # 10: 步入紫色
        "#7711ff", # 11
        "#9900ff", # 12: 纯正紫
        "#bb00ff", # 13
        "#cc00ee", # 14
        "#dd00cc", # 15: 偏向粉红
        "#ee00aa", # 16
        "#ff0088", # 17
        "#ff0066"  # 18: 霓虹粉
    ]

    text = Text()
    for i, line in enumerate(lines):
        text.append(line + "\n", style=gradient[i])
    console.print()
    console.print(Align.center(text))

    # Author credit
    credit = Text()
    credit.append("  by Julian Zhang  ", style="dim italic #888888")
    console.print(Align.center(credit))
    console.print()


def show_help():
    """Display help menu - all available slash commands"""
    t = Table(
        title="Commands",
        box=box.DOUBLE_EDGE,
        border_style="#00aaff",
        title_style="bold #00ddff",
        header_style="bold #ff9900",
        show_lines=True,
    )
    t.add_column("Command", style="bold #00ff88", min_width=16)
    t.add_column("Description", style="white", min_width=36)
    for cmd, desc in [
        ("/help",           "Show this help menu"),
        ("/clear",          "Clear conversation, start new session"),
        ("/sessions",       "List all saved sessions"),
        ("/load <n>",       "Load a saved session by index"),
        ("/delete <n>",     "Delete a saved session by index"),
        ("/history",        "Show current conversation summary"),
        ("/memory",         "View stored memories about you"),
        ("/remember <...>", "Manually add a memory"),
        ("/forget <n>",     "Delete a memory by index"),
        ("/forget all",     "Clear all memories"),
        ("/skills",         "List available skills"),
        ("/skill <n>",      "Activate a skill by index"),
        ("/skill off",      "Deactivate skill, return to normal mode"),
        ("/connect <url>",  "Change API server address"),
        ("/model",          "Show model & connection info"),
        ("/system <...>",   "Set system prompt"),
        ("/bye",            "Exit"),
    ]:
        t.add_row(cmd, desc)
    console.print()
    console.print(t)
    console.print()


def show_sessions():
    """
    Display session history table.

    Returns:
        list[dict]: Session metadata list (for /load, /delete)
    """
    sessions = list_sessions()
    if not sessions:
        console.print("[dim]No saved sessions.[/]")
        return []

    t = Table(
        title=f"Sessions ({len(sessions)})",
        box=box.ROUNDED,
        border_style="#0088cc",
        title_style="bold #00ddff",
        header_style="bold #ff9900",
        show_lines=True,
    )
    t.add_column("#", style="bold #00ff88", width=4, justify="center")
    t.add_column("Title", style="white", max_width=40)
    t.add_column("Msgs", style="dim", width=6, justify="center")
    t.add_column("Last Updated", style="dim #888888", width=16)

    for i, s in enumerate(sessions, 1):
        updated = s.get("updated_at", "?")[:16].replace("T", " ")
        t.add_row(str(i), s.get("title", "?"),
                  str(s.get("message_count", 0)), updated)

    console.print()
    console.print(t)
    console.print("[dim]/load <n> to load  |  /delete <n> to remove[/]")
    console.print()
    return sessions


def show_status():
    """Display model & connection status panel"""
    ok, models = False, []
    try:
        r = requests.get(f"{config.API_BASE}/v1/models", timeout=5)
        if r.status_code == 200:
            ok = True
            models = [m.get("id", "?") for m in r.json().get("data", [])]
    except Exception:
        pass

    status = "[bold #00ff88]Connected[/]" if ok else "[bold red]Disconnected[/]"
    console.print(Panel(
        f"[bold #00ddff]Server:[/] {config.API_BASE}\n"
        f"[bold #00ddff]Model:[/] {config.MODEL_NAME}\n"
        f"[bold #00ddff]Context:[/] 32768 tokens\n"
        f"[bold #00ddff]Loaded:[/] {', '.join(models) or 'N/A'}\n"
        f"[bold #00ddff]Status:[/] {status}",
        title="[bold #ff9900]Model Info[/]",
        border_style="#0088cc",
        box=box.ROUNDED,
        padding=(1, 2),
    ))


def show_history(messages):
    """Display current conversation message summary"""
    pairs = [(m["role"], m["content"]) for m in messages if m["role"] != "system"]
    if not pairs:
        console.print("[dim]No messages yet.[/]")
        return

    t = Table(
        title=f"Conversation ({len(pairs)} messages)",
        box=box.SIMPLE_HEAVY,
        border_style="#555555",
        title_style="bold #00ddff",
    )
    t.add_column("#", style="dim", width=4)
    t.add_column("Role", width=6)
    t.add_column("Content", max_width=60)

    for i, (role, content) in enumerate(pairs, 1):
        label = "[#00ff88]You[/]" if role == "user" else "[#ff9900]AI[/]"
        s = content[:60].replace("\n", " ") + ("..." if len(content) > 60 else "")
        t.add_row(str(i), label, s)
    console.print(t)


def show_memories():
    """Display all persistent memories"""
    memories = get_all_memories()
    if not memories:
        console.print("[dim]No memories stored. AI will remember important info from conversations.[/]")
        return

    t = Table(
        title=f"Memory ({len(memories)} items)",
        box=box.ROUNDED,
        border_style="#aa55ff",
        title_style="bold #cc77ff",
        header_style="bold #ff9900",
        show_lines=True,
    )
    t.add_column("#", style="bold #00ff88", width=4, justify="center")
    t.add_column("Content", style="white", max_width=50)
    t.add_column("Source", style="dim", width=6, justify="center")
    t.add_column("Time", style="dim #888888", width=16)

    for i, m in enumerate(memories, 1):
        source_label = "auto" if m.get("source") == "auto" else "manual"
        created = m.get("created_at", "?")[:16].replace("T", " ")
        t.add_row(str(i), m["content"], source_label, created)

    console.print()
    console.print(t)
    console.print("[dim]/remember <...> to add  |  /forget <n> to remove  |  /forget all to clear[/]")
    console.print()


def show_skills(active_skill_id=None):
    """
    Display all available skills.

    Args:
        active_skill_id: Currently active skill ID (for marking)

    Returns:
        list[dict]: Skill list
    """
    skills = list_skills()
    if not skills:
        console.print("[dim]No skill files in skills/ directory.[/]")
        console.print("[dim]Add .md files to create skills. See existing examples for format.[/]")
        return []

    t = Table(
        title="Skills",
        box=box.ROUNDED,
        border_style="#ff8800",
        title_style="bold #ffaa00",
        header_style="bold #ff9900",
        show_lines=True,
    )
    t.add_column("#", style="bold #00ff88", width=4, justify="center")
    t.add_column("Name", style="white", min_width=12)
    t.add_column("Description", style="dim", max_width=40)
    t.add_column("Status", width=8, justify="center")

    for i, s in enumerate(skills, 1):
        is_active = (s["id"] == active_skill_id) if active_skill_id else False
        status = "[bold #00ff88]active[/]" if is_active else "[dim]-[/]"
        t.add_row(str(i), s["name"], s["description"], status)

    console.print()
    console.print(t)
    console.print("[dim]/skill <n> to activate  |  /skill off to deactivate[/]")
    console.print()
    return skills
