#!/usr/bin/env python
"""Inspect chunks by keyword or document id."""

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

from financial_report_rag.utils import preview, read_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", default="data/processed/chunks.jsonl")
    parser.add_argument("--keyword", default="")
    parser.add_argument("--doc-id", default="")
    parser.add_argument("--limit", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    chunks_path = ROOT / args.chunks
    matched = 0

    for chunk in read_jsonl(chunks_path):
        text = chunk.get("text", "")
        if args.keyword and args.keyword not in text:
            continue
        if args.doc_id and chunk.get("doc_id") != args.doc_id:
            continue

        matched += 1
        print("=" * 80)
        print(f"chunk_id: {chunk.get('chunk_id')}")
        print(f"doc_id: {chunk.get('doc_id')}")
        print(f"source: {chunk.get('source')}")
        print(f"pages: {chunk.get('pages')}")
        print(f"type: {chunk.get('chunk_type')}  has_table: {chunk.get('has_table')}")
        metadata = chunk.get("metadata", {})
        print(f"title: {metadata.get('title', '')}")
        print(preview(text, 600))
        if matched >= args.limit:
            break

    print("=" * 80)
    print(f"matched: {matched}")


if __name__ == "__main__":
    main()
