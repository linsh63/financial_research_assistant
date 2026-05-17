#!/usr/bin/env python
"""执行 FAISS 向量 + BM25 的混合召回。"""

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

from financial_report_rag.retrieval.bm25_store import BM25Store  # noqa: E402
from financial_report_rag.retrieval.embeddings import EmbeddingConfig, FlagEmbeddingModel  # noqa: E402
from financial_report_rag.retrieval.hybrid_retriever import fuse_results  # noqa: E402
from financial_report_rag.retrieval.vector_store import (  # noqa: E402
    load_chunk_metadata,
    load_faiss_index,
    search_index,
)
from financial_report_rag.utils import preview  # noqa: E402


def parse_args() -> argparse.Namespace:
    """读取命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--index-dir", default="data/processed/indexes/bge_large_zh_v15")
    parser.add_argument("--index-type", choices=["flat", "ivf", "hnsw"], default="flat")
    parser.add_argument("--bm25-path", default="")
    parser.add_argument("--model", default="BAAI/bge-large-zh-v1.5")
    parser.add_argument("--backend", choices=["sentence-transformers", "flagembedding"], default="sentence-transformers")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--vector-top-k", type=int, default=20)
    parser.add_argument("--bm25-top-k", type=int, default=20)
    parser.add_argument("--vector-weight", type=float, default=0.5)
    parser.add_argument("--bm25-weight", type=float, default=0.5)
    parser.add_argument("--fusion", choices=["weighted", "rrf"], default="weighted")
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--no-normalize", action="store_true")
    parser.add_argument("--use-fp16", action="store_true")
    parser.add_argument("--vector-lower-is-better", action="store_true", help="当 FAISS 使用 L2 分数时启用。")
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析成绝对路径。"""
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def load_manifest(index_dir: Path) -> dict:
    """读取索引目录中的构建登记信息。"""
    manifest_path = index_dir / "index_manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path, dict]:
    """确定 FAISS、BM25、元数据文件路径。"""
    index_dir = resolve_path(args.index_dir)
    bm25_path = resolve_path(args.bm25_path) if args.bm25_path else index_dir / "bm25.pkl"
    return (
        index_dir / f"faiss_{args.index_type}.index",
        bm25_path,
        index_dir / "chunks_meta.jsonl",
        load_manifest(index_dir),
    )


def main() -> None:
    """执行一次混合召回并打印融合排序结果。"""
    args = parse_args()
    index_path, bm25_path, meta_path, manifest = resolve_paths(args)
    if not bm25_path.exists():
        raise SystemExit(f"BM25 index not found: {bm25_path}\n请先运行 scripts/build_bm25_index.py")

    metadata = load_chunk_metadata(meta_path)
    bm25_store = BM25Store.load(bm25_path)

    config = EmbeddingConfig(
        model_name=manifest.get("model", args.model),
        backend=manifest.get("backend", args.backend),
        batch_size=args.batch_size,
        max_length=manifest.get("max_length", args.max_length),
        normalize=manifest.get("normalize", not args.no_normalize),
        use_fp16=manifest.get("use_fp16", args.use_fp16),
    )
    embedder = FlagEmbeddingModel(config)
    query_vector = embedder.encode_queries([args.query])
    index = load_faiss_index(index_path)

    vector_results = search_index(index, metadata, query_vector, top_k=args.vector_top_k)
    bm25_results = bm25_store.search(args.query, top_k=args.bm25_top_k)
    results = fuse_results(
        vector_results,
        bm25_results,
        top_k=args.top_k,
        vector_weight=args.vector_weight,
        bm25_weight=args.bm25_weight,
        method=args.fusion,
        vector_higher_is_better=not args.vector_lower_is_better,
        rrf_k=args.rrf_k,
    )

    for result in results:
        chunk = result.chunk
        print("=" * 80)
        print(
            f"rank: {result.rank}  hybrid_score: {result.score:.4f}  "
            f"vector_score: {format_score(result.vector_score)}  bm25_score: {format_score(result.bm25_score)}"
        )
        print(f"vector_rank: {result.vector_rank}  bm25_rank: {result.bm25_rank}")
        print(f"vector_norm: {result.vector_norm:.4f}  bm25_norm: {result.bm25_norm:.4f}")
        print(f"chunk_id: {chunk.get('chunk_id')}")
        print(f"doc_id: {chunk.get('doc_id')}")
        print(f"source: {chunk.get('source')}")
        print(f"pages: {chunk.get('pages')}")
        print(f"type: {chunk.get('chunk_type')}  has_table: {chunk.get('has_table')}")
        metadata = chunk.get("metadata", {})
        print(f"title: {metadata.get('title', '')}")
        print(preview(chunk.get("text", ""), 700))
    print("=" * 80)
    print(f"matched: {len(results)}")
    print(f"fusion: {args.fusion}  vector_weight: {args.vector_weight}  bm25_weight: {args.bm25_weight}")


def format_score(score: float | None) -> str:
    """格式化可为空的检索分数。"""
    if score is None:
        return "-"
    return f"{score:.4f}"


if __name__ == "__main__":
    main()
