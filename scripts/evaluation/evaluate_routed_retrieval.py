#!/usr/bin/env python
"""评估按问题类型路由的检索策略。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import evaluate_retrieval as eval_base


def find_project_root() -> Path:
    """从脚本位置向上查找项目根目录。"""
    for parent in Path(__file__).resolve().parents:
        if (parent / "src" / "financial_report_rag").exists():
            return parent
    raise RuntimeError("无法定位项目根目录")


ROOT = find_project_root()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from financial_report_rag.retrieval.bm25_store import BM25Store  # noqa: E402
from financial_report_rag.retrieval.compare_rewriter import (  # noqa: E402
    CompareQueryRewrite,
    compare_rewrite_queries,
    load_compare_rewrites,
)
from financial_report_rag.retrieval.embeddings import EmbeddingConfig, FlagEmbeddingModel  # noqa: E402
from financial_report_rag.retrieval.hybrid_retriever import HybridSearchResult, fuse_results, result_key  # noqa: E402
from financial_report_rag.retrieval.parent_document import (  # noqa: E402
    ParentDocumentStore,
    SearchLikeResult,
    expand_results_to_parents,
)
from financial_report_rag.retrieval.reranker import CrossEncoderReranker, RerankConfig, RerankResult  # noqa: E402
from financial_report_rag.retrieval.routed_retriever import (  # noqa: E402
    RoutedRetrievalConfig,
    build_compare_entity_query,
    extract_compare_entities,
    merge_compare_candidates,
    route_results,
)
from financial_report_rag.retrieval.vector_store import (  # noqa: E402
    SearchResult,
    load_chunk_metadata,
    load_faiss_index,
    search_index,
)


def parse_args() -> argparse.Namespace:
    """读取路由检索评测参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", default="data/eval/financial_qa_dev.jsonl")
    parser.add_argument("--index-dir", default="data/processed/indexes/bge_large_zh_v15")
    parser.add_argument("--index-type", choices=["flat", "ivf", "hnsw"], default="flat")
    parser.add_argument("--bm25-path", default="")
    parser.add_argument("--vector-weight", type=float, default=0.6)
    parser.add_argument("--bm25-weight", type=float, default=0.4)
    parser.add_argument("--fusion", choices=["weighted", "rrf"], default="weighted")
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--ks", nargs="+", type=int, default=[5, 8])
    parser.add_argument("--match-level", choices=["doc", "page"], default="page")
    parser.add_argument("--embedding-model", default="models/bge-large-zh-v1.5")
    parser.add_argument("--embedding-backend", choices=["sentence-transformers", "flagembedding"], default="sentence-transformers")
    parser.add_argument("--embedding-batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--no-normalize", action="store_true")
    parser.add_argument("--use-fp16", action="store_true")
    parser.add_argument("--reranker-model", default="models/bge-reranker-v2-m3")
    parser.add_argument("--reranker-backend", choices=["flagembedding", "transformers"], default="transformers")
    parser.add_argument("--reranker-batch-size", type=int, default=2)
    parser.add_argument("--reranker-max-length", type=int, default=512)
    parser.add_argument("--score-activation", choices=["none", "sigmoid"], default="none")
    parser.add_argument("--score-threshold", type=float, default=None)
    parser.add_argument("--relative-drop-threshold", type=float, default=None)
    parser.add_argument("--parent-window-pages", type=int, default=1)
    parser.add_argument("--parent-max-chars", type=int, default=0)
    parser.add_argument("--fact-top-k", type=int, default=5)
    parser.add_argument("--compare-candidate-top-k", type=int, default=20)
    parser.add_argument("--compare-entity-top-k", type=int, default=8)
    parser.add_argument("--compare-rewrite-file", default="", help="可选：LLM 生成的 compare query rewrite JSONL。")
    parser.add_argument("--compare-rewrite-top-k", type=int, default=8)
    parser.add_argument("--compare-rewrite-mode", choices=["separate", "supplement"], default="separate")
    parser.add_argument("--compare-rewrite-per-query-keep", type=int, default=2)
    parser.add_argument("--compare-rewrite-include-merged", action="store_true", help="补召回时同时使用 merged_query。")
    parser.add_argument("--compare-parent-fill", action="store_true", help="compare 题按 parent 去重后继续补齐 TopK。")
    parser.add_argument("--compare-parent-fill-pool", type=int, default=12, help="compare parent 补齐前保留的 child 候选池大小。")
    parser.add_argument("--compare-top-k", type=int, default=5)
    parser.add_argument("--summary-candidate-top-k", type=int, default=50)
    parser.add_argument("--summary-top-k", type=int, default=8)
    parser.add_argument("--summary-per-source", type=int, default=2)
    parser.add_argument("--output", default="docs/experiments/rerank/06_routed_retrieval/report.md")
    parser.add_argument("--details-output", default="docs/experiments/rerank/06_routed_retrieval/details.json")
    parser.add_argument("--badcase-limit", type=int, default=20)
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析为绝对路径。"""
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def display_path(path: Path) -> str:
    """优先输出项目相对路径。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def routed_config_from_args(args: argparse.Namespace) -> RoutedRetrievalConfig:
    """从命令行参数生成路由配置。"""
    return RoutedRetrievalConfig(
        parent_window_pages=args.parent_window_pages,
        parent_max_chars=args.parent_max_chars,
        fact_top_k=args.fact_top_k,
        compare_candidate_top_k=args.compare_candidate_top_k,
        compare_entity_top_k=args.compare_entity_top_k,
        compare_top_k=args.compare_top_k,
        summary_candidate_top_k=args.summary_candidate_top_k,
        summary_top_k=args.summary_top_k,
        summary_per_source=args.summary_per_source,
    )


