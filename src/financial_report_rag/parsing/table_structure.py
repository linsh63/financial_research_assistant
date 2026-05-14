"""借鉴 DeepDoc 思路的表格结构重建。

RAGFlow DeepDoc 会把表格版面组件和 OCR 文本框结合起来，重建行、列、表头、
跨行跨列、HTML 和行级描述。本模块用本地 PDF 工具实现同样的数据形态：

* pdfplumber 提供表格、行、列、单元格的几何信息；
* PyMuPDF 文本框尽量回填到对应单元格；
* 表格行被序列化成保护单元，保证切块时不会切断一行。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from html import escape
from typing import Any, Iterable, Optional

from ..utils import normalize_whitespace


@dataclass
class TableCell:
    row: int
    col: int
    text: str
    bbox: Optional[list[float]]
    is_header: bool
    row_span: int = 1
    col_span: int = 1
    text_box_ids: list[str] = field(default_factory=list)


@dataclass
class ProtectedTableRow:
    row: int
    text: str
    is_header: bool
    cell_count: int
    cell_ids: list[str] = field(default_factory=list)


@dataclass
class StructuredTable:
    table_id: str
    page: int
    text: str
    rows: int
    columns: int
    bbox: Optional[list[float]]
    caption: str = ""
    html: str = ""
    source: str = "pdfplumber_structured"
    cells: list[dict] = field(default_factory=list)
    protected_rows: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """把结构化表格转换成普通字典。"""
        return asdict(self)


def construct_table(
    table_id: str,
    page: int,
    table_obj: Any,
    text_boxes: Iterable[Any],
    caption: str = "",
) -> StructuredTable:
    """基于 pdfplumber 几何信息和文本框重建结构化表格。"""

    raw_rows = table_obj.extract() or []
    rows = _normalize_matrix(raw_rows)
    row_count = len(rows)
    column_count = max((len(row) for row in rows), default=0)
    bbox = _round_bbox(getattr(table_obj, "bbox", None))

    row_bboxes = [_round_bbox(getattr(row, "bbox", None)) for row in getattr(table_obj, "rows", []) or []]
    column_bboxes = [_round_bbox(getattr(col, "bbox", None)) for col in getattr(table_obj, "columns", []) or []]
    cell_grid = _cell_grid(table_obj, row_count, column_count)
    header_rows = _infer_header_rows(rows)

    cells: list[TableCell] = []
    seen_spans: set[tuple[int, int, int, int]] = set()
    text_box_list = list(text_boxes)

    for row_index in range(row_count):
        for col_index in range(column_count):
            cell_bbox = _cell_bbox(cell_grid, row_index, col_index)
            if cell_bbox is None:
                continue

            row_span, col_span = _span_for_bbox(cell_bbox, row_bboxes, column_bboxes)
            span_key = (row_index, col_index, row_span, col_span)
            if span_key in seen_spans:
                continue
            seen_spans.add(span_key)

            text = rows[row_index][col_index] if col_index < len(rows[row_index]) else ""
            mapped_boxes = _boxes_in_bbox(text_box_list, cell_bbox)
            if not text:
                text = normalize_whitespace(" ".join(_box_text(box) for box in mapped_boxes))

            cells.append(
                TableCell(
                    row=row_index,
                    col=col_index,
                    text=text,
                    bbox=cell_bbox,
                    is_header=row_index in header_rows,
                    row_span=row_span,
                    col_span=col_span,
                    text_box_ids=[_box_id(box) for box in mapped_boxes if _box_id(box)],
                )
            )

    protected_rows = _protected_rows(cells, rows, header_rows, caption)
    html = _to_html(cells, row_count, column_count, header_rows, caption)
    text = _to_markdown(rows, caption)
    if protected_rows:
        descriptions = "\n".join(row.text for row in protected_rows if row.text)
        if descriptions:
            text = normalize_whitespace(text + "\n\n行级描述:\n" + descriptions)

    return StructuredTable(
        table_id=table_id,
        page=page,
        text=text,
        rows=row_count,
        columns=column_count,
        bbox=bbox,
        caption=caption,
        html=html,
        cells=[asdict(cell) for cell in cells],
        protected_rows=[asdict(row) for row in protected_rows],
    )


def construct_table_from_rows(
    table_id: str,
    page: int,
    rows: list[list[Any]],
    caption: str = "",
) -> StructuredTable:
    """在缺少几何信息时，用纯二维表格内容构造结构化表格。"""

    matrix = _normalize_matrix(rows)
    header_rows = _infer_header_rows(matrix)
    cells = []
    for row_index, row in enumerate(matrix):
        for col_index, text in enumerate(row):
            cells.append(
                TableCell(
                    row=row_index,
                    col=col_index,
                    text=text,
                    bbox=None,
                    is_header=row_index in header_rows,
                )
            )
    protected_rows = _protected_rows(cells, matrix, header_rows, caption)
    return StructuredTable(
        table_id=table_id,
        page=page,
        text=_to_markdown(matrix, caption),
        rows=len(matrix),
        columns=max((len(row) for row in matrix), default=0),
        bbox=None,
        caption=caption,
        html=_to_html(cells, len(matrix), max((len(row) for row in matrix), default=0), header_rows, caption),
        cells=[asdict(cell) for cell in cells],
        protected_rows=[asdict(row) for row in protected_rows],
    )


def construct_table_from_text_boxes(
    table_id: str,
    page: int,
    row_boxes: list[list[Any]],
    caption: str = "",
) -> StructuredTable:
    """用已经按行聚合的文本框构造结构化表格。"""
    matrix = [[_box_text(box) for box in row] for row in row_boxes]
    matrix = _normalize_matrix(matrix)
    header_rows = _infer_header_rows(matrix)
    cells: list[TableCell] = []
    all_boxes = []

    for row_index, boxes in enumerate(row_boxes):
        boxes = sorted(boxes, key=lambda box: _box_float(box, "x0"))
        all_boxes.extend(boxes)
        for col_index, box in enumerate(boxes):
            cells.append(
                TableCell(
                    row=row_index,
                    col=col_index,
                    text=_box_text(box),
                    bbox=_round_bbox(
                        [
                            _box_float(box, "x0"),
                            _box_float(box, "top"),
                            _box_float(box, "x1"),
                            _box_float(box, "bottom"),
                        ]
                    ),
                    is_header=row_index in header_rows,
                    text_box_ids=[_box_id(box)] if _box_id(box) else [],
                )
            )

    protected_rows = _protected_rows(cells, matrix, header_rows, caption)
    row_count = len(matrix)
    column_count = max((len(row) for row in matrix), default=0)
    bbox = _union_box_bbox(all_boxes)
    text = _to_markdown(matrix, caption)
    if protected_rows:
        descriptions = "\n".join(row.text for row in protected_rows if row.text)
        if descriptions:
            text = normalize_whitespace(text + "\n\n行级描述:\n" + descriptions)

    return StructuredTable(
        table_id=table_id,
        page=page,
        text=text,
        rows=row_count,
        columns=column_count,
        bbox=bbox,
        caption=caption,
        html=_to_html(cells, row_count, column_count, header_rows, caption),
        source="pymupdf_layout_table",
        cells=[asdict(cell) for cell in cells],
        protected_rows=[asdict(row) for row in protected_rows],
    )


def split_protected_table_rows(table: dict, chunk_size: int) -> list[dict]:
    """只在行边界切分表格，避免切断表格行。"""

    protected_rows = table.get("protected_rows") or []
    if not protected_rows:
        text = normalize_whitespace(table.get("text", ""))
        return [{"text": text, "row_start": None, "row_end": None, "row_count": table.get("rows", 0)}] if text else []

    caption = normalize_whitespace(table.get("caption", ""))
    header_rows = [row for row in protected_rows if row.get("is_header")]
    data_rows = [row for row in protected_rows if not row.get("is_header")]
    header_text = "\n".join(row.get("text", "") for row in header_rows if row.get("text"))

    prefix_parts = []
    if caption:
        prefix_parts.append(caption)
    if header_text:
        prefix_parts.append(header_text)
    prefix = "\n".join(prefix_parts)

    if not data_rows:
        header_indices = [int(row.get("row", -1)) for row in header_rows]
        header_indices = [row for row in header_indices if row >= 0]
        return [
            {
                "text": prefix,
                "row_start": min(header_indices) if header_indices else None,
                "row_end": max(header_indices) if header_indices else None,
                "row_count": len(header_indices),
            }
        ] if prefix else []

    chunks: list[dict] = []
    current_lines = [prefix] if prefix else []
    current_rows: list[int] = []

    def flush() -> None:
        """把当前积累的表格行写成一个受保护片段。"""
        nonlocal current_lines, current_rows
        text = normalize_whitespace("\n".join(line for line in current_lines if line))
        if text:
            chunks.append(
                {
                    "text": text,
                    "row_start": min(current_rows) if current_rows else None,
                    "row_end": max(current_rows) if current_rows else None,
                    "row_count": len(current_rows),
                }
            )
        current_lines = [prefix] if prefix else []
        current_rows = []

    for row in data_rows:
        row_text = normalize_whitespace(row.get("text", ""))
        if not row_text:
            continue
        candidate = normalize_whitespace("\n".join(current_lines + [row_text]))
        if current_rows and len(candidate) > chunk_size:
            flush()
        current_lines.append(row_text)
        current_rows.append(int(row.get("row", -1)))

    flush()

    if not chunks and prefix:
        header_indices = [int(row.get("row", -1)) for row in header_rows]
        header_indices = [row for row in header_indices if row >= 0]
        chunks.append(
            {
                "text": prefix,
                "row_start": min(header_indices) if header_indices else None,
                "row_end": max(header_indices) if header_indices else None,
                "row_count": len(header_indices),
            }
        )
    return chunks


def _normalize_matrix(rows: list[list[Any]]) -> list[list[str]]:
    """把原始表格行清洗成等宽字符串矩阵。"""
    matrix: list[list[str]] = []
    max_cols = max((len(row) for row in rows), default=0)
    for row in rows:
        cells = [normalize_whitespace(str(cell or "")) for cell in row]
        cells += [""] * (max_cols - len(cells))
        if any(cells):
            matrix.append(cells)
    return matrix


def _round_bbox(bbox: Optional[Iterable[float]]) -> Optional[list[float]]:
    """把边界框坐标统一保留两位小数。"""
    if not bbox:
        return None
    values = list(bbox)
    if len(values) != 4:
        return None
    return [round(float(value), 2) for value in values]


def _cell_grid(table_obj: Any, row_count: int, column_count: int) -> list[list[Optional[list[float]]]]:
    """从 pdfplumber Table 中提取单元格坐标网格。"""
    rows = getattr(table_obj, "rows", []) or []
    grid: list[list[Optional[list[float]]]] = []
    for row_index in range(row_count):
        row_cells = getattr(rows[row_index], "cells", []) if row_index < len(rows) else []
        grid.append([])
        for col_index in range(column_count):
            bbox = row_cells[col_index] if col_index < len(row_cells) else None
            grid[row_index].append(_round_bbox(bbox))
    return grid


def _cell_bbox(cell_grid: list[list[Optional[list[float]]]], row: int, col: int) -> Optional[list[float]]:
    """安全读取指定单元格的坐标。"""
    if row >= len(cell_grid) or col >= len(cell_grid[row]):
        return None
    return cell_grid[row][col]


def _span_for_bbox(
    bbox: list[float],
    row_bboxes: list[Optional[list[float]]],
    column_bboxes: list[Optional[list[float]]],
) -> tuple[int, int]:
    """根据单元格覆盖的行列中心点估算 rowspan/colspan。"""
    row_span = 1
    col_span = 1
    if row_bboxes:
        row_span = max(1, sum(1 for row_bbox in row_bboxes if row_bbox and _center_inside(row_bbox[1], row_bbox[3], bbox[1], bbox[3])))
    if column_bboxes:
        col_span = max(1, sum(1 for col_bbox in column_bboxes if col_bbox and _center_inside(col_bbox[0], col_bbox[2], bbox[0], bbox[2])))
    return row_span, col_span


def _center_inside(inner_start: float, inner_end: float, outer_start: float, outer_end: float) -> bool:
    """判断一个区间中心点是否落入另一个区间。"""
    center = (inner_start + inner_end) / 2
    return outer_start - 1 <= center <= outer_end + 1


def _boxes_in_bbox(boxes: list[Any], bbox: list[float]) -> list[Any]:
    """找出主要落在指定单元格内的文本框。"""
    matched = []
    for box in boxes:
        box_bbox = [_box_float(box, "x0"), _box_float(box, "top"), _box_float(box, "x1"), _box_float(box, "bottom")]
        area = max(0.0, box_bbox[2] - box_bbox[0]) * max(0.0, box_bbox[3] - box_bbox[1])
        if area <= 0:
            continue
        left = max(box_bbox[0], bbox[0])
        top = max(box_bbox[1], bbox[1])
        right = min(box_bbox[2], bbox[2])
        bottom = min(box_bbox[3], bbox[3])
        overlap = max(0.0, right - left) * max(0.0, bottom - top)
        if overlap / area >= 0.45:
            matched.append(box)
    matched.sort(key=lambda box: (_box_float(box, "top"), _box_float(box, "x0")))
    return matched


def _box_float(box: Any, key: str) -> float:
    """从对象或字典中读取浮点坐标。"""
    if isinstance(box, dict):
        return float(box.get(key, 0.0))
    return float(getattr(box, key, 0.0))


def _box_text(box: Any) -> str:
    """从对象或字典中读取文本内容。"""
    if isinstance(box, dict):
        return normalize_whitespace(str(box.get("text", "")))
    return normalize_whitespace(str(getattr(box, "text", "")))


def _box_id(box: Any) -> str:
    """从对象或字典中读取文本框 ID。"""
    if isinstance(box, dict):
        return str(box.get("box_id", ""))
    return str(getattr(box, "box_id", ""))


def _union_box_bbox(boxes: list[Any]) -> Optional[list[float]]:
    """合并一组文本框的 bbox。"""
    if not boxes:
        return None
    return _round_bbox(
        [
            min(_box_float(box, "x0") for box in boxes),
            min(_box_float(box, "top") for box in boxes),
            max(_box_float(box, "x1") for box in boxes),
            max(_box_float(box, "bottom") for box in boxes),
        ]
    )


def _infer_header_rows(rows: list[list[str]]) -> set[int]:
    """根据前几行的非数字比例推断表头行。"""
    if not rows:
        return set()
    header_rows = {0}
    for row_index, row in enumerate(rows[:2]):
        filled = [cell for cell in row if cell]
        if not filled:
            continue
        non_numeric = [cell for cell in filled if not _numeric_like(cell)]
        if len(non_numeric) / len(filled) >= 0.6:
            header_rows.add(row_index)
    return header_rows


def _numeric_like(text: str) -> bool:
    """粗略判断文本是否主要是数字。"""
    compact = text.replace(",", "").replace("%", "").replace("％", "").strip()
    if not compact:
        return False
    numeric_chars = sum(1 for char in compact if char.isdigit() or char in ".-+()/")
    return numeric_chars / len(compact) >= 0.65


def _protected_rows(cells: list[TableCell], rows: list[list[str]], header_rows: set[int], caption: str) -> list[ProtectedTableRow]:
    """把表格按行转成后续切块要保护的文本单元。"""
    by_row: dict[int, list[TableCell]] = {}
    for cell in cells:
        by_row.setdefault(cell.row, []).append(cell)

    headers = _column_headers(cells, rows, header_rows)
    protected = []
    for row_index in range(len(rows)):
        row_cells = sorted(by_row.get(row_index, []), key=lambda cell: cell.col)
        if not row_cells:
            continue
        if row_index in header_rows:
            text = " | ".join(cell.text for cell in row_cells if cell.text)
        else:
            parts = []
            for cell in row_cells:
                if not cell.text:
                    continue
                header = headers.get(cell.col, "")
                parts.append(f"{header}: {cell.text}" if header else cell.text)
            text = "; ".join(parts)
            if caption and text:
                text = f"{text}\t-- 来自「{caption}」"
        protected.append(
            ProtectedTableRow(
                row=row_index,
                text=normalize_whitespace(text),
                is_header=row_index in header_rows,
                cell_count=len(row_cells),
                cell_ids=[f"r{cell.row}c{cell.col}" for cell in row_cells],
            )
        )
    return protected


def _column_headers(cells: list[TableCell], rows: list[list[str]], header_rows: set[int]) -> dict[int, str]:
    """为每一列生成用于行级描述的表头文本。"""
    headers: dict[int, list[str]] = {}
    for cell in cells:
        if cell.row not in header_rows or not cell.text:
            continue
        headers.setdefault(cell.col, []).append(cell.text)
    if not headers and rows:
        headers = {idx: [text] for idx, text in enumerate(rows[0]) if text}
    return {col: "的".join(parts) for col, parts in headers.items() if any(parts)}


def _to_html(cells: list[TableCell], row_count: int, column_count: int, header_rows: set[int], caption: str) -> str:
    """把 cell 结构序列化为 HTML table。"""
    by_pos = {(cell.row, cell.col): cell for cell in cells}
    html = ["<table>"]
    if caption:
        html.append(f"<caption>{escape(caption)}</caption>")
    for row in range(row_count):
        html.append("<tr>")
        for col in range(column_count):
            cell = by_pos.get((row, col))
            if cell is None:
                continue
            tag = "th" if row in header_rows else "td"
            spans = []
            if cell.col_span > 1:
                spans.append(f'colspan="{cell.col_span}"')
            if cell.row_span > 1:
                spans.append(f'rowspan="{cell.row_span}"')
            span_text = " " + " ".join(spans) if spans else ""
            html.append(f"<{tag}{span_text}>{escape(cell.text)}</{tag}>")
        html.append("</tr>")
    html.append("</table>")
    return "\n".join(html)


def _to_markdown(rows: list[list[str]], caption: str) -> str:
    """把表格矩阵序列化为 Markdown 文本。"""
    if not rows:
        return ""
    max_cols = max((len(row) for row in rows), default=0)
    normalized = [row + [""] * (max_cols - len(row)) for row in rows]
    lines = []
    if caption:
        lines.append(caption)
    lines.append("| " + " | ".join(normalized[0]) + " |")
    lines.append("| " + " | ".join(["---"] * max_cols) + " |")
    for row in normalized[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)
