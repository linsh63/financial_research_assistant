"""BM25 与 FAISS 向量检索的融合排序。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .vector_store import SearchResult

FusionMethod = Literal["weighted", "rrf"]


@dataclass
class HybridSearchResult:
    score: float
    rank: int
    chunk: dict
    vector_score: float | None = None
    bm25_score: float | None = None
    vector_rank: int | None = None
    bm25_rank: int | None = None
    vector_norm: float = 0.0
    bm25_norm: float = 0.0


def fuse_results(
    vector_results: list[SearchResult],
    bm25_results: list[SearchResult],
    top_k: int = 5,
    vector_weight: float = 0.5,
    bm25_weight: float = 0.5,
    method: FusionMethod = "weighted",
    vector_higher_is_better: bool = True,
    rrf_k: int = 60,
) -> list[HybridSearchResult]:
    """融合两路召回结果，默认使用指导文档要求的分数加权融合。"""
    if method == "weighted":
        return weighted_score_fusion(
            vector_results,
            bm25_results,
            top_k=top_k,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
            vector_higher_is_better=vector_higher_is_better,
        )
    if method == "rrf":
        return rrf_fusion(
            vector_results,
            bm25_results,
            top_k=top_k,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight,
            rrf_k=rrf_k,
        )
    raise ValueError(f"不支持的融合方式：{method}")


def weighted_score_fusion(
    vector_results: list[SearchResult],
    bm25_results: list[SearchResult],
    top_k: int = 5,
    vector_weight: float = 0.5,
    bm25_weight: float = 0.5,
    vector_higher_is_better: bool = True,
) -> list[HybridSearchResult]:
    """把 BM25 和向量检索分数分别归一化后加权。"""
    vector_norms = normalize_scores(vector_results, higher_is_better=vector_higher_is_better)
    bm25_norms = normalize_scores(bm25_results, higher_is_better=True)
    records = collect_records(vector_results, bm25_results)

    fused: list[HybridSearchResult] = []
    for key, record in records.items():
        vector_norm = vector_norms.get(key, 0.0)
        bm25_norm = bm25_norms.get(key, 0.0)
        score = vector_weight * vector_norm + bm25_weight * bm25_norm
        fused.append(
            HybridSearchResult(
                score=score,
                rank=0,
                chunk=record["chunk"],
                vector_score=record.get("vector_score"),
                bm25_score=record.get("bm25_score"),
                vector_rank=record.get("vector_rank"),
                bm25_rank=record.get("bm25_rank"),
                vector_norm=vector_norm,
                bm25_norm=bm25_norm,
            )
        )

    return rerank(fused, top_k=top_k)


def rrf_fusion(
    vector_results: list[SearchResult],
    bm25_results: list[SearchResult],
    top_k: int = 5,
    vector_weight: float = 0.5,
    bm25_weight: float = 0.5,
    rrf_k: int = 60,
) -> list[HybridSearchResult]:
    """使用 RRF 排名融合，作为加权分数融合的对照方案。"""
    records = collect_records(vector_results, bm25_results)
    fused: list[HybridSearchResult] = []
    for record in records.values():
        vector_rank = record.get("vector_rank")
        bm25_rank = record.get("bm25_rank")
        score = 0.0
        if vector_rank is not None:
            score += vector_weight / (rrf_k + vector_rank)
        if bm25_rank is not None:
            score += bm25_weight / (rrf_k + bm25_rank)
        fused.append(
            HybridSearchResult(
                score=score,
                rank=0,
                chunk=record["chunk"],
                vector_score=record.get("vector_score"),
                bm25_score=record.get("bm25_score"),
                vector_rank=vector_rank,
                bm25_rank=bm25_rank,
            )
        )
    return rerank(fused, top_k=top_k)


def normalize_scores(results: list[SearchResult], higher_is_better: bool = True) -> dict[str, float]:
    """把一路检索分数压到 0-1，便于和另一路加权。"""
    if not results:
        return {}
    keyed_scores = [(result_key(result.chunk), result.score if higher_is_better else -result.score) for result in results]
    scores = [score for _, score in keyed_scores]
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return rank_based_scores(results)
    return {key: (score - min_score) / (max_score - min_score) for key, score in keyed_scores}


def rank_based_scores(results: list[SearchResult]) -> dict[str, float]:
    """当一路分数全部相同时，退化为按排名归一化。"""
    if not results:
        return {}
    if len(results) == 1:
        return {result_key(results[0].chunk): 1.0}
    total = len(results)
    return {
        result_key(result.chunk): (total - index) / total
        for index, result in enumerate(results)
    }


def collect_records(
    vector_results: list[SearchResult],
    bm25_results: list[SearchResult],
) -> dict[str, dict]:
    """按 chunk_id 合并两路召回结果。"""
    records: dict[str, dict] = {}
    for result in vector_results:
        key = result_key(result.chunk)
        records.setdefault(key, {"chunk": result.chunk})
        records[key].update({"vector_score": result.score, "vector_rank": result.rank})
    for result in bm25_results:
        key = result_key(result.chunk)
        records.setdefault(key, {"chunk": result.chunk})
        records[key].update({"bm25_score": result.score, "bm25_rank": result.rank})
    return records


def rerank(results: list[HybridSearchResult], top_k: int) -> list[HybridSearchResult]:
    """按融合分数重新排序并补全最终排名。"""
    results.sort(
        key=lambda result: (
            result.score,
            -(result.vector_rank or 10**9),
            -(result.bm25_rank or 10**9),
        ),
        reverse=True,
    )
    trimmed = results[:top_k]
    for rank, result in enumerate(trimmed, start=1):
        result.rank = rank
    return trimmed


def result_key(chunk: dict) -> str:
    """生成融合时用于去重的 chunk 键。"""
    if chunk.get("chunk_id"):
        return str(chunk["chunk_id"])
    pages = ",".join(str(page) for page in chunk.get("pages", []))
    return f"{chunk.get('doc_id', '')}:{pages}:{chunk.get('text', '')[:80]}"