def max_candidate_top_k(config: RoutedRetrievalConfig) -> int:
    """计算第一阶段混合召回需要的最大候选数。"""
    return max(config.fact_top_k, config.compare_candidate_top_k, config.summary_candidate_top_k)


def load_vector_resources(args: argparse.Namespace, index_dir: Path):
    """加载 embedding、FAISS 和 chunk 元数据。"""
    manifest = eval_base.load_manifest(index_dir)
    metadata = load_chunk_metadata(index_dir / "chunks_meta.jsonl")
    config = EmbeddingConfig(
        model_name=manifest.get("model", args.embedding_model),
        backend=manifest.get("backend", args.embedding_backend),
        batch_size=args.embedding_batch_size,
        max_length=manifest.get("max_length", args.max_length),
        normalize=manifest.get("normalize", not args.no_normalize),
        use_fp16=manifest.get("use_fp16", args.use_fp16),
    )
    embedder = FlagEmbeddingModel(config)
    index = load_faiss_index(index_dir / f"faiss_{args.index_type}.index")
    return embedder, index, metadata, manifest


def run_vector_searches(
    samples: list[eval_base.EvalSample],
    embedder: FlagEmbeddingModel,
    index,
    metadata: list[dict],
    top_k: int,
) -> dict[str, list[SearchResult]]:
    """批量执行向量检索。"""
    vectors = embedder.encode_queries([sample.query for sample in samples])
    return {
        sample.question_id: search_index(index, metadata, vector, top_k=top_k)
        for sample, vector in zip(samples, vectors)
    }


def run_bm25_searches(samples: list[eval_base.EvalSample], bm25_path: Path, top_k: int) -> dict[str, list[SearchResult]]:
    """批量执行 BM25 检索。"""
    if not bm25_path.exists():
        raise SystemExit(f"BM25 index not found: {bm25_path}")
    bm25_store = BM25Store.load(bm25_path)
    return {sample.question_id: bm25_store.search(sample.query, top_k=top_k) for sample in samples}


def run_hybrid_searches(
    args: argparse.Namespace,
    samples: list[eval_base.EvalSample],
    vector_results: dict[str, list[SearchResult]],
    bm25_results: dict[str, list[SearchResult]],
    top_k: int,
) -> dict[str, list[HybridSearchResult]]:
    """融合向量和 BM25 候选。"""
    return {
        sample.question_id: fuse_results(
            vector_results.get(sample.question_id, []),
            bm25_results.get(sample.question_id, []),
            top_k=top_k,
            vector_weight=args.vector_weight,
            bm25_weight=args.bm25_weight,
            method=args.fusion,
            rrf_k=args.rrf_k,
        )
        for sample in samples
    }


def run_compare_rerank(
    args: argparse.Namespace,
    samples: list[eval_base.EvalSample],
    hybrid_results: dict[str, list[HybridSearchResult]],
    config: RoutedRetrievalConfig,
) -> dict[str, list[RerankResult]]:
    """只对 compare 样本执行 rerank。"""
    compare_samples = [sample for sample in samples if sample.question_type == "compare"]
    if not compare_samples:
        return {}
    reranker = build_reranker(args)
    return {
        sample.question_id: reranker.rerank(
            sample.query,
            hybrid_results.get(sample.question_id, []),
            top_k=config.compare_top_k,
        )
        for sample in compare_samples
    }


def build_reranker(args: argparse.Namespace) -> CrossEncoderReranker:
    """按命令行配置加载 reranker。"""
    return CrossEncoderReranker(
        RerankConfig(
            model_name=args.reranker_model,
            backend=args.reranker_backend,
            batch_size=args.reranker_batch_size,
            max_length=args.reranker_max_length,
            use_fp16=args.use_fp16,
            score_activation=args.score_activation,
            score_threshold=args.score_threshold,
            relative_drop_threshold=args.relative_drop_threshold,
        )
    )


def recall_hybrid_for_query(
    args: argparse.Namespace,
    query: str,
    embedder: FlagEmbeddingModel,
    index,
    metadata: list[dict],
    bm25_store: BM25Store,
    top_k: int,
) -> list[HybridSearchResult]:
    """对单个改写 query 独立执行向量、BM25 和融合召回。"""
    query_vector = embedder.encode_queries([query])
    vector_results = search_index(index, metadata, query_vector, top_k=top_k)
    bm25_results = bm25_store.search(query, top_k=top_k)
    return fuse_results(
        vector_results,
        bm25_results,
        top_k=top_k,
        vector_weight=args.vector_weight,
        bm25_weight=args.bm25_weight,
        method=args.fusion,
        rrf_k=args.rrf_k,
    )


def run_compare_rewrite_rerank(
    args: argparse.Namespace,
    samples: list[eval_base.EvalSample],
    embedder: FlagEmbeddingModel,
    index,
    metadata: list[dict],
    bm25_store: BM25Store,
    base_hybrid_results: dict[str, list[HybridSearchResult]],
    config: RoutedRetrievalConfig,
    rewrite_by_id: dict[str, CompareQueryRewrite],
) -> dict[str, list[RerankResult]]:
    """用 LLM 改写后的子查询分别召回和 rerank，再按子查询配额合并。"""
    compare_samples = [sample for sample in samples if sample.question_type == "compare"]
    if not compare_samples:
        return {}

    reranker = build_reranker(args)
    results: dict[str, list[RerankResult]] = {}
    for sample in compare_samples:
        rewrite = rewrite_by_id.get(sample.question_id)
        base_results = base_hybrid_results.get(sample.question_id, [])[: config.compare_candidate_top_k]
        merge_top_k = compare_merge_top_k(args, config)
        original_reranked = reranker.rerank(sample.query, base_results, top_k=merge_top_k)
        if rewrite is None:
            results[sample.question_id] = original_reranked
            continue

        per_query_results: list[list[RerankResult]] = []
        for subquery, entity in compare_rewrite_subqueries_with_entities(
            rewrite,
            include_merged=args.compare_rewrite_include_merged,
        ):
            subquery_hybrid = recall_hybrid_for_query(
                args,
                subquery,
                embedder,
                index,
                metadata,
                bm25_store,
                top_k=args.compare_rewrite_top_k,
            )
            reranked = reranker.rerank(
                subquery,
                subquery_hybrid,
                top_k=max(args.compare_rewrite_per_query_keep, config.compare_top_k),
            )
            per_query_results.append(prefer_entity_results(reranked, entity))

        quota_selected = interleave_rewrite_results(
            per_query_results,
            per_query_keep=args.compare_rewrite_per_query_keep,
        )
        results[sample.question_id] = merge_rerank_results(
            quota_selected,
            original_reranked,
            top_k=merge_top_k,
        )
    return results


