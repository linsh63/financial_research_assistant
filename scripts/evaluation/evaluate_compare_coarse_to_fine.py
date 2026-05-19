#!/usr/bin/env python
"""评估 compare 题的“先定位文档，再定位页码”粗到细检索策略。"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import evaluate_retrieval as eval_base


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

from financial_report_rag.retrieval.bm25_store import BM25Store  # noqa: E402
from financial_report_rag.retrieval.compare_rewriter import load_compare_rewrites  # noqa: E402
from financial_report_rag.retrieval.parent_document import ParentDocumentStore, expand_results_to_parents  # noqa: E402
from financial_report_rag.retrieval.routed_retriever import extract_compare_entities  # noqa: E402
from financial_report_rag.retrieval.vector_store import SearchResult, load_chunk_metadata  # noqa: E402


FINANCIAL_REVENUE_RE = re.compile(r"(预计|预测).*(2026|26).*(营收|营业收入|营业总收入|主营业务收入)")


def parse_args() -> argparse.Namespace:
    """读取粗到细 compare 检索实验参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", default="data/eval/financial_qa_dev.jsonl")
    parser.add_argument("--index-dir", default="data/processed/indexes/bge_large_zh_v15")
    parser.add_argument("--chunks-meta", default="", help="默认读取 index-dir/chunks_meta.jsonl。")
    parser.add_argument("--compare-rewrite-file", default="data/processed/query_rewrites/compare_financial_table_no_unit_rule.jsonl")
    parser.add_argument("--ks", nargs="+", type=int, default=[5, 8])
    parser.add_argument("--match-level", choices=["doc", "page"], default="page")
    parser.add_argument("--doc-top-n", type=int, default=2)
    parser.add_argument(
        "--adaptive-doc-ratio",
        type=float,
        default=0.0,
        help="大于 0 时启用自适应文档数：top1/top2 分数比超过该阈值则只保留 top1。",
    )
    parser.add_argument("--page-top-k", type=int, default=12)
    parser.add_argument("--per-entity-keep", type=int, default=4)
    parser.add_argument("--parent-window-pages", type=int, default=1)
    parser.add_argument("--parent-max-chars", type=int, default=0)
    parser.add_argument("--output", default="docs/experiments/rerank/14_compare_coarse_to_fine/report.md")
    parser.add_argument("--details-output", default="docs/experiments/rerank/14_compare_coarse_to_fine/details.json")
    parser.add_argument("--badcase-limit", type=int, default=20)
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析为绝对路径。"""
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    """优先显示项目相对路径。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize_text(text: str) -> str:
    """去掉空白和常见分隔符，便于中文实体包含匹配。"""
    return re.sub(r"[\s·・（）()_\-—|/\\：:，,。；;]+", "", text).lower()


def source_key(chunk: dict) -> str:
    """取 chunk 的来源文档键。"""
    return str(chunk.get("source") or chunk.get("doc_id") or "")


def result_key(chunk: dict) -> str:
    """生成粗到细实验内部去重键。"""
    chunk_id = chunk.get("chunk_id")
    if chunk_id:
        return str(chunk_id)
    pages = ",".join(str(page) for page in chunk.get("pages") or [])
    return f"{chunk.get('source','')}:{pages}:{str(chunk.get('text') or '')[:80]}"


def load_chunks(args: argparse.Namespace) -> list[dict]:
    """读取 chunk 元数据。"""
    index_dir = resolve_path(args.index_dir)
    chunks_path = resolve_path(args.chunks_meta) if args.chunks_meta else index_dir / "chunks_meta.jsonl"
    return load_chunk_metadata(chunks_path)


def compare_samples(eval_path: Path) -> tuple[list[eval_base.EvalSample], int, int]:
    """读取评测集，只保留 compare 样本。"""
    samples, total_rows, skipped = eval_base.load_eval_samples(eval_path)
    return [sample for sample in samples if sample.question_type == "compare"], total_rows, skipped


