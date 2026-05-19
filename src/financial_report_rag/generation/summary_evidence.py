"""汇总型问题的证据包构造工具。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .context_formatter import FormattedContexts


@dataclass
class SummaryEvidenceConfig:
    """控制 summary 证据包的压缩强度。"""

    max_points_per_context: int = 6
    max_total_chars: int = 7000
    min_point_chars: int = 18


def build_summary_evidence_pack(
    query: str,
    formatted: FormattedContexts,
    config: SummaryEvidenceConfig | None = None,
) -> str:
    """从 summary 上下文中抽取原文政策要点，减少长上下文噪声。"""
    config = config or SummaryEvidenceConfig()
    blocks: list[str] = []
    total_chars = 0
    query_terms = extract_summary_query_terms(query)

    for context in formatted.contexts:
        points = select_evidence_points(
            context.text,
            query_terms=query_terms,
            max_points=config.max_points_per_context,
            min_chars=config.min_point_chars,
        )
        if not points:
            continue
        source_name = Path(context.source).name if context.source else ""
        page_text = ",".join(str(page) for page in context.pages) if context.pages else "-"
        block = "\n".join(
            [
                f"[资料{context.index}] source={source_name} pages={page_text}",
                *[f"- {point}" for point in points],
            ]
        )
        remaining = config.max_total_chars - total_chars
        if remaining <= 200:
            break
        if len(block) > remaining:
            block = block[:remaining].rstrip()
        blocks.append(block)
        total_chars += len(block)

    if blocks:
        return "\n\n".join(blocks)
    return formatted.text[: config.max_total_chars].strip()


def select_evidence_points(
    text: str,
    query_terms: list[str],
    max_points: int,
    min_chars: int,
) -> list[str]:
    """按查询词、政策关键词和数字密度选择原文要点。"""
    candidates: list[tuple[float, int, str]] = []
    seen: set[str] = set()
    for index, sentence in enumerate(split_policy_sentences(text)):
        point = clean_point(sentence)
        if len(point) < min_chars:
            continue
        key = normalize_for_dedupe(point)
        if not key or key in seen:
            continue
        seen.add(key)
        score = score_policy_point(point, query_terms)
        if score <= 0:
            continue
        candidates.append((score, index, point))

    candidates.sort(key=lambda item: (-item[0], item[1]))
    selected = [point for _score, _index, point in candidates[:max_points]]
    return restore_original_order(selected, text)


def split_policy_sentences(text: str) -> list[str]:
    """把上下文拆成适合抽取的政策句或短段。"""
    paragraphs = merge_wrapped_lines(text)
    raw_parts: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) > 220:
            raw_parts.extend(re.split(r"(?<=[。；;])", paragraph))
        else:
            raw_parts.append(paragraph)
    return [part.strip(" \t-•●◼") for part in raw_parts if part.strip(" \t-•●◼")]


def merge_wrapped_lines(text: str) -> list[str]:
    """先合并 PDF 抽取造成的换行碎片，再进入证据句抽取。"""
    normalized = re.sub(r"\r\n?", "\n", text)
    paragraphs: list[str] = []
    current = ""
    for raw_line in normalized.splitlines():
        line = raw_line.strip(" \t-•●◼")
        if not line:
            if current:
                paragraphs.append(current)
                current = ""
            continue
        if current and should_start_new_paragraph(line, current):
            paragraphs.append(current)
            current = line
            continue
        if current:
            current = join_wrapped_line(current, line)
        else:
            current = line
    if current:
        paragraphs.append(current)
    return paragraphs


def should_start_new_paragraph(line: str, current: str) -> bool:
    """判断新行是否应当另起一段，而不是接到上一行后面。"""
    if line.startswith(("【", "附件", "附表")):
        return True
    if re.match(r"^[（(]?[一二三四五六七八九十0-9]+[）)、.．]", line):
        return True
    if current.endswith(("。", "；", ";")) and len(current) >= 30:
        return True
    return False


def join_wrapped_line(current: str, line: str) -> str:
    """按中英文边界合并被 PDF 换行打断的文本。"""
    if not current:
        return line
    if current.endswith(("。", "；", ";", "：", ":")):
        return f"{current}\n{line}"
    if re.search(r"[\u4e00-\u9fff]$", current) and re.match(r"^[\u4e00-\u9fff，、；：。]", line):
        return current + line
    return f"{current} {line}"


def clean_point(text: str) -> str:
    """清理证据句中的多余空白，但保留原文措辞。"""
    text = collapse_repeated_glyphs(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip("；;。") + ("。" if not text.endswith(("。", "；", ";")) else "")


def collapse_repeated_glyphs(text: str) -> str:
    """压缩 OCR 造成的单字符连续重复噪声。"""
    return re.sub(r"([\u2e80-\u9fffA-Za-z，。：:；;？！、（）()《》【】])\1{2,}", r"\1", text)


def score_policy_point(point: str, query_terms: list[str]) -> float:
    """给候选证据句打分。"""
    score = 0.0
    normalized = normalize_for_match(point)
    for term in query_terms:
        if term and term in normalized:
            score += 2.5
    if POLICY_KEYWORD_RE.search(point):
        score += 2.0
    if NUMBER_RE.search(point):
        score += 2.0
    if STRUCTURE_RE.search(point):
        score += 1.0
    if len(point) > 260:
        score -= 0.8
    return score


def extract_summary_query_terms(query: str) -> list[str]:
    """从 summary 问题中抽取主题词。"""
    text = re.sub(r"^(结合|根据).*?政策[，,]?", "", query.strip())
    terms: list[str] = []
    for segment in re.findall(r"[\u4e00-\u9fffA-Za-z0-9%]+", text):
        for part in re.split(r"以及|及其|和|与|、|/|，|,", segment):
            part = strip_summary_question_words(part)
            if len(part) >= 2:
                terms.append(normalize_for_match(part))
    return dedupe_keep_order([term for term in terms if term])


def strip_summary_question_words(text: str) -> str:
    """去掉 summary 问题里的泛化问法。"""
    for word in (
        "如何",
        "怎么",
        "怎样",
        "主要",
        "哪些",
        "方向",
        "措施",
        "政策",
        "相关",
        "有关",
        "总结",
        "概括",
        "支持",
        "推动",
        "促进",
        "形成",
        "界定",
    ):
        text = text.replace(word, "")
    return text.strip()


def restore_original_order(points: list[str], original_text: str) -> list[str]:
    """按原文出现顺序输出已选要点，减少跳跃感。"""
    return sorted(points, key=lambda point: original_text.find(point[: min(30, len(point))]))


def normalize_for_match(text: str) -> str:
    """用于主题词匹配的规范化。"""
    return re.sub(r"[\s（）()《》“”、，。；;：:,.!?？/\\\-—]+", "", text).lower()


def normalize_for_dedupe(text: str) -> str:
    """用于去重的规范化。"""
    return normalize_for_match(text)[:120]


def dedupe_keep_order(items: list[str]) -> list[str]:
    """按原顺序去重。"""
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


POLICY_KEYWORD_RE = re.compile(
    r"目标|任务|行动|工程|机制|体系|制度|标准|规划|目录|分类|"
    r"推动|推进|支持|鼓励|加快|加强|完善|建立|健全|实施|开展|"
    r"提升|提高|促进|扩大|优化|强化|建设|培育|发展"
)

STRUCTURE_RE = re.compile(r"一是|二是|三是|四是|五是|首先|其次|同时|到20\d{2}年|20\d{2}[—-]20\d{2}年")

NUMBER_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|％|亿元|万亿元|万人|万千瓦|亿千瓦|吨|万吨|亿吨|个|项|类|所|家|倍|百分点)?")
