#!/usr/bin/env python
"""Build a FAISS Flat index with FlagEmbedding vectors."""

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
    build_flat_index,
    save_chunk_metadata,
    save_faiss_index,
)
from financial_report_rag.utils import read_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", default="data/processed/chunks.jsonl")
    parser.add_argument("--index-path", default="indexes/faiss_flat.index")
    parser.add_argument("--meta-path", default="indexes/faiss_meta.jsonl")
    parser.add_argument("--model", default="BAAI/bge-large-zh-v1.5")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--limit", type=int, default=0, help="Index only the first N chunks.")
    parser.add_argument("--no-normalize", action="store_true")
    parser.add_argument("--use-fp16", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chunks_path = ROOT / args.chunks
    index_path = ROOT / args.index_path
    meta_path = ROOT / args.meta_path

    chunks = [chunk for chunk in read_jsonl(chunks_path) if chunk.get("text", "").strip()]
    if args.limit:
        chunks = chunks[: args.limit]
    if not chunks:
        raise SystemExit(f"No chunks found in {chunks_path}")

    config = EmbeddingConfig(
        model_name=args.model,
        batch_size=args.batch_size,
        max_length=args.max_length,
        normalize=not args.no_normalize,
        use_fp16=args.use_fp16,
    )
    embedder = FlagEmbeddingModel(config)
    texts = [chunk["text"] for chunk in chunks]
    vectors = embedder.encode_passages(texts)
    index = build_flat_index(vectors)

    save_faiss_index(index, index_path)
    saved = save_chunk_metadata(chunks, meta_path)

    print(f"chunks: {saved}")
    print(f"dimension: {vectors.shape[1]}")
    print(f"index: {index_path.relative_to(ROOT)}")
    print(f"metadata: {meta_path.relative_to(ROOT)}")
    print(f"model: {args.model}")


if __name__ == "__main__":
    main()
