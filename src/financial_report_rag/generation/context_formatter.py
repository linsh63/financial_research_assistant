"""把 routed 检索结果整理成可放入 prompt 的上下文。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from financial_report_rag.retrieval.parent_document import SearchLikeResult


@dataclass
class ContextFormatConfig:
    """控制进入 LLM 的上下文数量和长度。"""

    max_contexts: int = 8
    max_chars_per_context: int = 1800
    max_total_chars: int = 9000
    child_hit_max_chars: int = 1200
    snippet_window_chars: int = 1200
    max_snippets_per_context: int = 2


@dataclass
class FormattedContext:
    """保存单条证据文本和引用信息。"""

    index: int
    source: str
    pages: list[int]
    chunk_id: str
    score: float
    text: str


@dataclass
class FormattedContexts:
    """保存 prompt 上下文文本和结构化引用。"""

    text: str
    references: list[dict]
    contexts: list[FormattedContext]


def format_contexts(
    results: list[SearchLikeResult],
    config: ContextFormatConfig | None = None,
    query: str = "",
    question_type: str = "",
) -> FormattedContexts:
    """把检索结果转换成带编号的资料块。"""
    config = config or ContextFormatConfig()
    contexts: list[FormattedContext] = []
    total_chars = 0

    for result in results[: config.max_contexts]:
        chunk = result.chunk
        text = build_context_text(chunk, query=query, question_type=question_type, config=config)
        if not text:
            continue
        text = text[: config.max_chars_per_context].strip()
        if total_chars + len(text) > config.max_total_chars:
            remaining = config.max_total_chars - total_chars
            if remaining <= 100:
                break
            text = text[:remaining].strip()
        context = FormattedContext(
            index=len(contexts) + 1,
            source=str(chunk.get("source") or ""),
            pages=parse_pages(chunk.get("pages") or []),
            chunk_id=str(chunk.get("chunk_id") or ""),
            score=float(result.score),
            text=text,
        )
        contexts.append(context)
        total_chars += len(text)
        if total_chars >= config.max_total_chars:
            break

    return FormattedContexts(
        text=render_context_text(contexts),
        references=[context_reference(context) for context in contexts],
        contexts=contexts,
    )


def render_context_text(contexts: list[FormattedContext]) -> str:
    """渲染 LLM 可读的资料块文本。"""
    blocks: list[str] = []
    for context in contexts:
        source_name = Path(context.source).name if context.source else ""
        page_text = ",".join(str(page) for page in context.pages) if context.pages else "-"
        blocks.append(
            "\n".join(
                [
                    f"[资料{context.index}] source={source_name} pages={page_text} score={context.score:.4f}",
                    context.text,
                ]
            )
        )
    return "\n\n".join(blocks)


def context_reference(context: FormattedContext) -> dict:
    """生成结构化引用，便于后续保存到 JSONL。"""
    return {
        "ref_id": f"资料{context.index}",
        "source": context.source,
        "pages": context.pages,
        "chunk_id": context.chunk_id,
        "score": context.score,
    }


def build_context_text(chunk: dict, query: str, question_type: str, config: ContextFormatConfig) -> str:
    """把 child 命中片段、相关片段和父页上下文合并成一条证据。"""
    parent_text = normalize_text(str(chunk.get("text") or ""))
    if not parent_text:
        return ""
    if question_type in {"compare", "summary"}:
        return parent_text

    blocks: list[str] = []
    child_texts = collect_child_hit_texts(chunk, config.child_hit_max_chars)
    if child_texts:
        blocks.append("【命中片段】\n" + "\n\n".join(child_texts))

    snippets = query_snippets(parent_text, query=query, config=config)
    if snippets:
        blocks.append("【相关片段】\n" + "\n\n".join(snippets))

    if not should_skip_parent_context(question_type, child_texts, snippets, parent_text):
        blocks.append("【父页上下文】\n" + parent_text)

    return "\n\n".join(dedupe_keep_order(blocks)).strip()


def collect_child_hit_texts(chunk: dict, max_chars: int) -> list[str]:
    """从 parent chunk 中取回原始命中的 child 文本。"""
    child_texts: list[str] = []
    for hit in chunk.get("child_hits") or []:
        if not isinstance(hit, dict):
            continue
        text = normalize_text(str(hit.get("text") or ""))
        if not text:
            continue
        child_texts.append(text[:max_chars].strip())
    return dedupe_keep_order(child_texts)


def should_skip_parent_context(question_type: str, child_texts: list[str], snippets: list[str], parent_text: str) -> bool:
    """事实题证据已足够集中时，减少父页全文干扰。"""
    if question_type != "fact":
        return False
    focused_chars = sum(len(text) for text in child_texts + snippets)
    return focused_chars >= min(1600, max(600, len(parent_text) // 3))


def query_snippets(parent_text: str, query: str, config: ContextFormatConfig) -> list[str]:
    """围绕查询词抽取父页中的高相关片段，避免从页首截断丢证据。"""
    terms = extract_query_terms(query)
    if not terms:
        return []

    candidates = score_lines(parent_text, terms)
    if not candidates:
        return []

    snippets: list[str] = []
    used_ranges: list[tuple[int, int]] = []
    for _, start, end in candidates:
        snippet_start, snippet_end = expand_range(parent_text, start, end, config.snippet_window_chars)
        if overlaps_existing(snippet_start, snippet_end, used_ranges):
            continue
        snippet = parent_text[snippet_start:snippet_end].strip()
        if snippet:
            snippets.append(snippet)
            used_ranges.append((snippet_start, snippet_end))
        if len(snippets) >= config.max_snippets_per_context:
            break
    return snippets


def extract_query_terms(query: str) -> list[str]:
    """从问题中抽取公司、年份、季度和指标词。"""
    normalized = normalize_for_match(query)
    terms: list[str] = []

    for term in re.findall(r"[A-Za-z]+(?:/[A-Za-z]+)?|\d{4}[A-Za-z]?|\d{2}Q[1-4]|Q[1-4]", query):
        terms.append(normalize_for_match(term))

    metric_terms = [
        "P/E",
        "P/B",
        "PE",
        "PB",
        "有息负债",
        "产品销售收入",
        "归母净利润",
        "归属母公司净利润",
        "营业总收入",
        "营业收入",
        "主营收入",
        "营收",
        "净利润",
        "毛利率",
        "销售毛利率",
        "研发费用",
    ]
    for term in metric_terms:
        normalized_term = normalize_for_match(term)
        if normalized_term and normalized_term in normalized:
            terms.append(normalized_term)

    terms.extend(metric_synonyms(normalized))

    for segment in re.findall(r"[\u4e00-\u9fff]{2,}", query):
        cleaned = strip_question_words(segment)
        if len(cleaned) >= 2:
            terms.append(normalize_for_match(cleaned))
        if len(cleaned) >= 6:
            for size in (4, 5, 6):
                for index in range(0, len(cleaned) - size + 1):
                    terms.append(normalize_for_match(cleaned[index : index + size]))

    return [term for term in dedupe_keep_order(terms) if term and term not in stop_terms()]


def metric_synonyms(normalized_query: str) -> list[str]:
    """补充财报常见指标别名，避免同义口径漏抽相关片段。"""
    synonyms: list[str] = []
    if "归母净利润" in normalized_query or "归属母公司净利润" in normalized_query:
        synonyms.extend(["归母净利润", "归属母公司净利润", "归属于母公司净利润"])
    if "pb" in normalized_query or "p/b" in normalized_query or "市净率" in normalized_query:
        synonyms.extend(["pb", "p/b", "市净率"])
    if "pe" in normalized_query or "p/e" in normalized_query or "市盈率" in normalized_query:
        synonyms.extend(["pe", "p/e", "市盈率"])
    if "营收" in normalized_query or "营业收入" in normalized_query:
        synonyms.extend(["营收", "营业收入", "营业总收入", "主营收入", "产品销售收入"])
    return [normalize_for_match(term) for term in synonyms]


def strip_question_words(text: str) -> str:
    """去掉问题中的泛化问法，保留实体和指标词。"""
    for word in ("多少", "是多少", "预计", "实现", "截至", "根据", "公司", "哪个", "哪家", "相比", "更高"):
        text = text.replace(word, "")
    return text.strip()


def stop_terms() -> set[str]:
    """返回 query 片段中的低价值停用词。"""
    return {
        "多少",
        "是多少",
        "公司",
        "预计",
        "实现",
        "截至",
        "根据",
        "哪个",
        "哪家",
        "相比",
        "更高",
        "资料",
        "现有",
    }


def score_lines(text: str, terms: list[str]) -> list[tuple[float, int, int]]:
    """按查询词覆盖度给每一行打分。"""
    candidates: list[tuple[float, int, int]] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        raw = line.strip()
        start = offset
        end = offset + len(line)
        offset = end
        if not raw:
            continue
        matched = matched_terms(raw, terms)
        if not matched:
            continue
        score = sum(term_weight(term) for term in matched)
        if re.search(r"\d", raw):
            score += 0.5
        candidates.append((score, start, end))
    candidates.sort(key=lambda item: (item[0], item[2] - item[1]), reverse=True)
    return candidates


def matched_terms(text: str, terms: list[str]) -> list[str]:
    """返回某行覆盖的查询词。"""
    normalized = normalize_for_match(text)
    return [term for term in terms if term in normalized]


def term_weight(term: str) -> float:
    """重要指标词和时间词权重更高。"""
    if re.search(r"\d", term):
        return 2.0
    if term in {"pe", "pb", "p/e", "p/b", "有息负债", "产品销售收入", "归母净利润", "归属母公司净利润"}:
        return 2.5
    if len(term) >= 5:
        return 1.5
    return 1.0


def expand_range(text: str, start: int, end: int, max_chars: int) -> tuple[int, int]:
    """围绕命中行扩展固定长度窗口。"""
    center = (start + end) // 2
    snippet_start = max(0, center - max_chars // 2)
    snippet_end = min(len(text), snippet_start + max_chars)
    snippet_start = max(0, snippet_end - max_chars)
    snippet_start = adjust_to_line_start(text, snippet_start)
    snippet_end = adjust_to_line_end(text, snippet_end)
    return snippet_start, snippet_end


def adjust_to_line_start(text: str, index: int) -> int:
    """尽量从完整行开头截取。"""
    if index <= 0:
        return 0
    line_start = text.rfind("\n", 0, index)
    return 0 if line_start < 0 else line_start + 1


def adjust_to_line_end(text: str, index: int) -> int:
    """尽量在完整行末尾结束。"""
    if index >= len(text):
        return len(text)
    line_end = text.find("\n", index)
    return len(text) if line_end < 0 else line_end


def overlaps_existing(start: int, end: int, ranges: list[tuple[int, int]]) -> bool:
    """避免重复抽取高度重叠的片段。"""
    for used_start, used_end in ranges:
        overlap = max(0, min(end, used_end) - max(start, used_start))
        if overlap >= min(end - start, used_end - used_start) * 0.5:
            return True
    return False


def normalize_for_match(text: str) -> str:
    """生成匹配用文本，去掉空白并统一大小写和符号。"""
    return (
        text.lower()
        .replace("，", ",")
        .replace("％", "%")
        .replace("／", "/")
        .replace(" ", "")
        .replace("\n", "")
        .strip()
    )


def normalize_text(text: str) -> str:
    """压缩空白，但保留段落换行。"""
    lines = [" ".join(line.split()) for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def parse_pages(value: object) -> list[int]:
    """解析 1-based 页码列表。"""
    if not isinstance(value, list):
        return []
    pages: list[int] = []
    for page in value:
        try:
            page_int = int(page)
        except (TypeError, ValueError):
            continue
        if page_int not in pages:
            pages.append(page_int)
    return pages


def dedupe_keep_order(texts: list[str]) -> list[str]:
    """按原顺序去掉重复文本。"""
    seen: set[str] = set()
    deduped: list[str] = []
    for text in texts:
        if text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped
