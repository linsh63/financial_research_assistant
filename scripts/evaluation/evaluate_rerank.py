#!/usr/bin/env python
"""评估向量 Top20 + rerank Top5 相比直接 Top5 的收益。"""

from __future__ import annotations

import argparse
import json
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
from financial_report_rag.retrieval.embeddings import EmbeddingConfig, FlagEmbeddingModel  # noqa: E402
from financial_report_rag.retrieval.hybrid_retriever import HybridSearchResult, fuse_results  # noqa: E402
from financial_report_rag.retrieval.parent_document import (  # noqa: E402
    ParentDocumentStore,
    expand_results_to_parents,
)
from financial_report_rag.retrieval.reranker import CrossEncoderReranker, RerankConfig, RerankResult  # noqa: E402
from financial_report_rag.retrieval.vector_store import (  # noqa: E402
    SearchResult,
    load_chunk_metadata,
    load_faiss_index,
    search_index,
)


def parse_args() -> argparse.Namespace:
    """读取 rerank 评测命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", default="data/eval/financial_qa_dev.jsonl")
    parser.add_argument("--index-dir", default="data/processed/indexes/bge_large_zh_v15")
    parser.add_argument("--index-type", choices=["flat", "ivf", "hnsw"], default="flat")
    parser.add_argument("--candidate-source", choices=["vector", "hybrid"], default="vector")
    parser.add_argument("--bm25-path", default="")
    parser.add_argument("--vector-weight", type=float, default=0.6)
    parser.add_argument("--bm25-weight", type=float, default=0.4)
    parser.add_argument("--fusion", choices=["weighted", "rrf"], default="weighted")
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--direct-top-k", type=int, default=5)
    parser.add_argument("--candidate-top-k", type=int, default=20)
    parser.add_argument("--rerank-top-k", type=int, default=5)
    parser.add_argument("--match-level", choices=["doc", "page"], default="page")
    parser.add_argument("--embedding-model", default="models/bge-large-zh-v1.5")
    parser.add_argument("--embedding-backend", choices=["sentence-transformers", "flagembedding"], default="sentence-transformers")
    parser.add_argument("--embedding-batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--no-normalize", action="store_true")
    parser.add_argument("--use-fp16", action="store_true")
    parser.add_argument("--reranker-model", default="BAAI/bge-reranker-v2-m3")
    parser.add_argument("--reranker-backend", choices=["flagembedding", "transformers"], default="flagembedding")
    parser.add_argument("--reranker-batch-size", type=int, default=8)
    parser.add_argument("--reranker-max-length", type=int, default=512)
    parser.add_argument("--score-activation", choices=["none", "sigmoid"], default="none")
    parser.add_argument("--score-threshold", type=float, default=None)
    parser.add_argument("--relative-drop-threshold", type=float, default=None)
    parser.add_argument("--use-qanything-thresholds", action="store_true", help="启用 QAnything 风格阈值预设：sigmoid + 0.28 + 0.5。")
    parser.add_argument("--parent-mode", choices=["none", "page", "window"], default="none")
    parser.add_argument("--parent-window-pages", type=int, default=0)
    parser.add_argument("--parent-stage", choices=["before-rerank", "after-rerank"], default="before-rerank")
    parser.add_argument("--parent-max-chars", type=int, default=0)
    parser.add_argument("--output", default="docs/experiments/rerank/vector_top20_rerank_top5.md")
    parser.add_argument("--details-output", default="docs/experiments/rerank/vector_top20_rerank_top5.details.json")
    parser.add_argument("--badcase-limit", type=int, default=20)
    return parser.parse_args()


def apply_qanything_preset(args: argparse.Namespace) -> None:
    """按需启用 QAnything 的 rerank 阈值经验值。"""
    if not args.use_qanything_thresholds:
        return
    if args.score_activation == "none":
        args.score_activation = "sigmoid"
    if args.score_threshold is None:
        args.score_threshold = 0.28
    if args.relative_drop_threshold is None:
        args.relative_drop_threshold = 0.5


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析成绝对路径。"""
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def display_path(path: Path) -> str:
    """优先用项目相对路径展示文件。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_vector_resources(args: argparse.Namespace, index_dir: Path):
    """加载 embedding 模型、FAISS 索引和 chunk 元数据。"""
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


def run_vector_searches(args: argparse.Namespace, samples, embedder, index, metadata) -> dict[str, list[SearchResult]]:
    """一次编码所有 query，并召回 TopN 候选。"""
    query_vectors = embedder.encode_queries([sample.query for sample in samples])
    return {
        sample.question_id: search_index(index, metadata, vector, top_k=args.candidate_top_k)
        for sample, vector in zip(samples, query_vectors)
    }


def run_bm25_searches(args: argparse.Namespace, samples, index_dir: Path) -> dict[str, list[SearchResult]]:
    """执行 BM25 检索，作为混合召回候选的一路。"""
    bm25_path = resolve_path(args.bm25_path) if args.bm25_path else index_dir / "bm25.pkl"
    if not bm25_path.exists():
        raise SystemExit(f"BM25 index not found: {bm25_path}")
    bm25_store = BM25Store.load(bm25_path)
    return {
        sample.question_id: bm25_store.search(sample.query, top_k=args.candidate_top_k)
        for sample in samples
    }


def run_hybrid_searches(
    args: argparse.Namespace,
    samples,
    vector_results: dict[str, list[SearchResult]],
    bm25_results: dict[str, list[SearchResult]],
) -> dict[str, list[HybridSearchResult]]:
    """融合向量和 BM25 候选，生成 rerank 前的混合候选。"""
    return {
        sample.question_id: fuse_results(
            vector_results.get(sample.question_id, []),
            bm25_results.get(sample.question_id, []),
            top_k=args.candidate_top_k,
            vector_weight=args.vector_weight,
            bm25_weight=args.bm25_weight,
            method=args.fusion,
            rrf_k=args.rrf_k,
        )
        for sample in samples
    }


def run_rerank_searches(
    args: argparse.Namespace,
    samples,
    candidate_results: dict[str, list[SearchResult | HybridSearchResult]],
) -> dict[str, list[RerankResult]]:
    """对每个问题的向量候选执行 rerank。"""
    reranker = CrossEncoderReranker(
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
    return {
        sample.question_id: reranker.rerank(
            sample.query,
            candidate_results.get(sample.question_id, [])[: args.candidate_top_k],
            top_k=args.rerank_top_k,
        )
        for sample in samples
    }


def expand_result_map_to_parents(
    args: argparse.Namespace,
    parent_store: ParentDocumentStore | None,
    results_by_id: dict[str, list[SearchResult | HybridSearchResult | RerankResult]],
    top_k: int | None = None,
) -> dict[str, list[SearchResult | HybridSearchResult | RerankResult]]:
    """把每个问题的 child 结果回填为 parent 结果。"""
    if parent_store is None or args.parent_mode == "none":
        return results_by_id
    return {
        question_id: expand_results_to_parents(
            results,
            parent_store=parent_store,
            mode=args.parent_mode,
            window_pages=args.parent_window_pages,
            max_chars=args.parent_max_chars,
            top_k=top_k,
        )
        for question_id, results in results_by_id.items()
    }


def render_report(
    args: argparse.Namespace,
    eval_path: Path,
    index_dir: Path,
    samples,
    total_rows: int,
    skipped: int,
    elapsed_seconds: float,
    all_scores,
) -> str:
    """把直接召回和 rerank 对比渲染成 Markdown。"""
    lines = [
        "# Rerank Evaluation",
        "",
        f"- evaluated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- eval_file: `{display_path(eval_path)}`",
        f"- index_dir: `{display_path(index_dir)}`",
        f"- index_type: `{args.index_type}`",
        f"- candidate_source: `{args.candidate_source}`",
        f"- match_level: `{args.match_level}`",
        f"- completed_samples: {len(samples)} / {total_rows}",
        f"- skipped_samples: {skipped}",
        f"- elapsed_seconds: {elapsed_seconds:.2f}",
        f"- reranker_model: `{args.reranker_model}`",
        f"- reranker_backend: `{args.reranker_backend}`",
        f"- candidate_top_k: {args.candidate_top_k}",
        f"- direct_top_k: {args.direct_top_k}",
        f"- rerank_top_k: {args.rerank_top_k}",
        f"- score_threshold: {args.score_threshold}",
        f"- relative_drop_threshold: {args.relative_drop_threshold}",
        f"- use_qanything_thresholds: {args.use_qanything_thresholds}",
        f"- parent_mode: `{args.parent_mode}`",
        f"- parent_stage: `{args.parent_stage}`",
        f"- parent_window_pages: {args.parent_window_pages}",
        f"- parent_max_chars: {args.parent_max_chars}",
    ]
    if args.candidate_source == "hybrid":
        lines.extend(
            [
                f"- fusion: `{args.fusion}`",
                f"- weights: vector={args.vector_weight}, bm25={args.bm25_weight}",
            ]
        )
    lines.extend(
        [
            "",
            "## Overall",
            "",
            "| scheme | Recall@5 | HitAny@5 | HitAll@5 |",
            "|---|---:|---:|---:|",
        ]
    )
    for scheme, scores_by_k in all_scores.items():
        summary = eval_base.summarize_scores(scores_by_k[args.rerank_top_k])
        lines.append(
            f"| {scheme} | {eval_base.format_rate(summary['recall'])} | "
            f"{eval_base.format_rate(summary['hit_any'])} | {eval_base.format_rate(summary['hit_all'])} |"
        )

    lines.extend(["", "## By Question Type", ""])
    for scheme, scores_by_k in all_scores.items():
        grouped: dict[str, list] = {}
        for score in scores_by_k[args.rerank_top_k]:
            grouped.setdefault(score.question_type, []).append(score)
        lines.extend([
            f"### {scheme}",
            "",
            "| question_type | count | Recall@5 | HitAny@5 | HitAll@5 |",
            "|---|---:|---:|---:|---:|",
        ])
        for question_type, items in sorted(grouped.items()):
            summary = eval_base.summarize_scores(items)
            lines.append(
                f"| {question_type} | {len(items)} | {eval_base.format_rate(summary['recall'])} | "
                f"{eval_base.format_rate(summary['hit_any'])} | {eval_base.format_rate(summary['hit_all'])} |"
            )
        lines.append("")

    lines.extend(render_changes(args, all_scores))
    lines.extend(eval_base.render_badcases(args, all_scores, args.rerank_top_k))
    return "\n".join(lines).rstrip() + "\n"


def render_changes(args: argparse.Namespace, all_scores) -> list[str]:
    """展示 rerank 相比直接 Top5 修复和退化的样本。"""
    direct_scheme = f"{args.candidate_source}_top{args.direct_top_k}"
    rerank_scheme = f"{args.candidate_source}_top{args.candidate_top_k}_rerank_top{args.rerank_top_k}"
    direct = {score.question_id: score for score in all_scores[direct_scheme][args.rerank_top_k]}
    reranked = {score.question_id: score for score in all_scores[rerank_scheme][args.rerank_top_k]}
    fixed = [qid for qid, score in reranked.items() if score.hit_all and not direct[qid].hit_all]
    regressed = [qid for qid, score in reranked.items() if not score.hit_all and direct[qid].hit_all]
    lines = [
        "## Changes",
        "",
        f"- fixed_hit_all: {len(fixed)}",
        f"- regressed_hit_all: {len(regressed)}",
        "",
        "### Fixed",
        "",
    ]
    lines.extend([f"- `{qid}`" for qid in fixed[: args.badcase_limit]] or ["None"])
    lines.extend(["", "### Regressed", ""])
    lines.extend([f"- `{qid}`" for qid in regressed[: args.badcase_limit]] or ["None"])
    lines.append("")
    return lines


def write_details(path: Path, all_scores, raw_results) -> None:
    """保存逐样本分数和 rerank 结果。"""
    payload = {"scores": {}, "results": {}}
    for scheme, scores_by_k in all_scores.items():
        payload["scores"][scheme] = {
            str(k): [asdict(score) for score in scores]
            for k, scores in scores_by_k.items()
        }
    for scheme, results_by_id in raw_results.items():
        payload["results"][scheme] = {}
        for question_id, results in results_by_id.items():
            payload["results"][scheme][question_id] = [
                result_to_dict(result)
                for result in results
            ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def result_to_dict(result) -> dict:
    """把 SearchResult/RerankResult 转为 JSON 友好的 dict。"""
    if isinstance(result, RerankResult):
        return {
            "rank": result.rank,
            "rerank_score": result.rerank_score,
            "retrieval_score": result.retrieval_score,
            "retrieval_rank": result.retrieval_rank,
            "chunk_id": result.chunk.get("chunk_id"),
            "parent_id": result.chunk.get("parent_id"),
            "child_chunk_id": result.chunk.get("child_chunk_id"),
            "source": result.chunk.get("source"),
            "pages": result.chunk.get("pages"),
            "child_hits": result.chunk.get("child_hits", []),
            "text": str(result.chunk.get("text") or "")[:300],
        }
    return {
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


def main() -> None:
    """执行向量 Top5 与 Top20+rerank Top5 对比。"""
    args = parse_args()
    apply_qanything_preset(args)
    eval_path = resolve_path(args.eval)
    index_dir = resolve_path(args.index_dir)
    output_path = resolve_path(args.output)
    details_path = resolve_path(args.details_output)

    samples, total_rows, skipped = eval_base.load_eval_samples(eval_path)
    if not samples:
        raise SystemExit("No completed eval samples found.")

    start = time.perf_counter()
    embedder, index, metadata, _manifest = load_vector_resources(args, index_dir)
    parent_store = ParentDocumentStore(metadata) if args.parent_mode != "none" else None
    vector_results = run_vector_searches(args, samples, embedder, index, metadata)
    if args.candidate_source == "hybrid":
        bm25_results = run_bm25_searches(args, samples, index_dir)
        candidate_results = run_hybrid_searches(args, samples, vector_results, bm25_results)
    else:
        candidate_results = vector_results
    if args.parent_stage == "before-rerank":
        candidate_results = expand_result_map_to_parents(args, parent_store, candidate_results, top_k=args.candidate_top_k)
    direct_results = {
        question_id: results[: args.direct_top_k]
        for question_id, results in candidate_results.items()
    }
    rerank_results = run_rerank_searches(args, samples, candidate_results)
    if args.parent_stage == "after-rerank":
        direct_results = expand_result_map_to_parents(args, parent_store, direct_results, top_k=args.direct_top_k)
        rerank_results = expand_result_map_to_parents(args, parent_store, rerank_results, top_k=args.rerank_top_k)

    direct_scheme = f"{args.candidate_source}_top{args.direct_top_k}"
    rerank_scheme = f"{args.candidate_source}_top{args.candidate_top_k}_rerank_top{args.rerank_top_k}"
    raw_results = {
        direct_scheme: direct_results,
        rerank_scheme: rerank_results,
    }
    all_scores = {
        scheme: eval_base.score_scheme(samples, results_by_id, [args.rerank_top_k], match_level=args.match_level)
        for scheme, results_by_id in raw_results.items()
    }
    elapsed_seconds = time.perf_counter() - start
    report = render_report(args, eval_path, index_dir, samples, total_rows, skipped, elapsed_seconds, all_scores)

    print(report)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    write_details(details_path, all_scores, raw_results)
    print(f"wrote: {display_path(output_path)}")
    print(f"wrote: {display_path(details_path)}")


if __name__ == "__main__":
    main()
