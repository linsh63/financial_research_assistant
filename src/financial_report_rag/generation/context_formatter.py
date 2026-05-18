"""把 routed 检索结果整理成可放入 prompt 的上下文。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from financial_report_rag.retrieval.parent_document import SearchLikeResult


@dataclass
class ContextFormatConfig:
    """控制进入 LLM 的上下文数量和长度。"""

    max_contexts: int = 8
    max_chars_per_context: int = 1800
    max_total_chars: int = 9000


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


def format_contexts(results: list[SearchLikeResult], config: ContextFormatConfig | None = None) -> FormattedContexts:
    """把检索结果转换成带编号的资料块。"""
    config = config or ContextFormatConfig()
    contexts: list[FormattedContext] = []
    total_chars = 0

    for result in results[: config.max_contexts]:
        chunk = result.chunk
        text = normalize_text(str(chunk.get("text") or ""))
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
