#!/usr/bin/env python
"""检索已经构建好的 BM25 索引。"""

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

from financial_report_rag.retrieval.bm25_store import BM25Store  # noqa: E402
from financial_report_rag.utils import preview  # noqa: E402


def parse_args() -> argparse.Namespace:
    """读取命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--index-dir", default="data/processed/indexes/bge_large_zh_v15")
    parser.add_argument("--bm25-path", default="")
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析成绝对路径。"""
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def resolve_bm25_path(args: argparse.Namespace) -> Path:
    """根据 index-dir 或显式路径确定 BM25 索引文件。"""
    if args.bm25_path:
        return resolve_path(args.bm25_path)
    return resolve_path(args.index_dir) / "bm25.pkl"


def main() -> None:
    """执行一次 BM25 检索并打印结果。"""
    args = parse_args()
    bm25_path = resolve_bm25_path(args)
    if not bm25_path.exists():
        raise SystemExit(f"BM25 index not found: {bm25_path}")
    store = BM25Store.load(bm25_path)
    results = store.search(args.query, top_k=args.top_k)

    for result in results:
        chunk = result.chunk
        print("=" * 80)
        print(f"rank: {result.rank}  bm25_score: {result.score:.4f}")
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
