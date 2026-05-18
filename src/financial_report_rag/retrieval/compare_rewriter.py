"""compare 问题的检索改写工具。"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


@dataclass
class CompareQueryRewrite:
    """保存一条 compare 问题的结构化改写结果。"""

    question_id: str
    original_query: str
    entities: list[str]
    aspect: str
    sub_queries: list[str]
    merged_query: str
    model: str = ""
    raw_response: str = ""
    rewritten_at: str = ""


def build_compare_rewrite_messages(query: str) -> list[dict[str, str]]:
    """构造只用于检索改写的 LLM prompt。"""
    system_prompt = (
        "你是金融研报 RAG 系统中的检索查询改写器。"
        "你的任务是把对比型问题拆成结构化检索意图，只能服务于召回，不要回答问题。"
        "不要补充外部知识，不要改写公司名、证券简称、年份、指标名称。"
        "如果无法确定两个对比对象，也要尽量从原问题中保留原始短语。"
        "必须只输出一个 JSON 对象，不要输出 Markdown。"
    )
    user_prompt = f"""
请把下面的 compare 问题改写为 JSON：

问题：{query}

JSON 字段要求：
- entities: 两个对比对象，数组，尽量使用原问题中的原文名称。
- aspect: 对比维度或核心指标，字符串，尽量使用原问题中的原文表述。
- sub_queries: 分别面向每个对比对象的检索 query，数组，每个 query 必须包含对应对象、年份/时间口径、aspect。
- merged_query: 保留两个对象和 aspect 的整体检索 query。

输出示例：
{{
  "entities": ["公司A", "公司B"],
  "aspect": "2025 年营业收入",
  "sub_queries": [
    "公司A 2025 年营业收入",
    "公司B 2025 年营业收入"
  ],
  "merged_query": "公司A 公司B 2025 年营业收入 对比"
}}
""".strip()
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_compare_rewrite_response(
    question_id: str,
    original_query: str,
    response_text: str,
    model: str = "",
) -> CompareQueryRewrite:
    """把 LLM 返回文本解析成 CompareQueryRewrite。"""
    data = extract_json_object(response_text)
    entities = normalize_string_list(data.get("entities"))
    aspect = str(data.get("aspect") or "").strip()
    sub_queries = normalize_string_list(data.get("sub_queries"))
    merged_query = str(data.get("merged_query") or "").strip()

    if not sub_queries:
        sub_queries = fallback_sub_queries(original_query, entities, aspect)
    if not merged_query:
        merged_query = " ".join([*entities, aspect, "对比"]).strip() or original_query

    return CompareQueryRewrite(
        question_id=question_id,
        original_query=original_query,
        entities=entities[:2],
        aspect=aspect,
        sub_queries=dedupe_keep_order(sub_queries),
        merged_query=merged_query,
        model=model,
        raw_response=response_text,
        rewritten_at=datetime.now().isoformat(timespec="seconds"),
    )


def extract_json_object(text: str) -> dict:
    """从模型输出中提取 JSON 对象。"""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def normalize_string_list(value: object) -> list[str]:
    """把任意数组字段规整成非空字符串列表。"""
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            result.append(text)
    return result


def fallback_sub_queries(query: str, entities: list[str], aspect: str) -> list[str]:
    """当 LLM 没返回 sub_queries 时，用保守方式兜底。"""
    if len(entities) >= 2:
        return [f"{entity} {aspect}".strip() for entity in entities[:2]]
    return [query]


def dedupe_keep_order(items: Iterable[str]) -> list[str]:
    """按原顺序去重。"""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def compare_rewrite_queries(rewrite: CompareQueryRewrite, include_merged: bool = True) -> list[str]:
    """把结构化改写转成实际用于补召回的 query 列表。"""
    queries = list(rewrite.sub_queries)
    if include_merged and rewrite.merged_query:
        queries.append(rewrite.merged_query)
    return dedupe_keep_order(queries)


def load_compare_rewrites(path: Path) -> dict[str, CompareQueryRewrite]:
    """读取 JSONL 格式的 compare 改写缓存。"""
    rewrites: dict[str, CompareQueryRewrite] = {}
    if not path.exists():
        return rewrites
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            rewrite = CompareQueryRewrite(
                question_id=str(data.get("question_id") or ""),
                original_query=str(data.get("original_query") or ""),
                entities=normalize_string_list(data.get("entities")),
                aspect=str(data.get("aspect") or "").strip(),
                sub_queries=normalize_string_list(data.get("sub_queries")),
                merged_query=str(data.get("merged_query") or "").strip(),
                model=str(data.get("model") or ""),
                raw_response=str(data.get("raw_response") or ""),
                rewritten_at=str(data.get("rewritten_at") or ""),
            )
            if rewrite.question_id:
                rewrites[rewrite.question_id] = rewrite
    return rewrites


def dump_compare_rewrite(rewrite: CompareQueryRewrite) -> str:
    """把改写结果转成单行 JSON。"""
    return json.dumps(asdict(rewrite), ensure_ascii=False)
