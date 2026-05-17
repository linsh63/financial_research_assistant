#!/usr/bin/env python
"""使用 FlagEmbedding 向量构建 FAISS Flat / IVF / HNSW 索引。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

import numpy as np


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
    save_chunk_metadata,
)
from financial_report_rag.utils import read_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    """读取命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", default="data/processed/chunks/samples/chunks_deepdoc_sample.jsonl")
    parser.add_argument("--output-dir", default="data/processed/indexes/samples/bge_large_zh_v15_sample")
    parser.add_argument("--model", default="BAAI/bge-large-zh-v1.5")
    parser.add_argument(
        "--backend",
        choices=["sentence-transformers", "flagembedding"],
        default="sentence-transformers",
        help="embedding 编码后端；Mac 本地推荐 sentence-transformers，服务器可用 flagembedding。",
    )
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--limit", type=int, default=0, help="只索引前 N 个 chunk，0 表示全部。")
    parser.add_argument("--no-normalize", action="store_true")
    parser.add_argument("--use-fp16", action="store_true")
    parser.add_argument("--force-embeddings", action="store_true", help="即使 embeddings.npy 已存在也重新编码。")
    parser.add_argument(
        "--index-types",
        nargs="+",
        choices=["flat", "ivf", "hnsw"],
        default=["flat", "ivf", "hnsw"],
        help="要构建的 FAISS 索引类型。",
    )
    parser.add_argument("--metric", choices=["ip", "l2"], default="ip")
    parser.add_argument("--ivf-nlist", type=int, default=64)
    parser.add_argument("--ivf-nprobe", type=int, default=8)
    parser.add_argument("--hnsw-m", type=int, default=32)
    parser.add_argument("--hnsw-ef-construction", type=int, default=200)
    parser.add_argument("--hnsw-ef-search", type=int, default=64)
    return parser.parse_args()


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


def load_chunks(chunks_path: Path, limit: int) -> list[dict]:
    """读取可被索引的 chunk 记录。"""
    chunks = [chunk for chunk in read_jsonl(chunks_path) if chunk.get("text", "").strip()]
    if limit:
        chunks = chunks[:limit]
    if not chunks:
        raise SystemExit(f"No chunks found in {chunks_path}")
    return chunks


def encode_or_load_vectors(
    chunks: list[dict],
    output_dir: Path,
    config: EmbeddingConfig,
    force_embeddings: bool,
) -> tuple[np.ndarray, str]:
    """只编码一次文本，并把 embeddings.npy 作为后续索引共用缓存。"""
    embedding_path = output_dir / "embeddings.npy"
    if embedding_path.exists() and not force_embeddings:
        vectors = np.load(embedding_path)
        if vectors.shape[0] != len(chunks):
            raise SystemExit(
                f"已有 embeddings 行数为 {vectors.shape[0]}，但 chunk 数为 {len(chunks)}；"
                "请加 --force-embeddings 重新编码。"
            )
        return vectors.astype("float32"), "reused"

    embedder = FlagEmbeddingModel(config)
    vectors = embedder.encode_passages([chunk["text"] for chunk in chunks])
    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(embedding_path, vectors.astype("float32"))
    return vectors.astype("float32"), "encoded"


def write_manifest(output_dir: Path, manifest: dict) -> Path:
    """保存索引构建登记信息。"""
    path = output_dir / "index_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_indexes_in_subprocess(args: argparse.Namespace, embedding_path: Path, output_dir: Path) -> list[dict]:
    """在独立进程中构建 FAISS 索引，避免 torch 与 FAISS IVF 在 Mac 上冲突。"""
    helper = Path(__file__).resolve().parent / "build_faiss_indexes_from_embeddings.py"
    with tempfile.NamedTemporaryFile(prefix="faiss_index_records_", suffix=".json", delete=False) as tmp:
        records_path = Path(tmp.name)

    command = [
        sys.executable,
        str(helper),
        "--embeddings",
        str(embedding_path),
        "--output-dir",
        str(output_dir),
        "--records-path",
        str(records_path),
        "--metric",
        args.metric,
        "--ivf-nlist",
        str(args.ivf_nlist),
        "--ivf-nprobe",
        str(args.ivf_nprobe),
        "--hnsw-m",
        str(args.hnsw_m),
        "--hnsw-ef-construction",
        str(args.hnsw_ef_construction),
        "--hnsw-ef-search",
        str(args.hnsw_ef_search),
        "--index-types",
        *args.index_types,
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    try:
        return json.loads(records_path.read_text(encoding="utf-8"))
    finally:
        records_path.unlink(missing_ok=True)


def main() -> None:
    """执行向量编码、三类 FAISS 索引构建和登记。"""
    args = parse_args()
    chunks_path = resolve_path(args.chunks)
    output_dir = resolve_path(args.output_dir)
    metadata_path = output_dir / "chunks_meta.jsonl"
    embedding_path = output_dir / "embeddings.npy"

    output_dir.mkdir(parents=True, exist_ok=True)
    chunks = load_chunks(chunks_path, args.limit)
    saved = save_chunk_metadata(chunks, metadata_path)

    embedding_config = EmbeddingConfig(
        model_name=args.model,
        backend=args.backend,
        batch_size=args.batch_size,
        max_length=args.max_length,
        normalize=not args.no_normalize,
        use_fp16=args.use_fp16,
    )
    start_embedding = time.perf_counter()
    vectors, embedding_status = encode_or_load_vectors(
        chunks,
        output_dir=output_dir,
        config=embedding_config,
        force_embeddings=args.force_embeddings,
    )
    embedding_seconds = time.perf_counter() - start_embedding

    index_records = build_indexes_in_subprocess(args, embedding_path, output_dir)

    manifest = {
        "built_at": datetime.now().isoformat(timespec="seconds"),
        "chunks_path": display_path(chunks_path),
        "metadata_path": display_path(metadata_path),
        "embedding_path": display_path(embedding_path),
        "embedding_status": embedding_status,
        "embedding_seconds": round(embedding_seconds, 4),
        "model": args.model,
        "backend": args.backend,
        "batch_size": args.batch_size,
        "max_length": args.max_length,
        "normalize": not args.no_normalize,
        "use_fp16": args.use_fp16,
        "chunk_count": saved,
        "vector_dimension": int(vectors.shape[1]),
        "indexes": index_records,
    }
    manifest_path = write_manifest(output_dir, manifest)

    print(f"chunks: {saved}")
    print(f"dimension: {vectors.shape[1]}")
    print(f"embeddings: {display_path(embedding_path)} ({embedding_status})")
    print(f"metadata: {display_path(metadata_path)}")
    for record in index_records:
        print(
            f"index[{record['index_type']}]: {record['path']} "
            f"build_seconds={record['build_seconds']} size_mb={record['file_size_mb']}"
        )
    print(f"manifest: {display_path(manifest_path)}")
    print(f"model: {args.model}")


if __name__ == "__main__":
    main()
