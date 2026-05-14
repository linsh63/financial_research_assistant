#!/usr/bin/env python
"""运行第一周的切块参数对比实验。"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
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
from financial_report_rag.utils import ensure_parent, read_jsonl, write_jsonl  # noqa: E402

DEFAULT_CONFIGS = [(256, 50), (512, 100), (1024, 200)]


def parse_config(value: str) -> tuple[int, int]:
    """把命令行中的 size:overlap 参数解析为整数二元组。"""
    if ":" in value:
        left, right = value.split(":", 1)
    elif "," in value:
        left, right = value.split(",", 1)
    else:
        raise argparse.ArgumentTypeError("配置格式应为 512:100 或 512,100")

    chunk_size = int(left)
    overlap = int(right)
    if chunk_size <= 0:
        raise argparse.ArgumentTypeError("chunk_size 必须为正数")
    if overlap < 0 or overlap >= chunk_size:
        raise argparse.ArgumentTypeError("overlap 必须大于等于 0 且小于 chunk_size")
    return chunk_size, overlap


def parse_args() -> argparse.Namespace:
    """读取切块实验需要的命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/processed/pages_deepdoc.jsonl")
    parser.add_argument("--output-dir", default="data/processed/chunking_experiment")
    parser.add_argument("--report", default="docs/experiments/chunking_experiment.md")
    parser.add_argument(
        "--config",
        action="append",
        type=parse_config,
        help="切块配置，格式为 512:100；可重复传入。",
    )
    return parser.parse_args()


def load_pages(path: Path) -> list[dict]:
    """一次性读取解析后的 page 记录，方便多组参数复用。"""
    pages = list(read_jsonl(path))
    if not pages:
        raise ValueError(f"没有读到页面记录：{path}")
    return pages


def page_stats(pages: list[dict]) -> dict:
    """统计页面、文档、行业和表格来源的基础信息。"""
    doc_ids = {page.get("doc_id") for page in pages}
    industries = Counter(page.get("metadata", {}).get("industry") or "未标注" for page in pages)
    table_sources = Counter()
    table_count = 0

    for page in pages:
        for table in page.get("tables", []):
            table_count += 1
            table_sources[table.get("source") or "unknown"] += 1

    return {
        "page_count": len(pages),
        "doc_count": len(doc_ids),
        "industry_page_counts": dict(sorted(industries.items())),
        "source_table_count": table_count,
        "table_sources": dict(sorted(table_sources.items())),
    }


def safe_mean(values: list[int]) -> float:
    """计算均值；空列表返回 0，便于报告稳定输出。"""
    return statistics.mean(values) if values else 0.0


def safe_median(values: list[int]) -> float:
    """计算中位数；空列表返回 0，便于报告稳定输出。"""
    return statistics.median(values) if values else 0.0


def chunk_stats(chunks: list[dict], chunk_size: int, overlap: int, output_path: Path) -> dict:
    """统计一组切块结果的数量、长度和表格保护状态。"""
    lengths = [len(chunk.get("text", "")) for chunk in chunks]
    chunk_types = Counter(chunk.get("chunk_type") or "unknown" for chunk in chunks)
    table_chunks = [chunk for chunk in chunks if chunk.get("has_table")]
    split_tables = [
        chunk
        for chunk in table_chunks
        if int(chunk.get("table", {}).get("part_count") or 1) > 1
    ]
    missing_table_protection = [
        chunk
        for chunk in table_chunks
        if chunk.get("table", {}).get("table_protection") != "row_boundary"
    ]
    doc_ids = {chunk.get("doc_id") for chunk in chunks}

    return {
        "chunk_size": chunk_size,
        "overlap": overlap,
        "output": str(output_path.relative_to(ROOT)),
        "doc_count": len(doc_ids),
        "chunk_count": len(chunks),
        "text_chunk_count": chunk_types.get("text", 0),
        "title_chunk_count": chunk_types.get("title", 0),
        "table_chunk_count": chunk_types.get("table", 0),
        "has_table_count": len(table_chunks),
        "split_table_chunk_count": len(split_tables),
        "table_protection_missing": len(missing_table_protection),
        "avg_chars": round(safe_mean(lengths), 1),
        "median_chars": round(safe_median(lengths), 1),
        "max_chars": max(lengths) if lengths else 0,
    }


def run_one_config(pages: list[dict], output_dir: Path, chunk_size: int, overlap: int) -> dict:
    """运行单组切块参数，并把结果写入独立 JSONL 文件。"""
    output_path = output_dir / f"chunks_{chunk_size}_{overlap}.jsonl"
    chunks = list(chunk_pages(pages, chunk_size=chunk_size, overlap=overlap))
    write_jsonl(output_path, chunks)
    return chunk_stats(chunks, chunk_size, overlap, output_path)


def format_source_tables(stats: dict) -> str:
    """把表格来源统计压缩成一行，便于写进 Markdown 报告。"""
    table_sources = stats["table_sources"]
    if not table_sources:
        return "无"
    return "，".join(f"{name}: {count}" for name, count in table_sources.items())


def format_industries(stats: dict) -> str:
    """把行业页面统计压缩成一行，便于写进 Markdown 报告。"""
    industries = stats["industry_page_counts"]
    if not industries:
        return "未标注"
    return "，".join(f"{name}: {count}" for name, count in industries.items())


def build_report(input_path: Path, page_summary: dict, experiment_rows: list[dict]) -> str:
    """生成切块实验的 Markdown 报告文本。"""
    lines = [
        "# 第一周切块实验",
        "",
        "## 数据概况",
        "",
        f"- 输入文件：`{input_path.relative_to(ROOT)}`",
        f"- 文档数：{page_summary['doc_count']}",
        f"- 页面数：{page_summary['page_count']}",
        f"- 解析出的表格数：{page_summary['source_table_count']}",
        f"- 表格来源：{format_source_tables(page_summary)}",
        f"- 行业页面分布：{format_industries(page_summary)}",
        "",
        "## 参数对比",
        "",
        "| chunk size | overlap | chunk 数 | 平均长度 | 中位长度 | 最大长度 | 表格 chunk | 拆分表格 chunk | 表格保护缺失 | Recall@5 | 输出 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]

    for row in experiment_rows:
        lines.append(
            "| {chunk_size} | {overlap} | {chunk_count} | {avg_chars} | {median_chars} | "
            "{max_chars} | {table_chunk_count} | {split_table_chunk_count} | "
            "{table_protection_missing} | 待召回评测 | `{output}` |".format(**row)
        )

    lines.extend(
        [
            "",
            "## 备注",
            "",
            "- 本阶段只做切块对比，不提前伪造 Recall@5；召回指标需要等 FAISS + FlagEmbedding 索引和评测集接入后再补。",
            "- 表格 chunk 使用 `row_boundary` 保护策略，允许按行分成多个 chunk，但不切断单个表格行。",
        ]
    )
    return "\n".join(lines) + "\n"


def write_report(path: Path, text: str) -> None:
    """把实验报告写入 Markdown 文件。"""
    ensure_parent(path)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    """按配置批量运行切块实验，并输出报告位置。"""
    args = parse_args()
    input_path = ROOT / args.input
    output_dir = ROOT / args.output_dir
    report_path = ROOT / args.report
    configs = args.config or DEFAULT_CONFIGS

    pages = load_pages(input_path)
    summary = page_stats(pages)
    rows = [run_one_config(pages, output_dir, chunk_size, overlap) for chunk_size, overlap in configs]
    report = build_report(input_path, summary, rows)
    write_report(report_path, report)

    print(report)
    print(f"report: {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