def compare_merge_top_k(args: argparse.Namespace, config: RoutedRetrievalConfig) -> int:
    """开启 parent 补齐时，保留更多 child 候选供后续去重补位。"""
    if not args.compare_parent_fill:
        return config.compare_top_k
    return max(config.compare_top_k, args.compare_parent_fill_pool)


def compare_rewrite_subqueries_with_entities(
    rewrite: CompareQueryRewrite,
    include_merged: bool = False,
) -> list[tuple[str, str]]:
    """把 compare rewrite 转成带实体归属的子查询列表。"""
    pairs: list[tuple[str, str]] = []
    for index, subquery in enumerate(rewrite.sub_queries):
        entity = rewrite.entities[index] if index < len(rewrite.entities) else ""
        pairs.append((subquery, entity))
    if include_merged and rewrite.merged_query:
        pairs.append((rewrite.merged_query, ""))
    return pairs


def prefer_entity_results(results: list[RerankResult], entity: str) -> list[RerankResult]:
    """子查询精排后，优先保留文本中明确出现该实体的结果。"""
    if not entity:
        return results
    matched = [result for result in results if result_mentions_entity(result, entity)]
    if not matched:
        return results
    unmatched = [result for result in results if not result_mentions_entity(result, entity)]
    reordered = [*matched, *unmatched]
    for rank, result in enumerate(reordered, start=1):
        result.rank = rank
    return reordered


def result_mentions_entity(result: RerankResult, entity: str) -> bool:
    """判断候选文本或元数据里是否包含当前子查询实体。"""
    entity_norm = normalize_entity_text(entity)
    if not entity_norm:
        return False
    chunk = result.chunk
    metadata = chunk.get("metadata") or {}
    fields = [
        chunk.get("text"),
        chunk.get("source"),
        chunk.get("doc_id"),
        metadata.get("title"),
        metadata.get("notes"),
    ]
    return any(entity_norm in normalize_entity_text(str(field or "")) for field in fields)


def normalize_entity_text(text: str) -> str:
    """去掉空白和常见分隔符，用于实体精确包含判断。"""
    return re.sub(r"[\s·・（）()_\-—|/\\]+", "", text).lower()


def interleave_rewrite_results(
    per_query_results: list[list[RerankResult]],
    per_query_keep: int,
) -> list[RerankResult]:
    """按子查询交错选结果，避免某个对比对象被挤掉。"""
    selected: list[RerankResult] = []
    seen: set[str] = set()
    keep = max(1, per_query_keep)
    for offset in range(keep):
        for results in per_query_results:
            if offset >= len(results):
                continue
            result = results[offset]
            key = result_key(result.chunk)
            if key in seen:
                continue
            seen.add(key)
            selected.append(result)
    return selected


def merge_rerank_results(
    primary: list[RerankResult],
    filler: list[RerankResult],
    top_k: int,
) -> list[RerankResult]:
    """先保留子查询配额结果，再用原问题 rerank 结果补齐 TopK。"""
    merged: list[RerankResult] = []
    seen: set[str] = set()
    for result in [*primary, *filler]:
        key = result_key(result.chunk)
        if key in seen:
            continue
        seen.add(key)
        merged.append(result)
        if len(merged) >= top_k:
            break
    for rank, result in enumerate(merged, start=1):
        result.rank = rank
    return merged


