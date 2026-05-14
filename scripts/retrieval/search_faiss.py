#!/usr/bin/env python
"""Search a FAISS index built from chunk embeddings."""

from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--index-path", default="indexes/faiss_flat.index")
    parser.add_argument("--meta-path", default="indexes/faiss_meta.jsonl")
    parser.add_argument("--model", default="BAAI/bge-large-zh-v1.5")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--no-normalize", action="store_true")
    parser.add_argument("--use-fp16", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    index = load_faiss_index(ROOT / args.index_path)
    metadata = load_chunk_metadata(ROOT / args.meta_path)

    config = EmbeddingConfig(
        model_name=args.model,
        batch_size=args.batch_size,
        max_length=args.max_length,
        normalize=not args.no_normalize,
        use_fp16=args.use_fp16,
    )
    embedder = FlagEmbeddingModel(config)
    query_vector = embedder.encode_queries([args.query])
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
