#!/usr/bin/env python
"""把评测集模板导出为 JSONL，并按 source 补全文档元数据。"""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


INDUSTRY_BY_DIR = {
    "new_energy": "new_energy",
    "semiconductor": "semiconductor",
    "consumer": "consumer",
    "healthcare": "healthcare",
    "real_estate": "real_estate",
    "policy": "policy",
}

INDUSTRY_BY_NAME = {
    "新能源": "new_energy",
    "半导体": "semiconductor",
    "消费": "consumer",
    "医疗": "healthcare",
    "房地产": "real_estate",
    "政策": "policy",
}


def find_project_root() -> Path:
    """从脚本位置向上查找项目根目录。"""
    for parent in Path(__file__).resolve().parents:
        if (parent / "src" / "financial_report_rag").exists():
            return parent
    raise RuntimeError("无法定位项目根目录")


ROOT = find_project_root()


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", default="data/eval/financial_qa_dev.template.json")
    parser.add_argument("--output", default="data/eval/financial_qa_dev.jsonl")
    parser.add_argument("--manifest", default="docs/data_collection/pdf_manifest.csv")
    parser.add_argument("--policy-theme-index", default="data/processed/metadata/policy_theme_index.csv")
    parser.add_argument("--keep-existing", action="store_true", help="已有 doc_id/industry 时不覆盖。")
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析成绝对路径。"""
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def normalize_source(source: str) -> str:
    """把 source 统一成项目相对 POSIX 路径。"""
    source = str(source or "").strip()
    if not source:
        return ""
    path = Path(source)
    if path.is_absolute():
        try:
            path = path.relative_to(ROOT)
        except ValueError:
            return path.as_posix()
    return path.as_posix().lstrip("./")


def normalize_industry(industry: str, source: str = "") -> str:
    """把中文行业名或 raw 子目录转换成评测集使用的英文标签。"""
    industry = str(industry or "").strip()
    if industry in INDUSTRY_BY_NAME:
        return INDUSTRY_BY_NAME[industry]
    if industry in INDUSTRY_BY_DIR.values():
        return industry

    source = normalize_source(source)
    parts = Path(source).parts
    if len(parts) >= 3 and parts[0] == "data" and parts[1] == "raw":
        return INDUSTRY_BY_DIR.get(parts[2], parts[2])
    return industry


def load_source_metadata(manifest_path: Path, policy_theme_index_path: Path) -> dict[str, dict[str, str]]:
    """读取各类清单，建立 source 到 doc_id/industry 的映射。"""
    source_map: dict[str, dict[str, str]] = {}

    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                source = normalize_source(row.get("file_path", ""))
                if not source:
                    continue
                source_map[source] = {
                    "doc_id": str(row.get("doc_id", "")).strip(),
                    "industry": normalize_industry(str(row.get("industry", "")).strip(), source),
                }

    if policy_theme_index_path.exists():
        with policy_theme_index_path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                source = normalize_source(row.get("source", ""))
                if not source:
                    continue
                source_map.setdefault(
                    source,
                    {
                        "doc_id": str(row.get("doc_id", "")).strip(),
                        "industry": normalize_industry("policy", source),
                    },
                )

    return source_map


def fallback_doc_id(source: str) -> str:
    """没有清单命中时，从文件名生成兜底 doc_id。"""
    stem = Path(normalize_source(source)).stem
    return stem.lower()


def load_template(path: Path) -> list[dict[str, Any]]:
    """读取 JSON 数组格式的评测模板。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"模板必须是 JSON 数组：{path}")
    return data


def enrich_sample(sample: dict[str, Any], source_map: dict[str, dict[str, str]], keep_existing: bool) -> tuple[dict[str, Any], list[str]]:
    """按 ground_truth.source 补齐单条样本的 doc_id 和 industry。"""
    item = deepcopy(sample)
    unresolved: list[str] = []
    industries: list[str] = []

    for evidence in item.get("ground_truth") or []:
        source = normalize_source(evidence.get("source", ""))
        if source:
            evidence["source"] = source

        meta = source_map.get(source, {}) if source else {}
        doc_id = meta.get("doc_id") or fallback_doc_id(source) if source else ""
        industry = meta.get("industry") or normalize_industry("", source)

        if source and not meta:
            unresolved.append(source)
        if doc_id and (not keep_existing or not evidence.get("doc_id")):
            evidence["doc_id"] = doc_id
        if industry:
            industries.append(industry)

    unique_industries = sorted(set(industries))
    if unique_industries:
        industry = unique_industries[0] if len(unique_industries) == 1 else "mixed"
        if not keep_existing or not item.get("industry"):
            item["industry"] = industry

    return item, unresolved


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    """写出 UTF-8 JSONL。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    """执行模板导出。"""
    args = parse_args()
    template_path = resolve_path(args.template)
    output_path = resolve_path(args.output)
    manifest_path = resolve_path(args.manifest)
    policy_theme_index_path = resolve_path(args.policy_theme_index)

    source_map = load_source_metadata(manifest_path, policy_theme_index_path)
    template_rows = load_template(template_path)

    rows: list[dict[str, Any]] = []
    unresolved_sources: set[str] = set()
    for sample in template_rows:
        row, unresolved = enrich_sample(sample, source_map, args.keep_existing)
        rows.append(row)
        unresolved_sources.update(unresolved)

    write_jsonl(rows, output_path)

    missing_doc_id = sum(
        1
        for row in rows
        for evidence in row.get("ground_truth", [])
        if evidence.get("source") and not evidence.get("doc_id")
    )
    missing_industry = sum(1 for row in rows if not row.get("industry"))

    print(f"template: {template_path.relative_to(ROOT)}")
    print(f"output: {output_path.relative_to(ROOT)}")
    print(f"samples: {len(rows)}")
    print(f"source_metadata: {len(source_map)}")
    print(f"missing_doc_id: {missing_doc_id}")
    print(f"missing_industry: {missing_industry}")
    if unresolved_sources:
        print("unresolved_sources:")
        for source in sorted(unresolved_sources):
            print(f"  - {source}")


if __name__ == "__main__":
    main()
