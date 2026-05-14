#!/usr/bin/env python
"""Build chunk-level JSONL records from parsed pages."""

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

from financial_report_rag.processing.chunker import chunk_pages  # noqa: E402
from financial_report_rag.utils import read_jsonl, write_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/processed/pages.jsonl")
    parser.add_argument("--output", default="data/processed/chunks.jsonl")
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--overlap", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = ROOT / args.input
    output_path = ROOT / args.output

    pages = read_jsonl(input_path)
    chunks = chunk_pages(pages, args.chunk_size, args.overlap)
    count = write_jsonl(output_path, chunks)
    print(f"chunks: {count}")
    print(f"output: {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
