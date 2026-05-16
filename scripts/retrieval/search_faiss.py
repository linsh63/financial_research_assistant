#!/usr/bin/env python
"""检索已经构建好的 FAISS 索引。"""

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

from financial_report_rag.retrieval.embeddings import EmbeddingConfig, FlagEmbeddingModel  # noqa: E402
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
    parser.add_argument(
        "--index-dir",
        default="data/processed/indexes/bge_large_zh_v15_sample",
        help="索引目录，例如 data/processed/indexes/bge_large_zh_v15_sample。",
    )
    parser.add_argument("--index-type", choices=["flat", "ivf", "hnsw"], default="flat")
    parser.add_argument("--index-path", default="data/processed/indexes/faiss_flat.index")
    parser.add_argument("--meta-path", default="data/processed/indexes/faiss_meta.jsonl")
    parser.add_argument("--model", default="BAAI/bge-large-zh-v1.5")
    parser.add_argument(
        "--backend",
        choices=["sentence-transformers", "flagembedding"],
        default="sentence-transformers",
        help="embedding 编码后端；默认与本地 Mac 环境兼容。",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--no-normalize", action="store_true")
    parser.add_argument("--use-fp16", action="store_true")
    return parser.parse_args()


def load_manifest(index_dir: Path) -> dict:
    """如果索引目录中有 manifest，就读取其中的模型配置。"""
    manifest_path = index_dir / "index_manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def resolve_index_paths(args: argparse.Namespace) -> tuple[Path, Path, dict]:
    """根据 index-dir 或显式路径确定索引和元数据文件。"""
    if args.index_dir:
        index_dir = ROOT / args.index_dir
        return (
            index_dir / f"faiss_{args.index_type}.index",
            index_dir / "chunks_meta.jsonl",
            load_manifest(index_dir),
        )
    return ROOT / args.index_path, ROOT / args.meta_path, {}


def main() -> None:
    """执行一次向量检索并打印结果。"""
    args = parse_args()
    index_path, meta_path, manifest = resolve_index_paths(args)
    metadata = load_chunk_metadata(meta_path)

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
    results = search_index(index, metadata, query_vector, args.top_k)

    for result in results:
        chunk = result.chunk
        print("=" * 80)
        print(f"rank: {result.rank}  score: {result.score:.4f}")
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


if __name__ == "__main__":
    main()