def entities_for_sample(sample: eval_base.EvalSample, rewrites: dict) -> list[str]:
    """优先从 rewrite 缓存取实体，否则从原问题抽取。"""
    rewrite = rewrites.get(sample.question_id)
    if rewrite and len(rewrite.entities) >= 2:
        return rewrite.entities[:2]
    return extract_compare_entities(sample.query)[:2]


def metric_query_for_sample(sample: eval_base.EvalSample, entity: str, entities: list[str], rewrites: dict) -> str:
    """构造文档内页码定位查询，避免重复携带实体名。"""
    rewrite = rewrites.get(sample.question_id)
    if rewrite:
        for index, subquery in enumerate(rewrite.sub_queries):
            if index < len(rewrite.entities) and rewrite.entities[index] == entity:
                return strip_entities_from_query(subquery, entities)
    if FINANCIAL_REVENUE_RE.search(sample.query):
        return "2026E 营收 营业收入 营业总收入 主营业务收入 收入"
    return strip_entities_from_query(sample.query, entities)


def strip_entities_from_query(query: str, entities: list[str]) -> str:
    """从页内定位 query 中去掉公司实体和 compare 连接词。"""
    text = query
    for entity in entities:
        text = text.replace(entity, " ")
    text = re.sub(r"\b(?:vs|VS|Vs|v\.s\.)\b", " ", text)
    text = re.sub(r"(哪家|哪个|公司|相比|比较|更高|更多|预计|实现|的|对比)", " ", text)
    text = " ".join(text.split())
    if "2026" in query and "2026E" not in text:
        text = f"2026E {text}".strip()
    return text or query


def locate_entity_documents(entity: str, chunks: list[dict], doc_top_n: int) -> list[dict]:
    """第一阶段：根据公司实体定位可能的来源文档。"""
    entity_norm = normalize_text(entity)
    if not entity_norm:
        return []
    scored: dict[str, dict] = {}
    for chunk in chunks:
        source = source_key(chunk)
        if not source:
            continue
        metadata = chunk.get("metadata") or {}
        fields = [
            str(chunk.get("text") or ""),
            str(metadata.get("title") or ""),
            str(metadata.get("notes") or ""),
            str(chunk.get("doc_id") or ""),
            source,
        ]
        field_text = "\n".join(fields)
        norm = normalize_text(field_text)
        count = norm.count(entity_norm)
        if count <= 0:
            continue
        pages = chunk.get("pages") or []
        page_min = min([int(page) for page in pages], default=999)
        score = count * 10.0
        if page_min <= 2:
            score += 8.0
        if chunk.get("chunk_type") in {"title", "table"}:
            score += 2.0
        row = scored.setdefault(
            source,
            {
                "source": source,
                "doc_id": chunk.get("doc_id"),
                "score": 0.0,
                "evidence_chunks": [],
            },
        )
        row["score"] += score
        if len(row["evidence_chunks"]) < 3:
            row["evidence_chunks"].append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "pages": pages,
                    "text": str(chunk.get("text") or "")[:120],
                }
            )
    return sorted(scored.values(), key=lambda item: item["score"], reverse=True)[:doc_top_n]


def search_within_sources(
    query: str,
    sources: list[str],
    chunks: list[dict],
    top_k: int,
) -> list[SearchResult]:
    """第二阶段：只在已定位文档内检索目标页和表格。"""
    source_set = set(sources)
    local_chunks = [chunk for chunk in chunks if source_key(chunk) in source_set and str(chunk.get("text") or "").strip()]
    if not local_chunks:
        return []
    store = BM25Store.from_chunks(local_chunks, tokenizer="jieba", include_source=False)
    raw_results = store.search(query, top_k=min(max(top_k * 4, top_k), len(local_chunks)))
    boosted: list[SearchResult] = []
    for result in raw_results:
        score = result.score + page_metric_boost(query, result.chunk)
        boosted.append(SearchResult(score=score, rank=0, chunk=result.chunk))
    boosted.sort(key=lambda item: item.score, reverse=True)
    trimmed = boosted[:top_k]
    for rank, result in enumerate(trimmed, start=1):
        result.rank = rank
    return trimmed


