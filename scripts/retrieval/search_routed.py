#!/usr/bin/env python
"""使用项目默认 routed 检索入口查询单个问题。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


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

from financial_report_rag.retrieval.routed_retriever import (  # noqa: E402
    RoutedRetrievalConfig,
    RoutedRetrievalOutput,
    RoutedRetriever,
    RoutedRetrieverConfig,
)
from financial_report_rag.utils import preview  # noqa: E402


def parse_args() -> argparse.Namespace:
    """读取 routed 检索命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--question-type", choices=["fact", "compare", "summary"], default="fact")
    parser.add_argument("--index-dir", default="data/processed/indexes/bge_large_zh_v15")
    parser.add_argument("--index-type", choices=["flat", "ivf", "hnsw"], default="flat")
    parser.add_argument("--bm25-path", default="")
    parser.add_argument("--embedding-model", default="models/bge-large-zh-v1.5")
    parser.add_argument("--embedding-backend", choices=["sentence-transformers", "flagembedding"], default="sentence-transformers")
    parser.add_argument("--embedding-batch-size", type=int, default=16)
    parser.add_argument("--embedding-max-length", type=int, default=512)
    parser.add_argument("--reranker-model", default="models/bge-reranker-v2-m3")
    parser.add_argument("--reranker-backend", choices=["flagembedding", "transformers"], default="transformers")
    parser.add_argument("--reranker-batch-size", type=int, default=2)
    parser.add_argument("--reranker-max-length", type=int, default=512)
    parser.add_argument("--use-fp16", action="store_true")
    parser.add_argument("--vector-weight", type=float, default=0.6)
    parser.add_argument("--bm25-weight", type=float, default=0.4)
    parser.add_argument("--fusion", choices=["weighted", "rrf"], default="weighted")
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--parent-window-pages", type=int, default=1)
    parser.add_argument("--parent-max-chars", type=int, default=0)
    parser.add_argument("--fact-top-k", type=int, default=5)
    parser.add_argument("--compare-candidate-top-k", type=int, default=20)
    parser.add_argument("--compare-top-k", type=int, default=5)
    parser.add_argument("--summary-candidate-top-k", type=int, default=50)
    parser.add_argument("--summary-top-k", type=int, default=8)
    parser.add_argument("--summary-per-source", type=int, default=2)
    parser.add_argument("--top-chars", type=int, default=500)
    parser.add_argument("--json", action="store_true", help="输出 JSON，方便后续生成阶段调用。")
    return parser.parse_args()


def build_retriever(args: argparse.Namespace) -> RoutedRetriever:
    """根据命令行参数构建 routed 检索器。"""
    runtime_config = RoutedRetrieverConfig(
        index_dir=args.index_dir,
        index_type=args.index_type,
        bm25_path=args.bm25_path,
        embedding_model=args.embedding_model,
        embedding_backend=args.embedding_backend,
        embedding_batch_size=args.embedding_batch_size,
        embedding_max_length=args.embedding_max_length,
        use_fp16=args.use_fp16,
        reranker_model=args.reranker_model,
        reranker_backend=args.reranker_backend,
        reranker_batch_size=args.reranker_batch_size,
        reranker_max_length=args.reranker_max_length,
        vector_weight=args.vector_weight,
        bm25_weight=args.bm25_weight,
        fusion=args.fusion,
        rrf_k=args.rrf_k,
    )
    route_config = RoutedRetrievalConfig(
        parent_window_pages=args.parent_window_pages,
        parent_max_chars=args.parent_max_chars,
        fact_top_k=args.fact_top_k,
        compare_candidate_top_k=args.compare_candidate_top_k,
        compare_top_k=args.compare_top_k,
        summary_candidate_top_k=args.summary_candidate_top_k,
        summary_top_k=args.summary_top_k,
        summary_per_source=args.summary_per_source,
    )
    return RoutedRetriever(runtime_config, route_config, base_dir=ROOT)


def output_to_dict(output: RoutedRetrievalOutput, top_chars: int) -> dict:
    """把检索输出转成可序列化字典。"""
    return {
        "query": output.query,
        "question_type": output.question_type,
        "strategy": output.strategy,
        "results": [result_to_dict(result, top_chars) for result in output.results],
        "rerank_results": [result_to_dict(result, top_chars) for result in output.rerank_results],
    }


def result_to_dict(result, top_chars: int) -> dict:
    """把单条检索结果转成字典。"""
    chunk = result.chunk
    payload = {
        "rank": result.rank,
        "score": result.score,
        "chunk_id": chunk.get("chunk_id"),
        "parent_id": chunk.get("parent_id"),
        "child_chunk_id": chunk.get("child_chunk_id"),
        "doc_id": chunk.get("doc_id"),
        "source": chunk.get("source"),
        "pages": chunk.get("pages"),
        "chunk_type": chunk.get("chunk_type"),
        "has_table": chunk.get("has_table"),
        "text": str(chunk.get("text") or "")[:top_chars],
    }
    for field in ["vector_score", "bm25_score", "vector_rank", "bm25_rank", "rerank_score", "retrieval_score", "retrieval_rank"]:
        if hasattr(result, field):
            payload[field] = getattr(result, field)
    return payload


def print_text(output: RoutedRetrievalOutput, top_chars: int) -> None:
    """以便于人工查看的格式打印 routed 检索结果。"""
    print(f"query: {output.query}")
    print(f"question_type: {output.question_type}")
    print(f"strategy: {output.strategy}")
    print(f"matched: {len(output.results)}")
    for result in output.results:
        item = result_to_dict(result, top_chars)
        print("=" * 80)
        print(f"rank: {item['rank']}  score: {item['score']:.4f}")
        print(f"source: {item['source']}")
        print(f"pages: {item['pages']}")
        print(f"chunk_id: {item['chunk_id']}")
        print(f"child_chunk_id: {item['child_chunk_id']}")
        print(f"type: {item['chunk_type']}  has_table: {item['has_table']}")
        print(preview(item["text"], top_chars))


def main() -> None:
    """执行一次 routed 检索。"""
    args = parse_args()
    retriever = build_retriever(args)
    output = retriever.retrieve(args.query, question_type=args.question_type)
    if args.json:
        print(json.dumps(output_to_dict(output, args.top_chars), ensure_ascii=False, indent=2))
    else:
        print_text(output, args.top_chars)


if __name__ == "__main__":
    main()
