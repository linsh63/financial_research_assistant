#!/usr/bin/env python
"""把 chunk JSONL 中的 bbox 可视化到原始 PDF 上。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import fitz


def find_project_root() -> Path:
    """从脚本位置向上查找项目根目录。"""
    for parent in Path(__file__).resolve().parents:
        if (parent / "src" / "financial_report_rag").exists():
            return parent
    raise RuntimeError("无法定位项目根目录")


ROOT = find_project_root()


def parse_args() -> argparse.Namespace:
    """读取命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chunks",
        required=True,
        help="chunk JSONL 文件，例如 data/processed/chunks/chunks_deepdoc_sample.jsonl。",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed/visualizations/chunks",
        help="输出 PDF 目录。每个 source PDF 会生成一个可视化 PDF。",
    )
    parser.add_argument(
        "--output",
        default="",
        help="只在输入 JSONL 对应单个 source PDF 时使用，指定单个输出 PDF 路径。",
    )
    parser.add_argument(
        "--with-labels",
        action="store_true",
        help="在红框左上角写入 chunk_id。",
    )
    parser.add_argument(
        "--include-cells",
        action="store_true",
        help="除了 chunk bbox，也画出 table.cells 里的单元格细框。",
    )
    return parser.parse_args()


def read_chunks(path: Path) -> list[dict[str, Any]]:
    """读取 chunk JSONL。"""
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL 第 {line_no} 行解析失败：{path}") from exc
    return rows


def resolve_path(path_text: str, *, search_processed: bool = False) -> Path:
    """把输入路径解析为绝对路径，可兼容 @filename 这种写法。"""
    cleaned = path_text[1:] if path_text.startswith("@") else path_text
    path = Path(cleaned)
    if path.is_absolute():
        return path
    root_path = ROOT / path
    if root_path.exists() or not search_processed:
        return root_path
    for processed_path in [
        ROOT / "data" / "processed" / path,
        ROOT / "data" / "processed" / path.name,
        ROOT / "data" / "processed" / "chunks" / path.name,
        ROOT / "data" / "processed" / "pages" / path.name,
    ]:
        if processed_path.exists():
            return processed_path
    return root_path


def display_path(path: Path) -> str:
    """优先用项目相对路径展示输出位置。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def chunk_bbox(chunk: dict[str, Any]) -> list[float] | None:
    """读取 chunk 的主 bbox，表格优先用 table.bbox，否则用 section.bbox。"""
    if chunk.get("has_table"):
        bbox = (chunk.get("table") or {}).get("bbox")
        if valid_bbox(bbox):
            return [float(v) for v in bbox]
    bbox = (chunk.get("section") or {}).get("bbox")
    if valid_bbox(bbox):
        return [float(v) for v in bbox]
    return None


def cell_bboxes(chunk: dict[str, Any]) -> list[list[float]]:
    """读取表格单元格 bbox。"""
    cells = (chunk.get("table") or {}).get("cells") or []
    bboxes = []
    for cell in cells:
        bbox = cell.get("bbox")
        if valid_bbox(bbox):
            bboxes.append([float(v) for v in bbox])
    return bboxes


def valid_bbox(bbox: object) -> bool:
    """判断 bbox 是否是 [x0, top, x1, bottom]。"""
    if not isinstance(bbox, list) or len(bbox) != 4:
        return False
    try:
        x0, top, x1, bottom = [float(v) for v in bbox]
    except (TypeError, ValueError):
        return False
    return x1 > x0 and bottom > top


def safe_stem(source: str) -> str:
    """把 source 路径转成安全文件名。"""
    stem = Path(source).stem
    stem = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff_.-]+", "_", stem)
    return stem or "visualized"


def grouped_by_source(chunks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """按原始 PDF source 分组。"""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for chunk in chunks:
        source = chunk.get("source")
        if source:
            grouped[str(source)].append(chunk)
    return dict(grouped)


def page_numbers(chunk: dict[str, Any]) -> list[int]:
    """读取 chunk 所在页码，默认使用第 1 页。"""
    pages = chunk.get("pages") or [1]
    result = []
    for page in pages:
        try:
            page_no = int(page)
        except (TypeError, ValueError):
            continue
        if page_no >= 1:
            result.append(page_no)
    return result or [1]


def draw_chunk(page: fitz.Page, chunk: dict[str, Any], include_cells: bool, with_labels: bool) -> bool:
    """在 PDF 页面上绘制单个 chunk 的红色 bbox。"""
    bbox = chunk_bbox(chunk)
    if not bbox:
        return False

    page_rect = page.rect
    rect = fitz.Rect(bbox) & page_rect
    if rect.is_empty:
        return False

    page.draw_rect(rect, color=(1, 0, 0), width=1.4, overlay=True)
    if include_cells:
        for cell_bbox in cell_bboxes(chunk):
            cell_rect = fitz.Rect(cell_bbox) & page_rect
            if not cell_rect.is_empty:
                page.draw_rect(cell_rect, color=(1, 0, 0), width=0.45, overlay=True)

    if with_labels:
        label = str(chunk.get("chunk_id", ""))[:80]
        if label:
            pos = fitz.Point(rect.x0, max(8, rect.y0 - 2))
            page.insert_text(pos, label, fontsize=6, color=(1, 0, 0), overlay=True)
    return True


def visualize_source(
    source: str,
    chunks: list[dict[str, Any]],
    output_path: Path,
    include_cells: bool,
    with_labels: bool,
) -> tuple[int, int]:
    """给一个源 PDF 绘制所有 chunk 框并保存。"""
    source_path = resolve_path(source)
    if not source_path.exists():
        raise FileNotFoundError(f"找不到源 PDF：{source_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    drawn = 0
    skipped = 0
    doc = fitz.open(source_path)
    try:
        for chunk in chunks:
            bbox = chunk_bbox(chunk)
            if not bbox:
                skipped += 1
                continue
            ok = False
            for page_no in page_numbers(chunk):
                page_index = page_no - 1
                if page_index < 0 or page_index >= len(doc):
                    continue
                ok = draw_chunk(doc[page_index], chunk, include_cells, with_labels) or ok
            if ok:
                drawn += 1
            else:
                skipped += 1
        doc.save(output_path)
    finally:
        doc.close()
    return drawn, skipped


def main() -> None:
    """执行 chunk bbox 可视化。"""
    args = parse_args()
    chunks_path = resolve_path(args.chunks, search_processed=True)
    output_dir = resolve_path(args.output_dir)
    chunks = read_chunks(chunks_path)
    grouped = grouped_by_source(chunks)
    if not grouped:
        print("没有找到带 source 字段的 chunk。", file=sys.stderr)
        raise SystemExit(1)

    if args.output and len(grouped) != 1:
        print("--output 只能在 JSONL 只包含一个 source PDF 时使用。", file=sys.stderr)
        raise SystemExit(1)

    total_drawn = 0
    total_skipped = 0
    for source, source_chunks in grouped.items():
        if args.output:
            output_path = resolve_path(args.output)
        else:
            output_path = output_dir / f"{safe_stem(source)}_chunks_red_boxes.pdf"
        drawn, skipped = visualize_source(
            source,
            source_chunks,
            output_path,
            include_cells=args.include_cells,
            with_labels=args.with_labels,
        )
        total_drawn += drawn
        total_skipped += skipped
        print(f"source: {source}")
        print(f"output: {display_path(output_path)}")
        print(f"drawn: {drawn}, skipped: {skipped}")

    print(f"total_drawn: {total_drawn}")
    print(f"total_skipped: {total_skipped}")


if __name__ == "__main__":
    main()
