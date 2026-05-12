"""
记忆模块 - 实现跨会话的持久化用户记忆

类似 ChatGPT / Gemini 的 Memory 功能:
  - 每轮对话后自动提取值得记住的关键信息
  - 记忆持久化到 JSON 文件，跨会话保留
  - 自动注入到系统提示词，让 AI 始终了解用户背景
  - 支持查看、手动添加、删除记忆

记忆存储格式 (memory.json):
{
  "memories": [
    {
      "id": "a1b2c3d4",
      "content": "用户的名字叫小明",
      "source": "auto",
      "created_at": "2026-05-12T09:00:00"
    },
    ...
  ]
}
"""

import os
import json
import uuid
import requests
from datetime import datetime

from .config import MEMORY_DIR, API_BASE, MODEL_NAME

# 记忆文件路径
MEMORY_FILE = os.path.join(MEMORY_DIR, "memory.json")

# ── 用于提取记忆的提示词 ──
# 这个提示词会发送给模型，要求它从对话中提取值得长期记住的信息
EXTRACT_PROMPT = """你是一个记忆提取助手。请分析以下对话片段，提取出值得长期记住的用户个人信息。

需要提取的信息类型:
- 姓名、昵称、称呼
- 年龄、生日
- 职业、工作、学校
- 居住地、家乡
- 兴趣爱好、偏好
- 技术栈、编程语言偏好
- 家庭成员信息
- 重要的个人经历或目标
- 使用习惯和偏好设置

规则:
1. 只提取明确的事实信息，不要推测
2. 每条记忆用简洁的一句话表达
3. 如果没有值得记住的信息，返回空数组
4. 返回纯 JSON 格式，不要有多余文字

已有记忆（避免重复）:
{existing_memories}

最新对话:
用户: {user_msg}
AI: {ai_msg}

请返回 JSON 格式:
{{"new_memories": ["记忆1", "记忆2"]}}"""


def _load_memory_file():
    """从磁盘加载记忆文件"""
    if not os.path.exists(MEMORY_FILE):
        return {"memories": []}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"memories": []}


def _save_memory_file(data):
    """保存记忆到磁盘"""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_all_memories():
    """
    获取所有记忆条目。

    返回:
        list[dict]: 记忆列表，每条包含 id, content, source, created_at
    """
    data = _load_memory_file()
    return data.get("memories", [])


def add_memory(content, source="auto"):
    """
    添加一条新记忆。

    参数:
        content: 记忆内容（一句话描述）
        source: 来源，"auto"=模型自动提取, "manual"=用户手动添加
    """
    data = _load_memory_file()
    entry = {
        "id": uuid.uuid4().hex[:8],
        "content": content.strip(),
        "source": source,
        "created_at": datetime.now().isoformat(),
    }
    data["memories"].append(entry)
    _save_memory_file(data)
    return entry


def delete_memory(memory_id):
    """
    通过 ID 删除一条记忆。

    返回:
        bool: 是否成功删除
    """
    data = _load_memory_file()
    original_len = len(data["memories"])
    data["memories"] = [m for m in data["memories"] if m["id"] != memory_id]
    if len(data["memories"]) < original_len:
        _save_memory_file(data)
        return True
    return False


def delete_memory_by_index(index):
    """
    通过序号（0-based）删除一条记忆。

    返回:
        tuple: (是否成功, 被删除的记忆内容或None)
    """
    data = _load_memory_file()
    if 0 <= index < len(data["memories"]):
        removed = data["memories"].pop(index)
        _save_memory_file(data)
        return True, removed["content"]
    return False, None


def clear_all_memories():
    """清除所有记忆"""
    _save_memory_file({"memories": []})


def build_memory_context():
    """
    将所有记忆构建为可注入系统提示词的文本块。

    返回:
        str: 格式化的记忆文本，若无记忆则返回空字符串

    示例输出:
        ## 关于用户的记忆
        - 用户的名字叫小明
        - 用户是一名Python开发者
    """
    memories = get_all_memories()
    if not memories:
        return ""
    lines = [m["content"] for m in memories]
    return "\n\n## 关于用户的记忆\n" + "\n".join(f"- {l}" for l in lines)


def extract_memories_from_chat(user_msg, ai_msg):
    """
    调用模型从最新一轮对话中自动提取值得记住的信息。

    这是一个独立的、非流式的 API 调用，不会影响主对话流。
    如果提取失败（网络错误、模型无法返回有效JSON等），
    会静默失败不影响用户体验。

    参数:
        user_msg: 用户的最新消息
        ai_msg: AI 的最新回复

    返回:
        list[str]: 新提取的记忆列表
    """
    # 获取已有记忆，避免重复提取
    existing = get_all_memories()
    existing_text = "\n".join(f"- {m['content']}" for m in existing) if existing else "（暂无）"

    # 构造提取请求
    prompt = EXTRACT_PROMPT.format(
        existing_memories=existing_text,
        user_msg=user_msg,
        ai_msg=ai_msg[:500],  # 截断 AI 回复，节省 token
    )

    try:
        resp = requests.post(
            f"{API_BASE}/v1/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,    # 低温度，确保输出稳定
                "max_tokens": 256,     # 记忆提取不需要长输出
                "stream": False,
            },
            headers={"Content-Type": "application/json"},
            timeout=15,  # 短超时，不阻塞用户太久
        )
        resp.raise_for_status()
        resp.encoding = "utf-8"

        # 解析模型返回的 JSON
        result_text = resp.json()["choices"][0]["message"]["content"].strip()

        # 尝试提取 JSON（模型可能返回 ```json ... ``` 包裹的内容）
        if "```" in result_text:
            # 提取代码块中的 JSON
            start = result_text.find("{")
            end = result_text.rfind("}") + 1
            if start >= 0 and end > start:
                result_text = result_text[start:end]

        result = json.loads(result_text)
        new_memories = result.get("new_memories", [])

        # 保存提取到的新记忆
        added = []
        for mem in new_memories:
            if isinstance(mem, str) and mem.strip():
                add_memory(mem.strip(), source="auto")
                added.append(mem.strip())
        return added

    except Exception:
        # 静默失败 - 记忆提取是增强功能，不应影响核心对话
        return []
