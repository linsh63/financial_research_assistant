"""数据清单读取和 PDF 自动发现逻辑。"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional

from ..utils import stable_id


@dataclass
class DocumentRecord:
    doc_id: str
    file_path: Path
    title: str = ""
    industry: str = ""
    doc_type: str = ""
    year_month: str = ""
    source_url: str = ""
    expected_pages: Optional[int] = None
    file_size_bytes: Optional[int] = None
    notes: str = ""
    extra: dict = field(default_factory=dict)

    def metadata(self) -> dict:
        """生成写入 page/chunk 的文档元数据。"""
        return {
            "title": self.title,
            "industry": self.industry,
            "doc_type": self.doc_type,
            "year_month": self.year_month,
            "source_url": self.source_url,
            "expected_pages": self.expected_pages,
            "file_size_bytes": self.file_size_bytes,
            "notes": self.notes,
        }


def _to_int(value: Optional[str]) -> Optional[int]:
    """把清单中的数字字段安全转换为整数。"""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def load_manifest(manifest_path: Path, project_root: Path) -> List[DocumentRecord]:
    """从 CSV 清单加载文档记录。"""
    records: List[DocumentRecord] = []
    if not manifest_path.exists():
        return records

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_path = row.get("file_path", "").strip()
            if not raw_path:
                continue
            file_path = Path(raw_path)
            if not file_path.is_absolute():
                file_path = project_root / file_path

            doc_id = row.get("doc_id", "").strip() or stable_id(file_path.stem)
            records.append(
                DocumentRecord(
                    doc_id=doc_id,
                    file_path=file_path,
                    title=row.get("title", "").strip(),
                    industry=row.get("industry", "").strip(),
                    doc_type=row.get("doc_type", "").strip(),
                    year_month=row.get("year_month", "").strip(),
                    source_url=row.get("source_url", "").strip(),
                    expected_pages=_to_int(row.get("pages")),
                    file_size_bytes=_to_int(row.get("file_size_bytes")),
                    notes=row.get("notes", "").strip(),
                    extra=dict(row),
                )
            )
    return records


def discover_pdfs(raw_dir: Path, project_root: Path) -> List[DocumentRecord]:
    """扫描 raw 目录，发现尚未登记的 PDF。"""
    records: List[DocumentRecord] = []
    for path in sorted(raw_dir.rglob("*.pdf")):
        rel = path.relative_to(project_root) if path.is_absolute() else path
        parts = path.relative_to(raw_dir).parts
        industry = parts[0] if len(parts) > 1 else ""
        records.append(
            DocumentRecord(
                doc_id=stable_id(path.stem),
                file_path=path,
                title=path.stem,
                industry=industry,
                doc_type="pdf",
                file_size_bytes=path.stat().st_size,
                extra={"file_path": str(rel)},
            )
        )
    return records


def load_documents(
    manifest_path: Path,
    raw_dir: Path,
    project_root: Path,
    include_unlisted: bool = True,
) -> List[DocumentRecord]:
    """合并清单记录和可选的未登记 PDF。"""
    records = load_manifest(manifest_path, project_root)
    seen = {record.file_path.resolve() for record in records}

    if include_unlisted:
        for record in discover_pdfs(raw_dir, project_root):
            if record.file_path.resolve() not in seen:
                records.append(record)

    return [record for record in records if record.file_path.exists()]


def missing_documents(records: Iterable[DocumentRecord]) -> List[DocumentRecord]:
    """返回路径不存在的文档记录。"""
    return [record for record in records if not record.file_path.exists()]
