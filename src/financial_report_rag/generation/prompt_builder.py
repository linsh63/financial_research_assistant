"""构造金融 RAG 回答生成提示词。"""

from __future__ import annotations


SYSTEM_PROMPT = """你是金融研报与政策文档问答助手。
你必须只根据用户提供的资料回答问题，不要使用资料外的知识。
如果资料不足以回答，请明确说明“根据现有资料无法确定”。
回答中需要保留关键数字、口径和时间，并用 [资料1] 这样的编号标注依据。
不要编造来源、页码、公司名称或政策名称。"""


QUESTION_TYPE_INSTRUCTIONS = {
    "fact": "这是事实型问题。请直接回答核心事实或数字，必要时补充同比、时间口径和引用。",
    "compare": "这是对比型问题。请分别列出对比对象的依据数字，再给出结论，避免只回答其中一方。",
    "summary": "这是汇总型问题。请按主题或政策来源归纳，尽量覆盖多个资料来源，答案要简洁但不能遗漏关键方向。",
}


def build_answer_messages(query: str, question_type: str, context_text: str) -> list[dict[str, str]]:
    """生成 Chat Completions 需要的 messages。"""
    question_type = normalize_question_type(question_type)
    user_prompt = f"""问题类型：{question_type}
任务要求：{QUESTION_TYPE_INSTRUCTIONS[question_type]}

问题：
{query}

可用资料：
{context_text}

请根据以上资料回答。"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def normalize_question_type(question_type: str) -> str:
    """规范化问题类型，未知类型按 fact 处理。"""
    normalized = (question_type or "").strip().lower()
    if normalized in QUESTION_TYPE_INSTRUCTIONS:
        return normalized
    return "fact"
