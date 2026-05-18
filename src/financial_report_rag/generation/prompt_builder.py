"""构造金融 RAG 回答生成提示词。"""

from __future__ import annotations


SYSTEM_PROMPT = """你是金融研报与政策文档问答助手。
你必须只根据用户提供的资料回答问题，不要使用资料外的知识。
你必须优先摘录资料中的原始表述和原始数字，不要自行计算、反推或换算，除非问题明确要求计算。
如果资料中有多个相似数字，必须选择与问题中的公司/政策、年份或季度、指标名称完全匹配的数字。
不要用相近但不同口径的指标替代答案，例如不要用归母净利润替代净利润、不要用利润替代营收、不要用年度预测替代季度实际值。
如果资料不足以回答，请明确说明“根据现有资料无法确定”，但不要在已有直接证据时轻易说无法确定。
回答中需要保留关键数字、口径和时间，并用 [资料1] 这样的编号标注依据。
不要编造来源、页码、公司名称、政策名称或资料中没有的细节。
回答前请自检：结论是否和列出的数字一致，引用是否支撑答案，是否混入了与问题无关的扩展内容。"""


QUESTION_TYPE_INSTRUCTIONS = {
    "fact": """这是事实型问题。
- 只回答问题所问的那个指标，优先给出“数字 + 单位 + 时间口径 + 引用”。
- 不要展开分析，不要自行计算估值、比率、同比或差值。
- 如果资料中同时出现多个年份、季度或口径，只能选择与问题完全匹配的一项。
- 如果确实找不到完全匹配项，说明缺失的是哪个口径，不要拿相近指标替代。""",
    "compare": """这是对比型问题。
- 必须分别列出两个对比对象的同口径数字和引用，再给出结论。
- 不能只回答其中一方；如果一方缺失，必须明确说明缺失哪一方、缺失什么指标。
- 不要用不同口径比较，例如不要用营收目标对比实际营收、不要用净利润对比营收。
- 最终结论必须与列出的数字大小关系一致。""",
    "summary": """这是汇总型问题。
- 只围绕问题要求的维度归纳，不要把资料里的所有相关背景都铺开。
- 尽量使用资料原文中的政策目标、任务、机制、领域和关键数字。
- 不要随意新增资料中没有的分类、案例、措施或解释。
- 优先按问题中的对象或政策来源组织答案，每个要点都要有资料编号。
- 答案要简洁完整：覆盖关键方向，但避免冗长扩展和泛泛表述。""",
}


OUTPUT_REQUIREMENTS = {
    "fact": """建议输出格式：
直接答案：……
依据：……[资料X]""",
    "compare": """建议输出格式：
- 对象A：数字、口径、引用
- 对象B：数字、口径、引用
结论：……""",
    "summary": """建议输出格式：
1. 要点：原文相关政策目标/机制/措施。[资料X]
2. 要点：原文相关政策目标/机制/措施。[资料Y]
结论：用一句话概括，不新增资料外判断。""",
}


def build_answer_messages(query: str, question_type: str, context_text: str) -> list[dict[str, str]]:
    """生成 Chat Completions 需要的 messages。"""
    question_type = normalize_question_type(question_type)
    user_prompt = f"""问题类型：{question_type}
任务要求：{QUESTION_TYPE_INSTRUCTIONS[question_type]}
输出要求：{OUTPUT_REQUIREMENTS[question_type]}

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
