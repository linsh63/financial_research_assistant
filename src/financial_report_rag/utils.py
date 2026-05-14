"""RAG 流程中共用的 IO 和文本处理工具。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Iterator


def ensure_parent(path: Path) -> None:
    """确保目标文件所在目录存在。"""
    path.parent.mkdir(parents=True, exist_ok=True)


def read_jsonl(path: Path) -> Iterator[dict]:
    """逐行读取 JSONL 文件。"""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_jsonl(path: Path, rows: Iterable[dict]) -> int:
    """把字典序列写成 JSONL 文件。"""
    ensure_parent(path)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def normalize_whitespace(text: str) -> str:
    """规范化空白字符但保留段落换行。"""
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def stable_id(text: str) -> str:
    """把任意标题或文件名转成稳定的标识符。"""
    text = text.strip().lower()
    text = re.sub(r"\.[a-z0-9]+$", "", text)
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "document"


def preview(text: str, max_chars: int = 240) -> str:
    """生成适合命令行展示的短预览文本。"""
    text = normalize_whitespace(text).replace("\n", " ")
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
