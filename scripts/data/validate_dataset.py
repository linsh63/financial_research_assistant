#!/usr/bin/env python
"""Lightweight dataset checks for the PDF corpus."""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
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

from financial_report_rag.data.manifest import discover_pdfs, load_manifest  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="docs/data_collection/pdf_manifest.csv")
    parser.add_argument("--raw-dir", default="data/raw")
    parser.add_argument("--show", type=int, default=10, help="Max examples to print per issue.")
    return parser.parse_args()


def print_examples(title: str, values: list[str], limit: int) -> None:
    print(f"{title}: {len(values)}")
    for value in values[:limit]:
        print(f"  - {value}")
    if len(values) > limit:
        print(f"  ... {len(values) - limit} more")


def main() -> None:
    args = parse_args()
    manifest_path = ROOT / args.manifest
    raw_dir = ROOT / args.raw_dir

    records = load_manifest(manifest_path, ROOT)
    raw_records = discover_pdfs(raw_dir, ROOT)

    doc_id_counts = Counter(record.doc_id for record in records)
    path_counts = Counter(str(record.file_path.relative_to(ROOT)) for record in records)
    duplicate_doc_ids = sorted(doc_id for doc_id, count in doc_id_counts.items() if count > 1)
    duplicate_paths = sorted(path for path, count in path_counts.items() if count > 1)
    missing_paths = sorted(
        str(record.file_path.relative_to(ROOT)) for record in records if not record.file_path.exists()
    )

    manifest_paths = {record.file_path.resolve() for record in records}
    unlisted_pdfs = sorted(
        str(record.file_path.relative_to(ROOT))
        for record in raw_records
        if record.file_path.resolve() not in manifest_paths
    )

    industry_counts = Counter(record.industry or "(empty)" for record in records)
    doc_type_counts = Counter(record.doc_type or "(empty)" for record in records)
    pages_by_industry: dict[str, int] = defaultdict(int)
    size_by_industry: dict[str, int] = defaultdict(int)
    missing_page_count = 0

    for record in records:
        industry = record.industry or "(empty)"
        if record.expected_pages is None:
            missing_page_count += 1
        else:
            pages_by_industry[industry] += record.expected_pages
        if record.file_path.exists():
            size_by_industry[industry] += record.file_path.stat().st_size

    print("Dataset validation")
    print(f"manifest: {manifest_path.relative_to(ROOT)}")
    print(f"raw_dir: {raw_dir.relative_to(ROOT)}")
    print(f"manifest_records: {len(records)}")
    print(f"raw_pdfs: {len(raw_records)}")
    print(f"missing_page_count: {missing_page_count}")
    print()

    print("By industry")
    for industry, count in sorted(industry_counts.items()):
        pages = pages_by_industry.get(industry, 0)
        size_mb = size_by_industry.get(industry, 0) / 1024 / 1024
        print(f"  {industry}: files={count}, pages={pages}, size_mb={size_mb:.1f}")
    print()

    print("By doc_type")
    for doc_type, count in sorted(doc_type_counts.items()):
        print(f"  {doc_type}: {count}")
    print()

    print_examples("duplicate_doc_ids", duplicate_doc_ids, args.show)
    print_examples("duplicate_paths", duplicate_paths, args.show)
    print_examples("missing_paths", missing_paths, args.show)
    print_examples("unlisted_pdfs", unlisted_pdfs, args.show)

    has_problem = bool(duplicate_doc_ids or duplicate_paths or missing_paths or unlisted_pdfs)
    print()
    print("status: FAIL" if has_problem else "status: OK")
    if has_problem:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
