#!/usr/bin/env python3
"""
AIChat 启动入口

职责:
  1. 自动检测并激活项目虚拟环境（免手动 source venv/bin/activate）
  2. 调用 aichat.app.main() 启动主程序

运行方式:
  python3 chat.py
"""

import os
import sys

# ════════════════════════════════════════
# 自动激活虚拟环境
# ════════════════════════════════════════
# 通过检查 sys.prefix 判断当前 Python 是否在 venv 中。
# 如果不在，用 os.execv 替换当前进程为 venv 的 Python。
# 比较 sys.prefix（而非 sys.executable）以避免符号链接导致的死循环。
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, "venv")

if os.path.isdir(VENV_DIR) and not sys.prefix.startswith(VENV_DIR):
    venv_python = os.path.join(VENV_DIR, "bin", "python3")
    if os.path.isfile(venv_python):
        os.execv(venv_python, [venv_python] + sys.argv)

# ════════════════════════════════════════
# 启动主程序
# ════════════════════════════════════════
from aichat.app import main

if __name__ == "__main__":
    main()
