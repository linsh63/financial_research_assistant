#!/usr/bin/env python
"""单文件修复 SNJT.pdf 的坏文本层。

这个脚本只替换 doc_id=snjt 的 page/chunk 记录。写入前后会校验所有非 SNJT
记录的哈希，避免影响其他 PDF。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Iterable


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

from financial_report_rag.parsing.table_structure import construct_table_from_rows  # noqa: E402
from financial_report_rag.processing.chunker import chunk_pages  # noqa: E402
from financial_report_rag.utils import read_jsonl, write_jsonl  # noqa: E402


DOC_ID = "snjt"
SOURCE = "data/raw/consumer/SNJT.pdf"
METADATA = {
    "title": "神农集团（605296）2026年一季报点评：养殖成本领先，周期有望获益",
    "industry": "消费",
    "doc_type": "report",
    "year_month": "2026-05",
    "source_url": "",
    "expected_pages": 5,
    "file_size_bytes": 1698534,
    "notes": "SNJT.pdf 文本层异常，已按单文件可视化核对结果修复 page/chunk 文本。",
}


PAGE1_SECTIONS = [
    (
        "header",
        "神农集团（605296）\n"
        "2026年05月08日\n"
        "证券研究报告/公司研究/公司点评\n"
        "养殖成本领先，周期有望获益\n"
        "投资评级：买入，维持评级",
    ),
    (
        "q1_pressure",
        "26Q1 经营短期承压\n"
        "2025年全年，公司实现营业收入53.52亿元，归母净利润3.39亿元，经营稳健。"
        "进入2026年一季度，受生猪市场价格持续低迷影响，公司业绩短期承压。"
        "公司实现营业收入13.22亿元，同比下降10.20%；实现归母净利润-6.48亿元，"
        "去年同期为盈利2.29亿元；扣非归母净利润为-6.53亿元，同比下降。"
        "亏损受到多重因素影响，一是猪价下跌、经营承压，经营活动产生的现金流量净额转负，"
        "为-1.27亿元；二是公司计提了高达4.8亿元的资产减值损失，主要为消耗性生物资产跌价准备。",
    ),
    (
        "cost",
        "公司养殖管理优秀，养殖成本领先\n"
        "公司将成本管控作为全年经营核心工作，全方位、全流程推进精细化成本管理，"
        "从种猪育种、饲料供应、饲养管理、智能化升级、费用管控五大维度发力，"
        "持续压缩生猪养殖完全成本。25年公司养殖完全成本12.3元/公斤。"
        "26年公司全年平均完全成本目标为11.5元/公斤。该目标锚定为锁价2025年饲料原料成本，"
        "要求团队通过内部管理提效、满负荷生产、优化料肉比、压降各项费用等方式实现。"
        "生产指标方面，目标PSY将由去年29.5提升至今年目标31；料肉比从当前2.49向2.4稳步靠拢。",
    ),
    (
        "cycle",
        "周期有望获益\n"
        "猪价仍将面临一定压力，产能去化趋势不改。据Mysteel生猪养殖样本企业数据，"
        "国内能繁母猪存栏量自24年以来趋势增加，25年8月才起止涨转降。"
        "考虑前期产能水平和养殖效率提升，26年前期行业生猪供给水平仍较高，进入淡季后，"
        "猪价面临压力。从历史生猪周期产能去化幅度看，当前行业产能去化幅度较低、速度偏缓。"
        "随着未来猪价行情压力，行业产能去化趋势望延续。行业产能去化过程中，"
        "也是生猪板块远期预期抬升过程，以神农集团为代表的优质养殖集团有望充分受益。",
    ),
]

PAGE2_SECTIONS = [
    (
        "investment",
        "投资建议\n"
        "神农集团是一家集饲料生产、生猪养殖、屠宰加工、食品深加工为一体的农业产业化国家重点龙头企业。"
        "公司养殖成绩优秀，有望在周期中充分获益。我们预计公司2026-2028年归母净利润分别为"
        "1.3亿元、7.3亿元、12.6亿元，EPS分别为0.26元、1.40元、2.41元，维持“买入”评级。",
    ),
    (
        "risk",
        "风险提示：生猪价格波动风险；生猪养殖行业疫病风险；自然灾害和极端天气风险；"
        "产业政策变化风险；宏观经济波动风险。",
    ),
]

PAGE2_TABLE_ROWS = [
    ["财务数据与估值", "2024A", "2025A", "2026E", "2027E", "2028E"],
    ["营业收入（百万元）", "5584.34", "5351.81", "5585.43", "6384.18", "7293.64"],
    ["增长率（%）", "43.51", "-4.16", "4.37", "14.30", "14.25"],
    ["归母净利润（百万元）", "686.82", "338.96", "134.75", "733.46", "1263.35"],
    ["增长率（%）", "271.16", "-50.65", "-60.25", "444.32", "72.25"],
    ["毛利率（%）", "20.78", "16.29", "12.84", "22.49", "27.82"],
    ["每股收益", "1.31", "0.65", "0.26", "1.40", "2.41"],
    ["市盈率 PE", "22.55", "45.69", "114.93", "21.11", "12.26"],
    ["市净率 PB", "3.20", "3.15", "3.09", "2.77", "2.36"],
    ["净资产收益率 ROE（%）", "14.21", "6.90", "2.69", "13.14", "19.26"],
]


def parse_args() -> argparse.Namespace:
    """读取修复脚本参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", default="data/processed/pages/pages_deepdoc.jsonl")
    parser.add_argument("--chunks", default="data/processed/chunks/chunks_boundary.jsonl")
    parser.add_argument("--chunk-size", type=int, default=512)
    parser.add_argument("--overlap", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析为绝对路径。"""
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def stable_json(row: dict) -> str:
    """生成稳定 JSON 字符串用于哈希校验。"""
    return json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def non_doc_digest(rows: Iterable[dict], doc_id: str) -> str:
    """计算非目标文档记录的稳定哈希。"""
    hasher = hashlib.sha256()
    for row in rows:
        if row.get("doc_id") == doc_id:
            continue
        hasher.update(stable_json(row).encode("utf-8"))
        hasher.update(b"\n")
    return hasher.hexdigest()


def section(page: int, name: str, text: str, index: int) -> dict:
    """生成一个人工校正 section。"""
    return {
        "section_id": f"{DOC_ID}-p{page:03d}-manual-{index:03d}-{name}",
        "page": page,
        "text": text,
        "layout_type": "text",
        "layoutno": f"manual-{name}",
        "col_id": 0,
        "bbox": None,
        "box_ids": [],
    }


def page_record(page: int, sections: list[dict], tables: list[dict] | None = None) -> dict:
    """生成一个 SNJT 页面记录。"""
    tables = tables or []
    text_parts = [item["text"] for item in sections]
    text_parts.extend(table.get("text", "") for table in tables)
    return {
        "doc_id": DOC_ID,
        "source": SOURCE,
        "page": page,
        "text": "\n\n".join(part for part in text_parts if part).strip(),
        "sections": sections,
        "tables": tables,
        "layout_regions": [],
        "text_boxes": [],
        "metadata": METADATA,
        "parser": {
            "name": "manual_snjt_single_pdf_repair",
            "ocr_stage": "manual_visual_transcription",
            "layout_stage": "manual_sections",
            "table_stage": "manual_table_rows",
            "text_box_count": 0,
            "layout_region_count": len(sections),
            "table_count": len(tables),
            "has_real_ocr": False,
        },
    }


def build_pages() -> list[dict]:
    """构造 SNJT 的人工校正页面记录。"""
    page1_sections = [section(1, name, text, idx) for idx, (name, text) in enumerate(PAGE1_SECTIONS, start=1)]
    page2_sections = [section(2, name, text, idx) for idx, (name, text) in enumerate(PAGE2_SECTIONS, start=1)]
    table = construct_table_from_rows(
        table_id=f"{DOC_ID}-p002-manual-table-financial",
        page=2,
        rows=PAGE2_TABLE_ROWS,
        caption="财务数据与估值，资料来源：iFind，中航证券研究所",
    ).to_dict()
    pages = [
        page_record(1, page1_sections),
        page_record(2, page2_sections, [table]),
    ]
    for page in range(3, 6):
        pages.append(page_record(page, []))
    return pages


def replace_doc_records(path: Path, doc_id: str, new_records: list[dict], dry_run: bool) -> tuple[int, int]:
    """只替换指定 doc_id 的记录，并校验其他记录不变。"""
    rows = list(read_jsonl(path))
    before_digest = non_doc_digest(rows, doc_id)
    old_count = 0
    inserted = False
    output = []
    for row in rows:
        if row.get("doc_id") == doc_id:
            old_count += 1
            if not inserted:
                output.extend(new_records)
                inserted = True
            continue
        output.append(row)
    if not inserted:
        output.extend(new_records)
    after_digest = non_doc_digest(output, doc_id)
    if before_digest != after_digest:
        raise RuntimeError(f"非 {doc_id} 记录发生变化，已中止写入：{path}")
    if not dry_run:
        write_jsonl(path, output)
    return old_count, len(new_records)


def main() -> None:
    """执行 SNJT 单文件页面和 chunk 修复。"""
    args = parse_args()
    pages_path = resolve_path(args.pages)
    chunks_path = resolve_path(args.chunks)
    pages = build_pages()
    chunks = list(chunk_pages(pages, chunk_size=args.chunk_size, overlap=args.overlap))

    page_old, page_new = replace_doc_records(pages_path, DOC_ID, pages, args.dry_run)
    chunk_old, chunk_new = replace_doc_records(chunks_path, DOC_ID, chunks, args.dry_run)

    action = "dry-run" if args.dry_run else "written"
    print(f"{action}: pages {page_old} -> {page_new}")
    print(f"{action}: chunks {chunk_old} -> {chunk_new}")
    print("non_snjt_records: unchanged")


if __name__ == "__main__":
    main()
