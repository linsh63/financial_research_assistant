"""DeepDoc 风格的 PDF 解析：文本框、版面区域和表格结构。

本模块参考 RAGFlow DeepDoc 的主流程组织：

1. 从每页 PDF 中抽取类似 OCR 结果的文本框；
2. 给文本框标注 header/footer/title/text/table 等版面类型；
3. 单独抽取并保护表格区域；
4. 把非表格文本框合并成有阅读顺序的 sections，供后续切块使用。

为了适合本地 Mac 开发，当前 OCR 阶段先使用 PyMuPDF 的数字 PDF 文本框，
而不是神经网络 OCR。输出结构保留 OCR/layout/table 的边界，方便以后替换
成真正的 OCR 和版面识别模型。
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import median
from typing import Iterable, List, Optional

import fitz
import pdfplumber

from ..data.manifest import DocumentRecord
from .table_structure import (
    StructuredTable,
    construct_table,
    construct_table_from_rows,
    construct_table_from_text_boxes,
)
from ..utils import normalize_whitespace


@dataclass
class TextBox:
    box_id: str
    page: int
    text: str
    x0: float
    top: float
    x1: float
    bottom: float
    font_size: float = 0.0
    block_no: int = 0
    line_no: int = 0
    source: str = "pymupdf_text"
    layout_type: str = ""
    layoutno: str = ""
    col_id: int = 0


@dataclass
class LayoutRegion:
    region_id: str
    page: int
    type: str
    x0: float
    top: float
    x1: float
    bottom: float
    score: float = 1.0
    source: str = "heuristic"


@dataclass
class ParsedSection:
    section_id: str
    page: int
    text: str
    layout_type: str
    layoutno: str
    col_id: int
    bbox: list[float]
    box_ids: list[str] = field(default_factory=list)


@dataclass
class ParsedPage:
    doc_id: str
    source: str
    page: int
    text: str
    sections: List[dict]
    tables: List[dict]
    layout_regions: List[dict]
    text_boxes: List[dict]
    metadata: dict
    parser: dict


def _clean_line(text: str) -> str:
    """清理单行文本中的多余空白。"""
    return normalize_whitespace(text).replace("\n", " ").strip()


def _round(value: float) -> float:
    """统一坐标数值精度。"""
    return round(float(value), 2)


def _bbox_from_values(x0: float, top: float, x1: float, bottom: float) -> list[float]:
    """用四个坐标值生成标准 bbox。"""
    return [_round(x0), _round(top), _round(x1), _round(bottom)]


def _box_area(box: TextBox) -> float:
    """计算文本框面积。"""
    return max(0.0, box.x1 - box.x0) * max(0.0, box.bottom - box.top)


def _overlap_ratio(box: TextBox, bbox: list[float]) -> float:
    """计算文本框落入目标区域的面积比例。"""
    left = max(box.x0, bbox[0])
    top = max(box.top, bbox[1])
    right = min(box.x1, bbox[2])
    bottom = min(box.bottom, bbox[3])
    area = max(0.0, right - left) * max(0.0, bottom - top)
    base = _box_area(box)
    if base <= 0:
        return 0.0
    return area / base


def _union_bbox(boxes: list[TextBox]) -> list[float]:
    """合并多个文本框的外接 bbox。"""
    return _bbox_from_values(
        min(box.x0 for box in boxes),
        min(box.top for box in boxes),
        max(box.x1 for box in boxes),
        max(box.bottom for box in boxes),
    )


def _extract_text_boxes(path: Path, doc_id: str) -> tuple[dict[int, list[TextBox]], dict[int, tuple[float, float]]]:
    """用 PyMuPDF 抽取每页的 OCR-like 文本框。"""
    pages: dict[int, list[TextBox]] = {}
    page_sizes: dict[int, tuple[float, float]] = {}
    doc = fitz.open(path)
    try:
        for page_index, page in enumerate(doc, start=1):
            page_sizes[page_index] = (float(page.rect.width), float(page.rect.height))
            page_dict = page.get_text("dict", sort=True)
            boxes: list[TextBox] = []
            for block_index, block in enumerate(page_dict.get("blocks", []), start=1):
                if block.get("type") != 0:
                    continue
                for line_index, line in enumerate(block.get("lines", []), start=1):
                    spans = line.get("spans", [])
                    text = _clean_line("".join(span.get("text", "") for span in spans))
                    if not text:
                        continue
                    x0, top, x1, bottom = line.get("bbox", [0, 0, 0, 0])
                    font_size = max((float(span.get("size", 0)) for span in spans), default=0.0)
                    boxes.append(
                        TextBox(
                            box_id=f"{doc_id}-p{page_index:03d}-b{block_index:03d}-l{line_index:03d}",
                            page=page_index,
                            text=text,
                            x0=float(x0),
                            top=float(top),
                            x1=float(x1),
                            bottom=float(bottom),
                            font_size=font_size,
                            block_no=block_index,
                            line_no=line_index,
                        )
                    )
            pages[page_index] = boxes
        return pages, page_sizes
    finally:
        doc.close()


def _extract_tables(
    path: Path,
    doc_id: str,
    boxes_by_page: dict[int, list[TextBox]],
) -> dict[int, list[StructuredTable]]:
    """用 pdfplumber 发现表格并重建结构化表格。"""
    by_page: dict[int, list[StructuredTable]] = defaultdict(list)
    with pdfplumber.open(path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            try:
                found_tables = page.find_tables() or []
            except Exception:
                found_tables = []

            if found_tables:
                for table_index, table_obj in enumerate(found_tables, start=1):
                    table_id = f"{doc_id}-p{page_index:03d}-t{table_index:03d}"
                    try:
                        table = construct_table(
                            table_id=table_id,
                            page=page_index,
                            table_obj=table_obj,
                            text_boxes=boxes_by_page.get(page_index, []),
                        )
                    except Exception:
                        continue
                    if table.text:
                        by_page[page_index].append(table)
                continue

            try:
                raw_tables = page.extract_tables() or []
            except Exception:
                raw_tables = []
            for table_index, rows in enumerate(raw_tables, start=1):
                table = construct_table_from_rows(
                    table_id=f"{doc_id}-p{page_index:03d}-t{table_index:03d}",
                    page=page_index,
                    rows=rows,
                )
                if not table.text:
                    continue
                by_page[page_index].append(table)
    _append_layout_detected_tables(doc_id, boxes_by_page, by_page)
    return by_page


def _append_layout_detected_tables(
    doc_id: str,
    boxes_by_page: dict[int, list[TextBox]],
    tables_by_page: dict[int, list[StructuredTable]],
) -> None:
    """用文本框行列对齐关系补充 pdfplumber 漏检的表格。"""
    for page, boxes in boxes_by_page.items():
        existing_bboxes = [table.bbox for table in tables_by_page.get(page, []) if table.bbox]
        free_boxes = [box for box in boxes if not _box_overlaps_any_table(box, existing_bboxes)]
        rows = _group_boxes_into_rows(free_boxes)
        table_runs = _find_table_row_runs(rows)

        for run_index, run in enumerate(table_runs, start=1):
            run = _trim_table_run_noise(run)
            if not _valid_table_run(run):
                continue
            all_run_boxes = [box for row in run for box in row]
            if _table_run_overlaps_existing(all_run_boxes, existing_bboxes):
                continue
            caption = _nearby_table_caption(rows, run)
            table_id = f"{doc_id}-p{page:03d}-layout-t{run_index:03d}"
            table = construct_table_from_text_boxes(
                table_id=table_id,
                page=page,
                row_boxes=run,
                caption=caption,
            )
            if table.text and table.rows >= 3 and table.columns >= 3:
                tables_by_page[page].append(table)


def _trim_table_run_noise(run: list[list[TextBox]]) -> list[list[TextBox]]:
    """根据表头年份列裁掉右侧联系人、图表等噪声文本框。"""
    header = next((row for row in run if sum(1 for box in row if _numeric_or_period_like(box.text)) >= 2), None)
    if not header:
        return run

    numeric_indexes = [idx for idx, box in enumerate(header) if _numeric_or_period_like(box.text)]
    if len(numeric_indexes) < 2:
        return run

    max_x = header[max(numeric_indexes)].x1 + 12
    trimmed = []
    for row in run:
        kept = [box for box in row if box.x0 <= max_x]
        if len(kept) >= 3:
            trimmed.append(kept)
    return trimmed


def _box_overlaps_any_table(box: TextBox, bboxes: list[list[float]]) -> bool:
    """判断文本框是否已经落入现有表格区域。"""
    return any(_overlap_ratio(box, bbox) >= 0.25 for bbox in bboxes)


def _group_boxes_into_rows(boxes: list[TextBox]) -> list[list[TextBox]]:
    """把同一水平线附近的文本框聚合成行。"""
    useful_boxes = [
        box
        for box in boxes
        if box.text
        and not _page_number_like(box.text)
        and not _disclaimer_like(box.text)
        and len(box.text) <= 120
    ]
    useful_boxes.sort(key=lambda box: ((box.top + box.bottom) / 2, box.x0))
    if not useful_boxes:
        return []

    heights = sorted(max(1.0, box.bottom - box.top) for box in useful_boxes)
    median_height = heights[len(heights) // 2]
    tolerance = max(3.0, median_height * 0.65)
    rows: list[list[TextBox]] = []
    centers: list[float] = []

    for box in useful_boxes:
        center = (box.top + box.bottom) / 2
        if rows and abs(center - centers[-1]) <= tolerance:
            rows[-1].append(box)
            centers[-1] = (centers[-1] * (len(rows[-1]) - 1) + center) / len(rows[-1])
        else:
            rows.append([box])
            centers.append(center)

    for row in rows:
        row.sort(key=lambda box: box.x0)
    return rows


def _find_table_row_runs(rows: list[list[TextBox]]) -> list[list[list[TextBox]]]:
    """寻找连续的表格型行组。"""
    runs: list[list[list[TextBox]]] = []
    current: list[list[TextBox]] = []
    skipped_noise_rows = 0

    for row in rows:
        if _table_like_row(row):
            current.append(row)
            skipped_noise_rows = 0
            continue
        if current and len(row) <= 2 and skipped_noise_rows < 1:
            skipped_noise_rows += 1
            continue
        if _valid_table_run(current):
            runs.append(current)
        current = []
        skipped_noise_rows = 0

    if _valid_table_run(current):
        runs.append(current)

    return runs


def _table_like_row(row: list[TextBox]) -> bool:
    """判断一行文本框是否像表格行。"""
    if len(row) < 3:
        return False
    texts = [box.text for box in row if box.text]
    numeric_cells = sum(1 for text in texts if _numeric_or_period_like(text))
    has_label = any(re.search(r"[\u4e00-\u9fffA-Za-z]", text) for text in texts)
    enough_columns = len(texts) >= 4
    return enough_columns and has_label and numeric_cells >= 2


def _valid_table_run(rows: list[list[TextBox]]) -> bool:
    """判断连续行组是否足够稳定，可以作为表格。"""
    if len(rows) < 3:
        return False
    column_counts = [len(row) for row in rows]
    dense_rows = sum(1 for count in column_counts if count >= 4)
    numeric_rows = sum(1 for row in rows if sum(1 for box in row if _numeric_or_period_like(box.text)) >= 2)
    return dense_rows >= 3 and numeric_rows / len(rows) >= 0.65


def _numeric_or_period_like(text: str) -> bool:
    """判断单元格是否像数字、年份或预测期。"""
    compact = text.replace(",", "").replace("%", "").replace("％", "").strip()
    if not compact:
        return False
    if compact in {"-", "—", "--", "－"}:
        return True
    if re.fullmatch(r"\(?[-+]?\d+(\.\d+)?\)?", compact):
        return True
    if re.fullmatch(r"\d{4}[AE]?", compact):
        return True
    return bool(re.fullmatch(r"\d{4}[A-Z]", compact))


def _table_run_overlaps_existing(run_boxes: list[TextBox], existing_bboxes: list[list[float]]) -> bool:
    """避免兜底表格和已有表格区域重复。"""
    if not run_boxes:
        return True
    bbox = _union_bbox(run_boxes)
    area = max(1.0, (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]))
    for existing in existing_bboxes:
        left = max(bbox[0], existing[0])
        top = max(bbox[1], existing[1])
        right = min(bbox[2], existing[2])
        bottom = min(bbox[3], existing[3])
        overlap = max(0.0, right - left) * max(0.0, bottom - top)
        if overlap / area >= 0.25:
            return True
    return False


def _nearby_table_caption(all_rows: list[list[TextBox]], run: list[list[TextBox]]) -> str:
    """为兜底表格寻找紧邻上方的标题行。"""
    if not run:
        return ""
    first = run[0]
    first_top = min(box.top for box in first)
    first_ids = {box.box_id for box in first}
    first_index = next(
        (index for index, row in enumerate(all_rows) if any(box.box_id in first_ids for box in row)),
        0,
    )
    for previous in reversed(all_rows[max(0, first_index - 2):first_index]):
        text = normalize_whitespace(" ".join(box.text for box in previous))
        if not text:
            continue
        distance = first_top - max(box.bottom for box in previous)
        if 0 <= distance <= 24 and (_caption_like(text) or "表" in text or "数据" in text):
            return text
    return ""


def _detect_repeated_margin_lines(
    boxes_by_page: dict[int, list[TextBox]],
    page_sizes: dict[int, tuple[float, float]],
) -> set[str]:
    """识别重复出现在页眉页脚区域的噪声文本。"""
    if len(boxes_by_page) < 3:
        return set()

    counts: Counter[str] = Counter()
    for page, boxes in boxes_by_page.items():
        _, page_height = page_sizes.get(page, (0, 0))
        if page_height <= 0:
            continue
        page_candidates = {
            box.text
            for box in boxes
            if box.text and (box.top <= page_height * 0.10 or box.bottom >= page_height * 0.90)
        }
        counts.update(page_candidates)

    threshold = max(2, int(len(boxes_by_page) * 0.35))
    return {
        text
        for text, count in counts.items()
        if count >= threshold and 3 <= len(text) <= 100
    }


def _caption_like(text: str) -> bool:
    """判断文本是否像表格或图表标题。"""
    compact = re.sub(r"\s+", "", text)
    return bool(
        re.match(r"^(表|图表|图|资料来源|数据来源|来源)[:：]?[0-9一二三四五六七八九十-]*", compact)
    )


def _page_number_like(text: str) -> bool:
    """判断文本是否像页码。"""
    compact = re.sub(r"\s+", "", text)
    return bool(
        re.match(r"^\d+[/／]\d+$", compact)
        or re.match(r"^第?\d+页共?\d*页?$", compact)
        or re.match(r"^-?\d+-$", compact)
    )


def _disclaimer_like(text: str) -> bool:
    """判断文本是否像页脚免责声明。"""
    compact = re.sub(r"\s+", "", text)
    return bool(
        re.search(r"请务必阅读.*免责", compact)
        or re.search(r"免责声明", compact)
        or re.search(r"本报告仅供", compact)
    )


def _tag_layouts(
    boxes_by_page: dict[int, list[TextBox]],
    page_sizes: dict[int, tuple[float, float]],
    tables_by_page: dict[int, list[StructuredTable]],
) -> dict[int, list[LayoutRegion]]:
    """给文本框标注版面类型，并生成表格/页眉页脚区域。"""
    repeated = _detect_repeated_margin_lines(boxes_by_page, page_sizes)
    layout_regions: dict[int, list[LayoutRegion]] = defaultdict(list)

    for page, boxes in boxes_by_page.items():
        page_width, page_height = page_sizes.get(page, (0.0, 0.0))
        font_sizes = [box.font_size for box in boxes if box.font_size > 0]
        median_font = median(font_sizes) if font_sizes else 0.0

        for table_index, table in enumerate(tables_by_page.get(page, []), start=1):
            if not table.bbox:
                continue
            region = LayoutRegion(
                region_id=f"p{page:03d}-table-{table_index:03d}",
                page=page,
                type="table",
                x0=table.bbox[0],
                top=table.bbox[1],
                x1=table.bbox[2],
                bottom=table.bbox[3],
                source="pdfplumber_table",
            )
            layout_regions[page].append(region)

        for box in boxes:
            if page_height > 0 and (box.bottom >= page_height * 0.82 or box.top <= page_height * 0.12):
                if _page_number_like(box.text) or _disclaimer_like(box.text):
                    box.layout_type = "footer" if box.bottom >= page_height * 0.5 else "header"
                    box.layoutno = f"{box.layout_type}-0"
                    continue

            if page_height > 0 and box.text in repeated:
                if box.top <= page_height * 0.15:
                    box.layout_type = "header"
                    box.layoutno = "header-0"
                    continue
                if box.bottom >= page_height * 0.85:
                    box.layout_type = "footer"
                    box.layoutno = "footer-0"
                    continue

            for table_index, table in enumerate(tables_by_page.get(page, []), start=1):
                if table.caption and normalize_whitespace(table.caption) == normalize_whitespace(box.text):
                    box.layout_type = "table caption"
                    box.layoutno = f"table-{table_index}-caption"
                    break
                if table.bbox and _overlap_ratio(box, table.bbox) >= 0.45:
                    box.layout_type = "table"
                    box.layoutno = f"table-{table_index}"
                    break
            if box.layout_type:
                continue

            if _caption_like(box.text):
                box.layout_type = "table caption"
                box.layoutno = "table-caption"
                continue

            is_large = median_font > 0 and box.font_size >= median_font * 1.18
            is_top = page_height > 0 and box.top <= page_height * 0.28
            is_short = len(box.text) <= 80
            if is_large and is_top and is_short:
                box.layout_type = "title"
                box.layoutno = "title-0"
                continue

            box.layout_type = "text"
            box.layoutno = "text-0"

        for box in boxes:
            if box.layout_type in {"header", "footer"}:
                layout_regions[page].append(
                    LayoutRegion(
                        region_id=f"{box.box_id}-{box.layout_type}",
                        page=page,
                        type=box.layout_type,
                        x0=box.x0,
                        top=box.top,
                        x1=box.x1,
                        bottom=box.bottom,
                        source="repeated_margin",
                    )
                )

        for region in layout_regions[page]:
            region.x0 = max(0.0, min(region.x0, page_width or region.x0))
            region.x1 = max(0.0, min(region.x1, page_width or region.x1))
            region.top = max(0.0, min(region.top, page_height or region.top))
            region.bottom = max(0.0, min(region.bottom, page_height or region.bottom))

    return layout_regions


def _assign_columns(boxes_by_page: dict[int, list[TextBox]], page_sizes: dict[int, tuple[float, float]]) -> None:
    """根据 x 坐标为正文文本框估计栏号。"""
    for page, boxes in boxes_by_page.items():
        page_width, _ = page_sizes.get(page, (0.0, 0.0))
        candidates = [
            box
            for box in boxes
            if box.layout_type in {"title", "text"} and box.x1 > box.x0 and box.bottom > box.top
        ]
        if page_width <= 0 or len(candidates) < 8:
            for box in boxes:
                box.col_id = 0
            continue

        x_positions = sorted(box.x0 for box in candidates)
        clusters = [x_positions[0]]
        for x in x_positions[1:]:
            if x - clusters[-1] > page_width * 0.22:
                clusters.append(x)
        if len(clusters) > 3:
            clusters = clusters[:3]

        for box in boxes:
            if len(clusters) == 1:
                box.col_id = 0
                continue
            nearest = min(range(len(clusters)), key=lambda idx: abs(box.x0 - clusters[idx]))
            box.col_id = nearest


def _attach_captions_to_tables(
    boxes_by_page: dict[int, list[TextBox]],
    tables_by_page: dict[int, list[StructuredTable]],
) -> None:
    """把附近的表格标题挂到最近的表格上。"""
    for page, tables in tables_by_page.items():
        captions = [box for box in boxes_by_page.get(page, []) if box.layout_type == "table caption"]
        for caption in captions:
            nearest: Optional[StructuredTable] = None
            nearest_distance = float("inf")
            for table in tables:
                if not table.bbox:
                    continue
                table_top = table.bbox[1]
                distance = abs(caption.bottom - table_top)
                x_overlap = not (caption.x1 < table.bbox[0] or caption.x0 > table.bbox[2])
                if x_overlap and distance < nearest_distance:
                    nearest = table
                    nearest_distance = distance
            if nearest and nearest_distance <= 80:
                nearest.caption = caption.text


def _build_sections(doc_id: str, boxes_by_page: dict[int, list[TextBox]]) -> dict[int, list[ParsedSection]]:
    """把非表格文本框按阅读顺序合并成 sections。"""
    sections_by_page: dict[int, list[ParsedSection]] = defaultdict(list)
    for page, boxes in boxes_by_page.items():
        section_boxes = [
            box
            for box in boxes
            if box.layout_type not in {"header", "footer", "table", "table caption"}
            and box.text
        ]
        section_boxes.sort(key=lambda box: (box.col_id, box.top, box.x0))

        current: list[TextBox] = []
        section_index = 1

        def flush() -> None:
            """把当前累积的文本框写成一个 section。"""
            nonlocal current, section_index
            if not current:
                return
            layout_type = current[0].layout_type or "text"
            text = normalize_whitespace("\n".join(box.text for box in current))
            if text:
                sections_by_page[page].append(
                    ParsedSection(
                        section_id=f"{doc_id}-p{page:03d}-s{section_index:03d}",
                        page=page,
                        text=text,
                        layout_type=layout_type,
                        layoutno=current[0].layoutno or layout_type,
                        col_id=current[0].col_id,
                        bbox=_union_bbox(current),
                        box_ids=[box.box_id for box in current],
                    )
                )
                section_index += 1
            current = []

        for box in section_boxes:
            if not current:
                current = [box]
                continue
            previous = current[-1]
            same_flow = (
                box.col_id == previous.col_id
                and box.layout_type == previous.layout_type
                and box.layoutno == previous.layoutno
                and box.top - previous.bottom <= max(18.0, previous.font_size * 2.2)
            )
            if same_flow:
                current.append(box)
            else:
                flush()
                current = [box]
        flush()
    return sections_by_page


def parse_pdf(record: DocumentRecord, project_root: Path) -> list[dict]:
    """解析单个 PDF，输出 page 级结构化记录。"""
    boxes_by_page, page_sizes = _extract_text_boxes(record.file_path, record.doc_id)
    tables_by_page = _extract_tables(record.file_path, record.doc_id, boxes_by_page)
    layout_regions = _tag_layouts(boxes_by_page, page_sizes, tables_by_page)
    _assign_columns(boxes_by_page, page_sizes)
    _attach_captions_to_tables(boxes_by_page, tables_by_page)
    sections_by_page = _build_sections(record.doc_id, boxes_by_page)

    rel_path = record.file_path
    if record.file_path.is_absolute():
        try:
            rel_path = record.file_path.relative_to(project_root)
        except ValueError:
            rel_path = record.file_path

    parsed_pages: list[dict] = []
    for page in sorted(boxes_by_page):
        sections = [asdict(section) for section in sections_by_page.get(page, [])]
        tables = [asdict(table) for table in tables_by_page.get(page, [])]
        text_boxes = [asdict(box) for box in boxes_by_page.get(page, [])]
        regions = [asdict(region) for region in layout_regions.get(page, [])]
        page_text = normalize_whitespace("\n".join(section["text"] for section in sections))
        parser_meta = {
            "name": "deepdoc_style_local",
            "ocr_stage": "pymupdf_text_boxes",
            "layout_stage": "heuristic_regions",
            "table_stage": "pdfplumber_tables",
            "text_box_count": len(text_boxes),
            "layout_region_count": len(regions),
            "table_count": len(tables),
            "has_real_ocr": False,
        }
        parsed_pages.append(
            asdict(
                ParsedPage(
                    doc_id=record.doc_id,
                    source=str(rel_path),
                    page=page,
                    text=page_text,
                    sections=sections,
                    tables=tables,
                    layout_regions=regions,
                    text_boxes=text_boxes,
                    metadata=record.metadata(),
                    parser=parser_meta,
                )
            )
        )
    return parsed_pages


def parse_documents(records: Iterable[DocumentRecord], project_root: Path) -> Iterable[dict]:
    """批量解析文档记录。"""
    for record in records:
        yield from parse_pdf(record, project_root)
