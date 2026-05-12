"""
会话持久化模块 - 管理对话的保存、加载、列表和删除

会话以 JSON 格式存储在 chat_history/ 目录中，
每个会话一个文件，文件名为 {session_id}.json。

JSON 结构:
{
  "session_id": "20260512_090000_a1b2",
  "title": "用户第一条消息的前30字符...",
  "model": "google/gemma-4-e4b",
  "system_prompt": "...",
  "created_at": "2026-05-12T09:00:00",
  "updated_at": "2026-05-12T09:05:00",
  "message_count": 6,
  "messages": [{"role": "system", "content": "..."}, ...]
}
"""

import os
import json
import uuid
from datetime import datetime

from .config import HISTORY_DIR, MODEL_NAME


def ensure_history_dir():
    """确保历史目录存在，不存在则自动创建"""
    os.makedirs(HISTORY_DIR, exist_ok=True)


def gen_session_id():
    """
    生成短会话 ID，格式: 日期_时间_随机4位十六进制
    例如: 20260512_090000_a1b2
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:4]


def auto_title(messages):
    """
    从第一条用户消息自动生成会话标题。
    截取前30个字符，超出部分以省略号替代。
    """
    for m in messages:
        if m["role"] == "user":
            t = m["content"].replace("\n", " ").strip()
            return t[:30] + ("..." if len(t) > 30 else "")
    return "新对话"


def save_session(session_id, messages, system_prompt, title=None):
    """
    保存当前会话到 JSON 文件。

    如果文件已存在，会保留原始的 created_at 时间戳，
    仅更新 updated_at 和消息内容。
    """
    ensure_history_dir()
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")

    # 保留已有文件的创建时间
    created = datetime.now().isoformat()
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                old = json.load(f)
                created = old.get("created_at", created)
        except Exception:
            pass

    data = {
        "session_id": session_id,
        "title": title or auto_title(messages),
        "model": MODEL_NAME,
        "system_prompt": system_prompt,
        "created_at": created,
        "updated_at": datetime.now().isoformat(),
        "message_count": len([m for m in messages if m["role"] != "system"]),
        "messages": messages,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_session(session_id):
    """
    加载指定会话。

    返回:
        tuple: (messages, system_prompt, title)
    """
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["messages"], data.get("system_prompt", ""), data.get("title", "?")


def list_sessions():
    """
    列出所有历史会话元数据，按最后更新时间倒序排列。

    返回:
        list[dict]: 会话元数据列表
    """
    ensure_history_dir()
    sessions = []
    for fname in os.listdir(HISTORY_DIR):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(HISTORY_DIR, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions.append(data)
        except Exception:
            continue
    sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return sessions


def delete_session(session_id):
    """
    删除指定会话文件。

    返回:
        bool: 删除成功返回 True，文件不存在返回 False
    """
    filepath = os.path.join(HISTORY_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False