def page_metric_boost(query: str, chunk: dict) -> float:
    """对页内表格和关键财务字段做轻量加分。"""
    text = str(chunk.get("text") or "")
    boost = 0.0
    if chunk.get("has_table"):
        boost += 2.0
    if "2026E" in query and "2026E" in text:
        boost += 3.0
    for term in ["营收", "营业收入", "营业总收入", "主营业务收入"]:
        if term in query and term in text:
            boost += 2.0
    return boost


def retrieve_one_compare(
    sample: eval_base.EvalSample,
    chunks: list[dict],
    parent_store: ParentDocumentStore,
    rewrites: dict,
    args: argparse.Namespace,
) -> tuple[list[SearchResult], dict]:
    """对单条 compare 样本执行粗到细检索。"""
    entities = entities_for_sample(sample, rewrites)
    per_entity: list[list[SearchResult]] = []
    trace = {"entities": entities, "entity_docs": {}, "metric_queries": {}}
    for entity in entities:
        docs = locate_entity_documents(entity, chunks, doc_top_n=args.doc_top_n)
        docs = adapt_document_candidates(docs, ratio_threshold=args.adaptive_doc_ratio)
        sources = [doc["source"] for doc in docs]
        metric_query = metric_query_for_sample(sample, entity, entities, rewrites)
        trace["entity_docs"][entity] = docs
        trace["metric_queries"][entity] = metric_query
        per_entity.append(search_within_sources(metric_query, sources, chunks, top_k=args.page_top_k))

    selected = interleave_results(per_entity, keep=args.per_entity_keep)
    parent_results = expand_results_to_parents(
        selected,
        parent_store=parent_store,
        mode="window",
        window_pages=args.parent_window_pages,
        max_chars=args.parent_max_chars,
        top_k=max(args.ks),
    )
    return parent_results, trace


def adapt_document_candidates(docs: list[dict], ratio_threshold: float) -> list[dict]:
    """当 top1 文档明显领先时，丢弃弱相关的同业提及文档。"""
    if ratio_threshold <= 0 or len(docs) < 2:
        return docs
    top_score = float(docs[0].get("score") or 0.0)
    second_score = float(docs[1].get("score") or 0.0)
    if second_score <= 0:
        return docs[:1]
    if top_score / second_score >= ratio_threshold:
        return docs[:1]
    return docs


def interleave_results(per_entity: list[list[SearchResult]], keep: int) -> list[SearchResult]:
    """按实体交错合并页级候选，避免某一家公司挤占全部位置。"""
    selected: list[SearchResult] = []
    seen: set[str] = set()
    for offset in range(max(1, keep)):
        for results in per_entity:
            if offset >= len(results):
                continue
            result = results[offset]
            key = result_key(result.chunk)
            if key in seen:
                continue
            seen.add(key)
            selected.append(result)
    for rank, result in enumerate(selected, start=1):
        result.rank = rank
    return selected


def run_experiment(args: argparse.Namespace) -> tuple[str, dict]:
    """执行实验并返回 Markdown 报告和明细。"""
    args.ks = sorted(set(args.ks))
    eval_path = resolve_path(args.eval)
    rewrite_path = resolve_path(args.compare_rewrite_file) if args.compare_rewrite_file else None
    chunks = load_chunks(args)
    parent_store = ParentDocumentStore(chunks)
    rewrites = load_compare_rewrites(rewrite_path) if rewrite_path and rewrite_path.exists() else {}
    samples, total_rows, skipped = compare_samples(eval_path)
    start = time.perf_counter()
    results_by_id: dict[str, list[SearchResult]] = {}
    traces: dict[str, dict] = {}
    for sample in samples:
        results, trace = retrieve_one_compare(sample, chunks, parent_store, rewrites, args)
        results_by_id[sample.question_id] = results
        traces[sample.question_id] = trace
    scores = eval_base.score_scheme(samples, results_by_id, args.ks, match_level=args.match_level)
    elapsed = time.perf_counter() - start
    report = render_report(args, eval_path, rewrite_path, samples, total_rows, skipped, elapsed, scores)
    details = {
        "scores": {str(k): [asdict(score) for score in rows] for k, rows in scores.items()},
        "traces": traces,
        "results": {
            question_id: [result_to_dict(result) for result in results]
            for question_id, results in results_by_id.items()
        },
    }
    return report, details


