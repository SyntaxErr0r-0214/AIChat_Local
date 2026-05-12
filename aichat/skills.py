"""
技能模块 - 管理可切换的 AI 技能/角色

Skill 是一组预定义的系统提示词，可以让 AI 切换到不同的工作模式。
例如：翻译助手、代码审查、写作助手等。

技能文件格式（.md 文件，放在 skills/ 目录下）:
────────────────────────────
---
name: 翻译助手
description: 专业的多语言翻译工具
---
你是一个专业的翻译助手。用户发送任何语言的文本，
你都应该将其翻译为用户指定的目标语言...
────────────────────────────

文件名即为技能 ID（不含扩展名），如 translator.md → ID 为 "translator"
"""

import os
import re

from .config import PROJECT_DIR

# 技能文件存储目录
SKILLS_DIR = os.path.join(PROJECT_DIR, "skills")


def ensure_skills_dir():
    """确保技能目录存在"""
    os.makedirs(SKILLS_DIR, exist_ok=True)


def _parse_skill_file(filepath):
    """
    解析技能文件，提取元数据和提示词内容。

    技能文件使用 YAML front matter 格式：
    ---
    name: 技能名称
    description: 技能描述
    ---
    这里是系统提示词内容...

    参数:
        filepath: 技能文件完整路径

    返回:
        dict: {
            "id": "文件名（不含扩展名）",
            "name": "技能名称",
            "description": "技能描述",
            "prompt": "系统提示词内容",
            "filepath": "文件路径"
        }
    """
    skill_id = os.path.splitext(os.path.basename(filepath))[0]

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()

    name = skill_id       # 默认名称为文件名
    description = ""      # 默认无描述
    prompt = content      # 默认整个文件都是提示词

    # 尝试解析 YAML front matter（--- 包裹的头部）
    fm_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(fm_pattern, content, re.DOTALL)

    if match:
        # 解析头部元数据
        header = match.group(1)
        prompt = match.group(2).strip()

        for line in header.split("\n"):
            line = line.strip()
            if line.startswith("name:"):
                name = line[5:].strip()
            elif line.startswith("description:"):
                description = line[12:].strip()

    return {
        "id": skill_id,
        "name": name,
        "description": description,
        "prompt": prompt,
        "filepath": filepath,
    }


def list_skills():
    """
    列出所有可用技能。

    返回:
        list[dict]: 技能列表，每个包含 id, name, description, prompt, filepath
    """
    ensure_skills_dir()
    skills = []
    for fname in sorted(os.listdir(SKILLS_DIR)):
        if fname.endswith((".md", ".txt")):
            try:
                skill = _parse_skill_file(os.path.join(SKILLS_DIR, fname))
                skills.append(skill)
            except Exception:
                continue
    return skills


def load_skill(skill_id):
    """
    通过 ID 或序号加载指定技能。

    参数:
        skill_id: 技能文件名（不含扩展名）

    返回:
        dict 或 None: 技能数据，未找到返回 None
    """
    skills = list_skills()
    for s in skills:
        if s["id"] == skill_id:
            return s
    return None


def load_skill_by_index(index):
    """
    通过序号（0-based）加载指定技能。

    返回:
        dict 或 None
    """
    skills = list_skills()
    if 0 <= index < len(skills):
        return skills[index]
    return None


def create_example_skills():
    """
    如果 skills/ 目录为空，创建示例技能文件，
    让用户了解技能文件的格式。
    """
    ensure_skills_dir()

    # 检查是否已有技能文件
    existing = [f for f in os.listdir(SKILLS_DIR) if f.endswith((".md", ".txt"))]
    if existing:
        return  # 已有文件，不覆盖

    # 示例1: 翻译助手
    translator = """---
name: 翻译助手
description: 专业多语言翻译，支持中英日韩等语言互译
---
你是一个专业的多语言翻译助手。

规则：
1. 用户发送中文时，翻译为英文
2. 用户发送英文时，翻译为中文
3. 用户发送其他语言时，翻译为中文和英文
4. 如果用户指定了目标语言，按指定语言翻译
5. 保持原文的语气、风格和格式
6. 对于专业术语，提供多种可能的翻译并解释差异
7. 翻译后简要说明关键词的翻译选择理由"""

    # 示例2: 代码审查
    code_review = """---
name: 代码审查
description: 专业代码审查，发现问题并提供改进建议
---
你是一位资深的代码审查专家。

当用户提交代码时，请按以下维度进行审查：

1. **正确性**: 逻辑错误、边界条件、空指针等
2. **安全性**: SQL注入、XSS、敏感信息泄露等
3. **性能**: 时间复杂度、内存泄漏、不必要的计算
4. **可读性**: 命名规范、代码结构、注释质量
5. **最佳实践**: 设计模式、SOLID原则、语言惯用法

输出格式：
- 🔴 严重问题（必须修复）
- 🟡 建议改进（推荐修复）
- 🟢 优点（值得表扬的地方）
- 最后给出总体评分（1-10分）和改进建议摘要"""

    # 示例3: 写作助手
    writer = """---
name: 写作助手
description: 帮助润色、改写、扩展文本内容
---
你是一位专业的写作助手，擅长中文和英文写作。

你的能力包括：
1. **润色**: 改善语句流畅度、修正语法错误、提升文采
2. **改写**: 用不同风格重写内容（正式/口语/学术/文学）
3. **扩展**: 根据大纲或要点扩展为完整文章
4. **缩写**: 将长文精炼为摘要
5. **纠错**: 检查并修正拼写、语法、标点错误

请始终保持原文的核心意思，并在修改处用【】标注说明修改理由。"""

    # 写入示例文件
    examples = {
        "translator.md": translator,
        "code_review.md": code_review,
        "writer.md": writer,
    }
    for fname, content in examples.items():
        filepath = os.path.join(SKILLS_DIR, fname)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
