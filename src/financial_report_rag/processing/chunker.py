"""DeepDoc 风格的正文分区切块和表格保护切块。"""

from __future__ import annotations

import re
from typing import Iterable

from ..parsing.table_structure import split_protected_table_rows
from ..utils import normalize_whitespace


BOUNDARY_RE = re.compile(r"[。！？；;]\s*|\n+")
UNFINISHED_TAILS = (
    "分别为",
    "主要为",
    "包括",
    "如下",
    "其中",
    "同比",
    "环比",
    "达到",
    "为",
)
UNFINISHED_CHARS = ("，", ",", "、", "/", "：", ":")


def _boundary_ends(text: str, start: int, end: int) -> list[int]:
    """找出指定区间内适合作为句子边界的结束位置。"""
    return [start + match.end() for match in BOUNDARY_RE.finditer(text[start:end])]


def _looks_unfinished(piece: str) -> bool:
    """判断 chunk 尾部是否明显像半句话。"""
    tail = piece.rstrip()
    if not tail:
        return False
    if tail.endswith(UNFINISHED_CHARS):
        return True
    compact_tail = re.sub(r"\s+", "", tail)
    return any(compact_tail.endswith(word) for word in UNFINISHED_TAILS)


def _choose_semantic_end(text: str, start: int, hard_end: int, chunk_size: int) -> int:
    """在固定窗口附近选择更自然的句子结束位置。"""
    if hard_end >= len(text):
        return len(text)

    min_piece_len = max(80, int(chunk_size * 0.5))
    min_end = min(hard_end, start + min_piece_len)
    candidates = _boundary_ends(text, min_end, hard_end)
    for end in reversed(candidates):
        if not _looks_unfinished(text[start:end]):
            return end
    if candidates:
        return candidates[-1]

    max_extension = min(240, max(80, chunk_size // 2))
    extended_end = min(len(text), hard_end + max_extension)
    for end in _boundary_ends(text, hard_end, extended_end):
        if not _looks_unfinished(text[start:end]):
            return end
    return hard_end


def _choose_next_start(text: str, current_start: int, current_end: int, overlap: int) -> int:
    """为下一个 chunk 选择不容易切半句话的起点。"""
    proposed = max(current_end - overlap, current_start + 1)
    if proposed >= current_end:
        return proposed
    candidates = _boundary_ends(text, proposed, current_end)
    if candidates:
        return max(candidates[-1], current_start + 1)
    return proposed


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """按固定窗口切分普通文本，并尽量保护中文句子边界。"""
    text = normalize_whitespace(text)
    if not text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须为正数")
    if overlap < 0:
        raise ValueError("overlap 不能为负数")
    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")

    chunks = []
    start = 0
    while start < len(text):
        hard_end = min(start + chunk_size, len(text))
        end = _choose_semantic_end(text, start, hard_end, chunk_size)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = _choose_next_start(text, start, end, overlap)
    return chunks


def _base_chunk(page: dict, chunk_id: str, text: str, chunk_type: str, has_table: bool) -> dict:
    """生成所有 chunk 共用的基础字段。"""
    return {
        "chunk_id": chunk_id,
        "doc_id": page["doc_id"],
        "source": page["source"],
        "pages": [page["page"]],
        "text": text,
        "chunk_type": chunk_type,
        "has_table": has_table,
        "metadata": page.get("metadata", {}),
    }


def _chunk_sections(page: dict, chunk_size: int, overlap: int) -> list[dict]:
    """优先基于版面 section 生成正文 chunk。"""
    chunks: list[dict] = []
    for section in page.get("sections", []):
        section_text = normalize_whitespace(section.get("text", ""))
        if not section_text:
            continue
        pieces = split_text(section_text, chunk_size, overlap)
        for piece_index, text in enumerate(pieces, start=1):
            section_id = section.get("section_id") or f"{page['doc_id']}-p{page['page']:03d}-s{len(chunks) + 1:03d}"
            chunk_id = f"{section_id}-c{piece_index:03d}"
            chunk = _base_chunk(page, chunk_id, text, section.get("layout_type") or "text", False)
            chunk["section"] = {
                "section_id": section_id,
                "layout_type": section.get("layout_type"),
                "layoutno": section.get("layoutno"),
                "col_id": section.get("col_id"),
                "bbox": section.get("bbox"),
                "box_ids": section.get("box_ids", []),
            }
            chunks.append(chunk)
    return chunks


def _chunk_page_text_fallback(page: dict, chunk_size: int, overlap: int) -> list[dict]:
    """当没有 section 时回退到整页文本切块。"""
    chunks: list[dict] = []
    for idx, text in enumerate(split_text(page.get("text", ""), chunk_size, overlap), start=1):
        chunk_id = f"{page['doc_id']}-p{page['page']:03d}-c{idx:03d}"
        chunks.append(_base_chunk(page, chunk_id, text, "text", False))
    return chunks


def _chunk_tables(page: dict, chunk_size: int) -> list[dict]:
    """按表格行边界生成 table chunk，避免切断单行。"""
    chunks: list[dict] = []
    for table_index, table in enumerate(page.get("tables", []), start=1):
        table_id = table.get("table_id") or f"{page['doc_id']}-p{page['page']:03d}-t{table_index:03d}"
        protected_parts = split_protected_table_rows(table, chunk_size)
        for part_index, part in enumerate(protected_parts, start=1):
            table_text = normalize_whitespace(part.get("text", ""))
            if not table_text:
                continue
            chunk_id = table_id if len(protected_parts) == 1 else f"{table_id}-part{part_index:03d}"
            chunk = _base_chunk(page, chunk_id, table_text, "table", True)
            chunk["table"] = {
                "table_id": table_id,
                "parent_table_id": table_id,
                "part_index": part_index,
                "part_count": len(protected_parts),
                "rows": table.get("rows"),
                "columns": table.get("columns"),
                "row_start": part.get("row_start"),
                "row_end": part.get("row_end"),
                "row_count": part.get("row_count"),
                "bbox": table.get("bbox"),
                "caption": table.get("caption", ""),
                "html": table.get("html", ""),
                "source": table.get("source", ""),
                "cells": table.get("cells", []),
                "protected_rows": table.get("protected_rows", []),
                "table_protection": "row_boundary",
            }
            chunks.append(chunk)
    return chunks


def chunk_page(page: dict, chunk_size: int, overlap: int) -> list[dict]:
    """把一个页面转换为正文 chunk 和表格 chunk。"""
    chunks = _chunk_sections(page, chunk_size, overlap)
    if not chunks:
        chunks = _chunk_page_text_fallback(page, chunk_size, overlap)
    chunks.extend(_chunk_tables(page, chunk_size))
    return chunks


def chunk_pages(pages: Iterable[dict], chunk_size: int, overlap: int) -> Iterable[dict]:
    """批量把页面流转换为 chunk 流。"""
    for page in pages:
        yield from chunk_page(page, chunk_size, overlap)