def render_report(
    args: argparse.Namespace,
    eval_path: Path,
    rewrite_path: Path | None,
    samples: list[eval_base.EvalSample],
    total_rows: int,
    skipped: int,
    elapsed_seconds: float,
    scores: dict[int, list[eval_base.SampleScore]],
) -> str:
    """渲染粗到细实验报告。"""
    ks = sorted(args.ks)
    lines = [
        "# Compare 粗到细检索实验",
        "",
        f"- 评测时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 评测集：`{display_path(eval_path)}`",
        f"- compare 样本数：{len(samples)} / {total_rows}",
        f"- 原始跳过样本：{skipped}",
        f"- 匹配粒度：`{args.match_level}`",
        f"- compare rewrite：`{display_path(rewrite_path) if rewrite_path else 'disabled'}`",
        f"- 文档定位数量：每个实体 top{args.doc_top_n}",
        f"- 自适应文档阈值：{args.adaptive_doc_ratio if args.adaptive_doc_ratio > 0 else 'disabled'}",
        f"- 页内检索数量：每个实体 top{args.page_top_k}，交错保留 top{args.per_entity_keep}",
        f"- 父文档窗口：前后各 {args.parent_window_pages} 页",
        f"- 总耗时（秒）：{elapsed_seconds:.2f}",
        "",
        "## 指标",
        "",
        "| scheme | " + " | ".join(f"Recall@{k}" for k in ks) + " | " + " | ".join(f"HitAny@{k}" for k in ks) + " | " + " | ".join(f"HitAll@{k}" for k in ks) + " |",
        "|---|" + "|".join("---:" for _ in range(len(ks) * 3)) + "|",
    ]
    recall_cells = [eval_base.format_rate(eval_base.summarize_scores(scores[k])["recall"]) for k in ks]
    hit_any_cells = [eval_base.format_rate(eval_base.summarize_scores(scores[k])["hit_any"]) for k in ks]
    hit_all_cells = [eval_base.format_rate(eval_base.summarize_scores(scores[k])["hit_all"]) for k in ks]
    lines.append("| coarse_to_fine | " + " | ".join(recall_cells + hit_any_cells + hit_all_cells) + " |")
    lines.extend(
        [
            "",
            "## 说明",
            "",
            "- 本实验不修改主 routed 检索链路，只验证 compare 题的候选生成思路。",
            "- 第一阶段用公司实体在全库中定位 PDF；第二阶段只在对应 PDF 内检索年份和财务字段所在页。",
            "- 该实验暂未接入向量召回和 cross-encoder rerank，主要用于判断“先文档、后页码”的方向是否值得并入正式流程。",
            "",
        ]
    )
    lines.extend(eval_base.render_badcases(args, {"coarse_to_fine": scores}, max(ks)))
    return "\n".join(lines).rstrip() + "\n"


def result_to_dict(result: SearchResult) -> dict:
    """把检索结果序列化成实验明细。"""
    return {
        "rank": result.rank,
        "score": result.score,
        "chunk_id": result.chunk.get("chunk_id"),
        "parent_id": result.chunk.get("parent_id"),
        "child_chunk_id": result.chunk.get("child_chunk_id"),
        "source": result.chunk.get("source"),
        "pages": result.chunk.get("pages"),
        "child_hits": result.chunk.get("child_hits", []),
        "text": str(result.chunk.get("text") or "")[:500],
    }


def main() -> None:
    """运行粗到细 compare 检索实验并写出报告。"""
    args = parse_args()
    report, details = run_experiment(args)
    print(report)
    output_path = resolve_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    details_path = resolve_path(args.details_output)
    details_path.parent.mkdir(parents=True, exist_ok=True)
    details_path.write_text(json.dumps(details, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote: {display_path(output_path)}")
    print(f"wrote: {display_path(details_path)}")


if __name__ == "__main__":
    main()
