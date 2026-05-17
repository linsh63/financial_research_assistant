#!/usr/bin/env python
"""基于 chunks_meta.jsonl 构建 BM25 关键词索引。"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
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
from financial_report_rag.utils import read_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    """读取命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks-meta", default="data/processed/indexes/samples/bge_large_zh_v15_sample/chunks_meta.jsonl")
    parser.add_argument("--output-dir", default="data/processed/indexes/samples/bge_large_zh_v15_sample")
    parser.add_argument("--output-name", default="bm25.pkl")
    parser.add_argument("--tokenizer", choices=["jieba", "fallback"], default="jieba")
    parser.add_argument("--include-source", action="store_true", help="把 source 文件名也加入 BM25 检索文本。")
    parser.add_argument("--limit", type=int, default=0, help="只索引前 N 个 chunk，0 表示全部。")
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


def load_chunks(path: Path, limit: int) -> list[dict]:
    """读取向量索引配套的 chunk 元数据。"""
    chunks = [chunk for chunk in read_jsonl(path) if chunk.get("text", "").strip()]
    if limit:
        chunks = chunks[:limit]
    if not chunks:
        raise SystemExit(f"No chunks found in {path}")
    return chunks


def write_manifest(output_dir: Path, manifest: dict) -> Path:
    """保存 BM25 构建登记信息。"""
    path = output_dir / "bm25_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    """构建 BM25 索引并写入索引目录。"""
    args = parse_args()
    chunks_meta_path = resolve_path(args.chunks_meta)
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / args.output_name

    chunks = load_chunks(chunks_meta_path, args.limit)
    start = time.perf_counter()
    store = BM25Store.from_chunks(chunks, tokenizer=args.tokenizer, include_source=args.include_source)
    store.save(output_path)
    build_seconds = time.perf_counter() - start
    info = store.build_info()

    manifest = {
        "built_at": datetime.now().isoformat(timespec="seconds"),
        "chunks_meta_path": display_path(chunks_meta_path),
        "bm25_path": display_path(output_path),
        "chunk_count": info.chunk_count,
        "token_count": info.token_count,
        "requested_tokenizer": args.tokenizer,
        "tokenizer": info.tokenizer,
        "include_source": info.include_source,
        "build_seconds": round(build_seconds, 4),
        "file_size_mb": round(output_path.stat().st_size / 1024 / 1024, 4),
    }
    manifest_path = write_manifest(output_dir, manifest)

    print(f"chunks: {info.chunk_count}")
    print(f"tokens: {info.token_count}")
    print(f"bm25: {display_path(output_path)}")
    print(f"manifest: {display_path(manifest_path)}")
    print(f"build_seconds: {build_seconds:.4f}")


if __name__ == "__main__":
    main()