def expand_compare_hybrid_results(
    args: argparse.Namespace,
    samples: list[eval_base.EvalSample],
    embedder: FlagEmbeddingModel,
    index,
    metadata: list[dict],
    bm25_store: BM25Store,
    hybrid_results: dict[str, list[HybridSearchResult]],
    config: RoutedRetrievalConfig,
    rewrite_by_id: dict[str, CompareQueryRewrite] | None = None,
) -> dict[str, list[HybridSearchResult]]:
    """只为 compare 样本追加补召回候选；优先使用 LLM rewrite 缓存。"""
    expanded = dict(hybrid_results)
    rewrite_by_id = rewrite_by_id or {}
    for sample in samples:
        if sample.question_type != "compare":
            continue
        base_results = hybrid_results.get(sample.question_id, [])[: config.compare_candidate_top_k]
        supplemental: list[HybridSearchResult] = []

        rewrite = rewrite_by_id.get(sample.question_id)
        if rewrite is not None:
            subqueries = compare_rewrite_queries(rewrite, include_merged=args.compare_rewrite_include_merged)
            subquery_top_k = args.compare_rewrite_top_k
        else:
            entities = extract_compare_entities(sample.query)
            subqueries = [build_compare_entity_query(sample.query, entity, entities) for entity in entities[:2]]
            subquery_top_k = config.compare_entity_top_k

        for subquery in subqueries:
            query_vector = embedder.encode_queries([subquery])
            vector_results = search_index(index, metadata, query_vector, top_k=subquery_top_k)
            bm25_results = bm25_store.search(subquery, top_k=subquery_top_k)
            supplemental.extend(
                fuse_results(
                    vector_results,
                    bm25_results,
                    top_k=subquery_top_k,
                    vector_weight=args.vector_weight,
                    bm25_weight=args.bm25_weight,
                    method=args.fusion,
                    rrf_k=args.rrf_k,
                )
            )
        expanded[sample.question_id] = merge_compare_candidates(base_results, supplemental)
    return expanded


def run_routed_searches(
    samples: list[eval_base.EvalSample],
    hybrid_results: dict[str, list[HybridSearchResult]],
    compare_rerank_results: dict[str, list[RerankResult]],
    parent_store: ParentDocumentStore,
    config: RoutedRetrievalConfig,
    args: argparse.Namespace | None = None,
) -> dict[str, list[SearchLikeResult]]:
    """按 question_type 路由到不同检索策略。"""
    return {
        sample.question_id: route_one_sample(
            sample,
            hybrid_results,
            compare_rerank_results,
            parent_store=parent_store,
            config=config,
            args=args,
        )
        for sample in samples
    }


def route_one_sample(
    sample: eval_base.EvalSample,
    hybrid_results: dict[str, list[HybridSearchResult]],
    compare_rerank_results: dict[str, list[RerankResult]],
    parent_store: ParentDocumentStore,
    config: RoutedRetrievalConfig,
    args: argparse.Namespace | None = None,
) -> list[SearchLikeResult]:
    """路由单条样本；compare 可选 parent 去重补齐。"""
    if (
        args is not None
        and args.compare_parent_fill
        and sample.question_type == "compare"
        and compare_rerank_results.get(sample.question_id)
    ):
        return expand_results_to_parents(
            compare_rerank_results.get(sample.question_id, []),
            parent_store=parent_store,
            mode="window",
            window_pages=config.parent_window_pages,
            max_chars=config.parent_max_chars,
            top_k=config.compare_top_k,
        )

    return route_results(
        sample.question_type,
        hybrid_results.get(sample.question_id, []),
        compare_rerank_results.get(sample.question_id, []),
        parent_store=parent_store,
        config=config,
    )


