import sys
import os

# Add the project root to sys.path so we can import aichat
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_root)

from aichat import ui
from rich.console import Console

# Create assets directory
os.makedirs(os.path.join(project_root, "assets"), exist_ok=True)

# Create a new console with recording enabled
recording_console = Console(record=True, force_terminal=True)
ui.console = recording_console  # override the global console

# Generate Banner
ui.show_banner()
recording_console.save_svg(os.path.join(project_root, "assets/banner.svg"), title="AIChat Banner")

# Generate Help
recording_console.clear()
ui.show_help()
recording_console.save_svg(os.path.join(project_root, "assets/help_menu.svg"), title="AIChat Help Menu")

# Generate Status
recording_console.clear()
ui.show_status()
recording_console.save_svg(os.path.join(project_root, "assets/status_panel.svg"), title="AIChat Status")

# Generate chat mockup
recording_console.clear()
from rich.markdown import Markdown

recording_console.print("\n❯ 帮我写一段快排代码，用 Python\n")
recording_console.print("  🤖 [bold #ff9900]AI[/]  [dim]10:30:00[/]\n")

md = Markdown("""
当然，这里是使用 Python 实现的快速排序（Quicksort）代码：

```python
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

# 测试示例
print(quicksort([3,6,8,10,1,2,1]))
```
""", code_theme="monokai")

recording_console.print(md)
recording_console.print("\n  [dim #888888]⏱ 2.1s  |  📝 243 chars[/]\n")
recording_console.save_svg(os.path.join(project_root, "assets/chat_example.svg"), title="AIChat Chatting")

print("Generated SVGs in assets/")
