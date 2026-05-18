"""QAnything 风格的父子文档回填。"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Literal

from .hybrid_retriever import HybridSearchResult
from .reranker import RerankResult
from .vector_store import SearchResult

ParentMode = Literal["none", "page", "window"]
SearchLikeResult = SearchResult | HybridSearchResult | RerankResult


class ParentDocumentStore:
    """基于已有 child chunk 元数据构建轻量 parent 文档库。"""

    def __init__(self, chunks: list[dict]):
        """按 source/page 为 child chunk 建立页级索引。"""
        self.page_chunks: dict[str, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))
        for order, chunk in enumerate(chunks):
            source = str(chunk.get("source") or chunk.get("doc_id") or "")
            for page in parse_pages(chunk.get("pages") or []):
                copied = deepcopy(chunk)
                copied["_parent_order"] = order
                self.page_chunks[source][page].append(copied)
        for pages in self.page_chunks.values():
            for page_chunks in pages.values():
                page_chunks.sort(key=lambda item: (item.get("_parent_order", 0), str(item.get("chunk_id") or "")))

    def make_parent_chunk(
        self,
        child_chunk: dict,
        mode: ParentMode = "page",
        window_pages: int = 0,
        max_chars: int = 0,
    ) -> dict:
        """把命中的 child chunk 回填为 page/window 级 parent chunk。"""
        if mode == "none":
            return deepcopy(child_chunk)

        source = str(child_chunk.get("source") or child_chunk.get("doc_id") or "")
        child_pages = parse_pages(child_chunk.get("pages") or [])
        if not source or not child_pages:
            return deepcopy(child_chunk)

        parent_pages = self._parent_pages(source, child_pages, mode, window_pages)
        parent_text = self._join_pages(source, parent_pages)
        if not parent_text:
            return deepcopy(child_chunk)

        anchor_text = str(child_chunk.get("text") or "")
        parent_text = trim_around_anchor(parent_text, anchor_text, max_chars=max_chars)
        parent_id = make_parent_id(source, parent_pages, mode)
        parent_chunk = deepcopy(child_chunk)
        parent_chunk.update(
            {
                "chunk_id": parent_id,
                "parent_id": parent_id,
                "child_chunk_id": child_chunk.get("chunk_id"),
                "pages": parent_pages,
                "text": parent_text,
                "chunk_type": f"parent_{mode}",
                "has_table": self._parent_has_table(source, parent_pages),
            }
        )
        metadata = dict(parent_chunk.get("metadata") or {})
        metadata.update(
            {
                "parent_mode": mode,
                "parent_window_pages": window_pages if mode == "window" else 0,
                "child_chunk_id": child_chunk.get("chunk_id"),
            }
        )
        parent_chunk["metadata"] = metadata
        parent_chunk["child_hits"] = [child_hit_metadata(child_chunk)]
        return parent_chunk

    def _parent_pages(self, source: str, child_pages: list[int], mode: ParentMode, window_pages: int) -> list[int]:
        """根据 parent 模式决定应该回填哪些页。"""
        available = self.page_chunks.get(source, {})
        if mode == "page":
            return sorted(page for page in set(child_pages) if page in available)
        start = min(child_pages) - max(0, window_pages)
        end = max(child_pages) + max(0, window_pages)
        return sorted(page for page in available if start <= page <= end)

    def _join_pages(self, source: str, pages: list[int]) -> str:
        """把 parent 页内的 child chunk 重新拼接成上下文。"""
        page_texts: list[str] = []
        for page in pages:
            chunks = self.page_chunks.get(source, {}).get(page, [])
            texts = [str(chunk.get("text") or "").strip() for chunk in chunks if str(chunk.get("text") or "").strip()]
            if not texts:
                continue
            page_text = "\n".join(dedupe_keep_order(texts))
            if len(pages) > 1:
                page_text = f"[第 {page} 页]\n{page_text}"
            page_texts.append(page_text)
        return "\n\n".join(page_texts).strip()

    def _parent_has_table(self, source: str, pages: list[int]) -> bool:
        """判断 parent 覆盖范围内是否包含表格。"""
        return any(
            bool(chunk.get("has_table"))
            for page in pages
            for chunk in self.page_chunks.get(source, {}).get(page, [])
        )


def expand_results_to_parents(
    results: list[SearchLikeResult],
    parent_store: ParentDocumentStore,
    mode: ParentMode,
    window_pages: int = 0,
    max_chars: int = 0,
    top_k: int | None = None,
) -> list[SearchLikeResult]:
    """把召回结果中的 child chunk 去重回填为 parent chunk。"""
    if mode == "none":
        return results[:top_k] if top_k else list(results)

    expanded: list[SearchLikeResult] = []
    parent_positions: dict[str, int] = {}
    for result in results:
        parent_chunk = parent_store.make_parent_chunk(
            result.chunk,
            mode=mode,
            window_pages=window_pages,
            max_chars=max_chars,
        )
        parent_id = str(parent_chunk.get("parent_id") or parent_chunk.get("chunk_id") or "")
        if parent_id in parent_positions:
            existing = expanded[parent_positions[parent_id]].chunk
            existing.setdefault("child_hits", []).append(child_hit_metadata(result.chunk))
            continue
        parent_positions[parent_id] = len(expanded)
        expanded.append(copy_result_with_chunk(result, parent_chunk))
        if top_k is not None and len(expanded) >= top_k:
            break

    rerank_positions(expanded)
    return expanded


def copy_result_with_chunk(result: SearchLikeResult, chunk: dict) -> SearchLikeResult:
    """复制检索结果，同时替换为 parent chunk。"""
    if isinstance(result, RerankResult):
        return RerankResult(
            score=result.score,
            rank=result.rank,
            chunk=chunk,
            retrieval_score=result.retrieval_score,
            retrieval_rank=result.retrieval_rank,
            rerank_score=result.rerank_score,
        )
    if isinstance(result, HybridSearchResult):
        return HybridSearchResult(
            score=result.score,
            rank=result.rank,
            chunk=chunk,
            vector_score=result.vector_score,
            bm25_score=result.bm25_score,
            vector_rank=result.vector_rank,
            bm25_rank=result.bm25_rank,
            vector_norm=result.vector_norm,
            bm25_norm=result.bm25_norm,
        )
    return SearchResult(score=result.score, rank=result.rank, chunk=chunk)


def rerank_positions(results: list[SearchLikeResult]) -> None:
    """按当前顺序重新写入 rank。"""
    for rank, result in enumerate(results, start=1):
        result.rank = rank


def parse_pages(value: object) -> list[int]:
    """解析 chunk 中的 1-based 页码。"""
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
    return sorted(pages)


def make_parent_id(source: str, pages: list[int], mode: ParentMode) -> str:
    """生成稳定的 parent chunk id。"""
    page_text = "-".join(str(page) for page in pages)
    safe_source = source.replace("/", "_").replace("\\", "_")
    return f"parent-{mode}-{safe_source}-p{page_text}"


def child_hit_metadata(chunk: dict) -> dict:
    """记录 parent 来源于哪些 child chunk 命中。"""
    return {
        "chunk_id": chunk.get("chunk_id"),
        "source": chunk.get("source"),
        "pages": chunk.get("pages"),
    }


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


def trim_around_anchor(text: str, anchor: str, max_chars: int = 0) -> str:
    """在过长 parent 中尽量保留命中的 child 附近上下文。"""
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    anchor = anchor.strip()
    anchor_at = text.find(anchor[: min(len(anchor), 80)]) if anchor else -1
    if anchor_at < 0:
        return text[:max_chars].rstrip()
    start = max(0, anchor_at - max_chars // 3)
    end = min(len(text), start + max_chars)
    start = max(0, end - max_chars)
    return text[start:end].strip()