def render_report(
    args: argparse.Namespace,
    config: RoutedRetrievalConfig,
    eval_path: Path,
    index_dir: Path,
    samples: list[eval_base.EvalSample],
    total_rows: int,
    skipped: int,
    elapsed_seconds: float,
    all_scores: dict[str, dict[int, list[eval_base.SampleScore]]],
) -> str:
    """把路由评测结果渲染成 Markdown。"""
    ks = sorted(args.ks)
    lines = [
        "# 按问题类型路由检索实验",
        "",
        f"- 评测时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 评测集：`{display_path(eval_path)}`",
        f"- 索引目录：`{display_path(index_dir)}`",
        f"- 索引类型：`{args.index_type}`",
        f"- 匹配粒度：`{args.match_level}`",
        f"- 完成样本：{len(samples)} / {total_rows}",
        f"- 跳过样本：{skipped}",
        f"- 总耗时（秒）：{elapsed_seconds:.2f}",
        f"- 融合方式：`{args.fusion}`，vector={args.vector_weight}, bm25={args.bm25_weight}",
        f"- compare rewrite：`{args.compare_rewrite_file or 'disabled'}`",
        f"- 父文档窗口：前后各 {config.parent_window_pages} 页",
        f"- fact 策略：hybrid_top{config.fact_top_k} + parent_window",
        f"- compare 策略：{compare_strategy_text(args, config)}",
        f"- summary 策略：hybrid_top{config.summary_candidate_top_k} + source_diverse_top{config.summary_top_k} + parent_window",
        "",
        "## Overall",
        "",
        "| scheme | " + " | ".join(f"Recall@{k}" for k in ks) + " | " + " | ".join(f"HitAny@{k}" for k in ks) + " | " + " | ".join(f"HitAll@{k}" for k in ks) + " |",
        "|---|" + "|".join("---:" for _ in range(len(ks) * 3)) + "|",
    ]
    for scheme, scores_by_k in all_scores.items():
        recall_cells = [eval_base.format_rate(eval_base.summarize_scores(scores_by_k[k])["recall"]) for k in ks]
        hit_any_cells = [eval_base.format_rate(eval_base.summarize_scores(scores_by_k[k])["hit_any"]) for k in ks]
        hit_all_cells = [eval_base.format_rate(eval_base.summarize_scores(scores_by_k[k])["hit_all"]) for k in ks]
        lines.append(f"| {scheme} | " + " | ".join(recall_cells + hit_any_cells + hit_all_cells) + " |")

    lines.extend(["", "## By Question Type", ""])
    largest_k = max(ks)
    for scheme, scores_by_k in all_scores.items():
        grouped: dict[str, list[eval_base.SampleScore]] = {}
        for score in scores_by_k[largest_k]:
            grouped.setdefault(score.question_type, []).append(score)
        lines.extend(
            [
                f"### {scheme} @ {largest_k}",
                "",
                "| question_type | count | Recall | HitAny | HitAll |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for question_type, items in sorted(grouped.items()):
            summary = eval_base.summarize_scores(items)
            lines.append(
                f"| {question_type} | {len(items)} | {eval_base.format_rate(summary['recall'])} | "
                f"{eval_base.format_rate(summary['hit_any'])} | {eval_base.format_rate(summary['hit_all'])} |"
            )
        lines.append("")

    lines.extend(render_result_lengths(args, all_scores, all_scores.keys()))
    lines.extend(eval_base.render_badcases(args, all_scores, largest_k))
    return "\n".join(lines).rstrip() + "\n"


def render_result_lengths(args: argparse.Namespace, all_scores, schemes) -> list[str]:
    """预留结果长度区块，保持报告结构稳定。"""
    return [
        "## Notes",
        "",
        "- 本实验的 `routed` 结果会按问题类型使用不同策略，因此 summary 的候选数量可能大于 5。",
        "- `Recall@5` 便于和前序实验横向对比，`Recall@8` 用于观察 summary 多文档聚合是否带来额外覆盖。",
        "",
    ]


def write_details(
    path: Path,
    all_scores: dict[str, dict[int, list[eval_base.SampleScore]]],
    routed_results: dict[str, list[SearchLikeResult]],
    strategy_by_id: dict[str, str],
    rewrite_by_id: dict[str, CompareQueryRewrite] | None = None,
) -> None:
    """保存逐样本指标、检索结果和路由策略。"""
    payload = {
        "scores": {
            scheme: {str(k): [asdict(score) for score in scores] for k, scores in scores_by_k.items()}
            for scheme, scores_by_k in all_scores.items()
        },
        "strategy_by_id": strategy_by_id,
        "compare_rewrites": {
            question_id: {
                "entities": rewrite.entities,
                "aspect": rewrite.aspect,
                "sub_queries": rewrite.sub_queries,
                "merged_query": rewrite.merged_query,
                "model": rewrite.model,
            }
            for question_id, rewrite in (rewrite_by_id or {}).items()
        },
        "results": {
            "routed": {
                question_id: [result_to_dict(result) for result in results]
                for question_id, results in routed_results.items()
            }
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def result_to_dict(result: SearchLikeResult) -> dict:
    """把检索结果转成 JSON。"""
    payload = {
        "rank": result.rank,
        "score": result.score,
        "chunk_id": result.chunk.get("chunk_id"),
        "parent_id": result.chunk.get("parent_id"),
        "child_chunk_id": result.chunk.get("child_chunk_id"),
        "source": result.chunk.get("source"),
        "pages": result.chunk.get("pages"),
        "child_hits": result.chunk.get("child_hits", []),
        "text": str(result.chunk.get("text") or "")[:300],
    }
    if isinstance(result, RerankResult):
        payload["rerank_score"] = result.rerank_score
        payload["retrieval_score"] = result.retrieval_score
        payload["retrieval_rank"] = result.retrieval_rank
    return payload


def strategy_name(question_type: str, config: RoutedRetrievalConfig) -> str:
    """给每条样本记录实际采用的策略。"""
    question_type = (question_type or "").strip().lower()
    if question_type == "compare":
        return (
            f"hybrid_top{config.compare_candidate_top_k}"
            f"_entity_top{config.compare_entity_top_k}"
            f"_rerank_top{config.compare_top_k}_parent_window{config.parent_window_pages}"
        )
    if question_type == "summary":
        return f"hybrid_top{config.summary_candidate_top_k}_source_diverse_top{config.summary_top_k}_parent_window{config.parent_window_pages}"
    return f"hybrid_top{config.fact_top_k}_parent_window{config.parent_window_pages}"


def compare_strategy_text(args: argparse.Namespace, config: RoutedRetrievalConfig) -> str:
    """生成 compare 策略的报告文本。"""
    parent_fill = f" + parent_fill_pool{args.compare_parent_fill_pool}" if args.compare_parent_fill else ""
    if args.compare_rewrite_file:
        merged = "+merged_query" if args.compare_rewrite_include_merged else ""
        if args.compare_rewrite_mode == "separate":
            return (
                f"hybrid_top{config.compare_candidate_top_k} + "
                f"llm_rewrite_separate_subquery_top{args.compare_rewrite_top_k}{merged} + "
                f"per_query_keep{args.compare_rewrite_per_query_keep} + "
                "entity_prefer + "
                f"rerank_top{config.compare_top_k}{parent_fill} + parent_window"
            )
        return (
            f"hybrid_top{config.compare_candidate_top_k} + "
            f"llm_rewrite_subquery_top{args.compare_rewrite_top_k}{merged} + "
            f"rerank_top{config.compare_top_k}{parent_fill} + parent_window"
        )
    return (
        f"hybrid_top{config.compare_candidate_top_k} + "
        f"entity_top{config.compare_entity_top_k} + "
        f"rerank_top{config.compare_top_k}{parent_fill} + parent_window"
    )


def routed_strategy_name(question_type: str, args: argparse.Namespace, config: RoutedRetrievalConfig) -> str:
    """给每条样本记录实际采用的策略。"""
    question_type = (question_type or "").strip().lower()
    parent_fill = f"_parent_fill_pool{args.compare_parent_fill_pool}" if args.compare_parent_fill else ""
    if question_type == "compare" and args.compare_rewrite_file:
        merged = "_merged" if args.compare_rewrite_include_merged else ""
        if args.compare_rewrite_mode == "separate":
            return (
                f"hybrid_top{config.compare_candidate_top_k}"
                f"_llm_rewrite_separate_top{args.compare_rewrite_top_k}{merged}"
                f"_keep{args.compare_rewrite_per_query_keep}"
                "_entity_prefer"
                f"_rerank_top{config.compare_top_k}{parent_fill}_parent_window{config.parent_window_pages}"
            )
        return (
            f"hybrid_top{config.compare_candidate_top_k}"
            f"_llm_rewrite_top{args.compare_rewrite_top_k}{merged}"
            f"_rerank_top{config.compare_top_k}{parent_fill}_parent_window{config.parent_window_pages}"
        )
    if question_type == "compare" and args.compare_parent_fill:
        return (
            f"hybrid_top{config.compare_candidate_top_k}"
            f"_entity_top{config.compare_entity_top_k}"
            f"_rerank_top{config.compare_top_k}{parent_fill}_parent_window{config.parent_window_pages}"
        )
    return strategy_name(question_type, config)


def main() -> None:
    """执行路由检索评测。"""
    args = parse_args()
    args.ks = sorted(set(args.ks))
    eval_path = resolve_path(args.eval)
    index_dir = resolve_path(args.index_dir)
    output_path = resolve_path(args.output)
    details_path = resolve_path(args.details_output)
    bm25_path = resolve_path(args.bm25_path) if args.bm25_path else index_dir / "bm25.pkl"
    compare_rewrite_path = resolve_path(args.compare_rewrite_file) if args.compare_rewrite_file else None
    config = routed_config_from_args(args)
    candidate_top_k = max_candidate_top_k(config)

    samples, total_rows, skipped = eval_base.load_eval_samples(eval_path)
    if not samples:
        raise SystemExit("No completed eval samples found.")
    if compare_rewrite_path and not compare_rewrite_path.exists():
        raise SystemExit(f"Compare rewrite file not found: {compare_rewrite_path}")
    rewrite_by_id = load_compare_rewrites(compare_rewrite_path) if compare_rewrite_path else {}

    start = time.perf_counter()
    embedder, index, metadata, _manifest = load_vector_resources(args, index_dir)
    parent_store = ParentDocumentStore(metadata)
    vector_results = run_vector_searches(samples, embedder, index, metadata, top_k=candidate_top_k)
    if not bm25_path.exists():
        raise SystemExit(f"BM25 index not found: {bm25_path}")
    bm25_store = BM25Store.load(bm25_path)
    bm25_results = {sample.question_id: bm25_store.search(sample.query, top_k=candidate_top_k) for sample in samples}
    hybrid_results = run_hybrid_searches(args, samples, vector_results, bm25_results, top_k=candidate_top_k)
    if rewrite_by_id and args.compare_rewrite_mode == "separate":
        compare_rerank_results = run_compare_rewrite_rerank(
            args,
            samples,
            embedder,
            index,
            metadata,
            bm25_store,
            hybrid_results,
            config,
            rewrite_by_id,
        )
    else:
        hybrid_results = expand_compare_hybrid_results(
            args,
            samples,
            embedder,
            index,
            metadata,
            bm25_store,
            hybrid_results,
            config,
            rewrite_by_id,
        )
        compare_rerank_results = run_compare_rerank(args, samples, hybrid_results, config)
    routed_results = run_routed_searches(samples, hybrid_results, compare_rerank_results, parent_store, config, args=args)

    all_scores = {
        "routed": eval_base.score_scheme(samples, routed_results, args.ks, match_level=args.match_level)
    }
    strategy_by_id = {
        sample.question_id: routed_strategy_name(sample.question_type, args, config)
        for sample in samples
    }
    elapsed_seconds = time.perf_counter() - start
    report = render_report(args, config, eval_path, index_dir, samples, total_rows, skipped, elapsed_seconds, all_scores)

    print(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    write_details(details_path, all_scores, routed_results, strategy_by_id, rewrite_by_id)
    print(f"wrote: {display_path(output_path)}")
    print(f"wrote: {display_path(details_path)}")


if __name__ == "__main__":
    main()
