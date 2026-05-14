#!/usr/bin/env python
"""Parse PDFs into page-level JSONL records."""

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

from financial_report_rag.data.manifest import load_documents  # noqa: E402
from financial_report_rag.parsing.pdf_parser import parse_documents  # noqa: E402
from financial_report_rag.utils import write_jsonl  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="docs/data_collection/pdf_manifest.csv")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--output", default="data/processed/pages.jsonl")
    parser.add_argument("--limit", type=int, default=0, help="Parse only the first N documents.")
    parser.add_argument(
        "--manifest-only",
        action="store_true",
        help="Only parse PDFs listed in the manifest.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = ROOT / args.manifest
    raw_dir = ROOT / args.raw_dir
    output_path = ROOT / args.output

    records = load_documents(
        manifest_path=manifest_path,
        raw_dir=raw_dir,
        project_root=ROOT,
        include_unlisted=not args.manifest_only,
    )
    if args.limit:
        records = records[: args.limit]

    print(f"documents: {len(records)}")
    for record in records:
        print(f"parse: {record.doc_id} -> {record.file_path}")

    count = write_jsonl(output_path, parse_documents(records, ROOT))
    print(f"pages: {count}")
    print(f"output: {output_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
