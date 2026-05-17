#!/usr/bin/env python
"""评估 FAISS、BM25 和混合召回的 Recall@K。"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
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

from financial_report_rag.retrieval.bm25_store import BM25Store  # noqa: E402
from financial_report_rag.retrieval.embeddings import EmbeddingConfig, FlagEmbeddingModel  # noqa: E402
from financial_report_rag.retrieval.hybrid_retriever import HybridSearchResult, fuse_results  # noqa: E402
from financial_report_rag.retrieval.vector_store import (  # noqa: E402
    SearchResult,
    load_chunk_metadata,
    load_faiss_index,
    search_index,
)


@dataclass
class Evidence:
    doc_id: str
    source: str
    pages: set[int]


@dataclass
class EvalSample:
    question_id: str
    question_type: str
    query: str
    answer: str
    evidences: list[Evidence]
    raw: dict


@dataclass
class SampleScore:
    question_id: str
    question_type: str
    query: str
    coverage: float
    matched: int
    total: int
    hit_any: bool
    hit_all: bool
    top_sources: list[str]


def parse_args() -> argparse.Namespace:
    """读取命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", default="data/eval/financial_qa_dev.template.json", help="评测集 JSON 或 JSONL。")
    parser.add_argument("--index-dir", default="data/processed/indexes/bge_large_zh_v15")
    parser.add_argument("--index-type", choices=["flat", "ivf", "hnsw"], default="flat")
    parser.add_argument("--bm25-path", default="")
    parser.add_argument("--schemes", nargs="+", choices=["vector", "bm25", "hybrid"], default=["vector", "bm25", "hybrid"])
    parser.add_argument("--ks", nargs="+", type=int, default=[3, 5, 10])
    parser.add_argument("--match-level", choices=["doc", "page"], default="page")
    parser.add_argument("--vector-top-k", type=int, default=20)
    parser.add_argument("--bm25-top-k", type=int, default=20)
    parser.add_argument("--vector-weight", type=float, default=0.5)
    parser.add_argument("--bm25-weight", type=float, default=0.5)
    parser.add_argument("--fusion", choices=["weighted", "rrf"], default="weighted")
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--model", default="BAAI/bge-large-zh-v1.5")
    parser.add_argument("--backend", choices=["sentence-transformers", "flagembedding"], default="sentence-transformers")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--no-normalize", action="store_true")
    parser.add_argument("--use-fp16", action="store_true")
    parser.add_argument("--vector-lower-is-better", action="store_true", help="当 FAISS 使用 L2 分数时启用。")
    parser.add_argument("--output", default="", help="可选：把评测结果写入 Markdown 文件。")
    parser.add_argument("--details-output", default="", help="可选：把逐样本结果写入 JSON 文件。")
    parser.add_argument("--badcase-limit", type=int, default=20)
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析成绝对路径。"""
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def display_path(path: Path) -> str:
    """优先用项目相对路径展示文件。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_eval_rows(path: Path) -> list[dict]:
    """读取 JSON 数组或 JSONL 格式的评测集。"""
    if path.suffix.lower() == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return data["data"]
    raise ValueError(f"不支持的评测集结构：{path}")


def load_eval_samples(path: Path) -> tuple[list[EvalSample], int, int]:
    """读取评测集并跳过尚未填写完成的样本。"""
    rows = load_eval_rows(path)
    samples: list[EvalSample] = []
    skipped = 0
    for row in rows:
        query = str(row.get("query") or "").strip()
        evidences = parse_evidences(row.get("ground_truth") or [])
        if not query or not evidences:
            skipped += 1
            continue
        samples.append(
            EvalSample(
                question_id=str(row.get("question_id") or ""),
                question_type=str(row.get("question_type") or "unknown"),
                query=query,
                answer=str(row.get("answer") or ""),
                evidences=evidences,
                raw=row,
            )
        )
    return samples, len(rows), skipped


def parse_evidences(items: Iterable[dict]) -> list[Evidence]:
    """把 ground_truth 转成用于匹配召回结果的证据列表。"""
    evidences: list[Evidence] = []
    for item in items:
        doc_id = normalize_doc_id(item.get("doc_id") or "")
        source = normalize_source(item.get("source") or "")
        pages = parse_pages(item.get("pages") or [])
        if doc_id or source:
            evidences.append(Evidence(doc_id=doc_id, source=source, pages=pages))
    return dedupe_evidences(evidences)


def parse_pages(value: object) -> set[int]:
    """解析 1-based 页码列表。"""
    pages: set[int] = set()
    if not isinstance(value, list):
        return pages
    for page in value:
        try:
            pages.add(int(page))
        except (TypeError, ValueError):
            continue
    return pages


def dedupe_evidences(evidences: list[Evidence]) -> list[Evidence]:
    """去掉重复填写的证据项。"""
    seen: set[tuple[str, str, tuple[int, ...]]] = set()
    deduped: list[Evidence] = []
    for evidence in evidences:
        key = (evidence.doc_id, evidence.source, tuple(sorted(evidence.pages)))
        if key not in seen:
            seen.add(key)
            deduped.append(evidence)
    return deduped


def load_manifest(index_dir: Path) -> dict:
    """读取向量索引构建登记信息。"""
    manifest_path = index_dir / "index_manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def load_vector_resources(args: argparse.Namespace, index_dir: Path, max_k: int):
    """加载向量检索需要的模型、索引和元数据。"""
    manifest = load_manifest(index_dir)
    metadata = load_chunk_metadata(index_dir / "chunks_meta.jsonl")
    config = EmbeddingConfig(
        model_name=manifest.get("model", args.model),
        backend=manifest.get("backend", args.backend),
        batch_size=args.batch_size,
        max_length=manifest.get("max_length", args.max_length),
        normalize=manifest.get("normalize", not args.no_normalize),
        use_fp16=manifest.get("use_fp16", args.use_fp16),
    )
    embedder = FlagEmbeddingModel(config)
    index = load_faiss_index(index_dir / f"faiss_{args.index_type}.index")
    top_k = max(max_k, args.vector_top_k)
    return embedder, index, metadata, top_k


def run_vector_searches(
    samples: list[EvalSample],
    embedder: FlagEmbeddingModel,
    index,
    metadata: list[dict],
    top_k: int,
) -> dict[str, list[SearchResult]]:
    """批量编码 query 后执行向量检索。"""
    vectors = embedder.encode_queries([sample.query for sample in samples])
    results: dict[str, list[SearchResult]] = {}
    for sample, vector in zip(samples, vectors):
        results[sample.question_id] = search_index(index, metadata, vector, top_k=top_k)
    return results


def run_bm25_searches(samples: list[EvalSample], bm25_store: BM25Store, top_k: int) -> dict[str, list[SearchResult]]:
    """执行 BM25 检索。"""
    return {sample.question_id: bm25_store.search(sample.query, top_k=top_k) for sample in samples}


def run_hybrid_searches(
    samples: list[EvalSample],
    vector_results: dict[str, list[SearchResult]],
    bm25_results: dict[str, list[SearchResult]],
    args: argparse.Namespace,
    max_k: int,
) -> dict[str, list[HybridSearchResult]]:
    """融合向量和 BM25 两路召回。"""
    results: dict[str, list[HybridSearchResult]] = {}
    for sample in samples:
        results[sample.question_id] = fuse_results(
            vector_results.get(sample.question_id, []),
            bm25_results.get(sample.question_id, []),
            top_k=max_k,
            vector_weight=args.vector_weight,
            bm25_weight=args.bm25_weight,
            method=args.fusion,
            vector_higher_is_better=not args.vector_lower_is_better,
            rrf_k=args.rrf_k,
        )
    return results


def score_scheme(
    samples: list[EvalSample],
    results_by_id: dict[str, list[SearchResult | HybridSearchResult]],
    ks: list[int],
    match_level: str,
) -> dict[int, list[SampleScore]]:
    """计算某一路召回在不同 K 下的逐样本分数。"""
    scored: dict[int, list[SampleScore]] = {k: [] for k in ks}
    for sample in samples:
        results = results_by_id.get(sample.question_id, [])
        for k in ks:
            scored[k].append(score_sample(sample, results[:k], match_level=match_level))
    return scored


def score_sample(
    sample: EvalSample,
    results: list[SearchResult | HybridSearchResult],
    match_level: str,
) -> SampleScore:
    """计算一个问题的证据覆盖率。"""
    matched = 0
    for evidence in sample.evidences:
        if any(evidence_matches_chunk(evidence, result.chunk, match_level=match_level) for result in results):
            matched += 1
    total = len(sample.evidences)
    coverage = matched / total if total else 0.0
    return SampleScore(
        question_id=sample.question_id,
        question_type=sample.question_type,
        query=sample.query,
        coverage=coverage,
        matched=matched,
        total=total,
        hit_any=matched > 0,
        hit_all=matched == total and total > 0,
        top_sources=top_sources(results),
    )


def evidence_matches_chunk(evidence: Evidence, chunk: dict, match_level: str) -> bool:
    """判断一个召回 chunk 是否命中某条 ground truth。"""
    doc_match = evidence_matches_doc(evidence, chunk)
    if not doc_match:
        return False
    if match_level == "doc":
        return True
    if not evidence.pages:
        return True
    chunk_pages = parse_pages(chunk.get("pages") or [])
    return bool(evidence.pages & chunk_pages)


def evidence_matches_doc(evidence: Evidence, chunk: dict) -> bool:
    """用 doc_id 或 source 判断文档是否一致。"""
    chunk_doc_id = normalize_doc_id(chunk.get("doc_id") or "")
    chunk_source = normalize_source(chunk.get("source") or "")
    if evidence.doc_id and evidence.doc_id == chunk_doc_id:
        return True
    if evidence.source and sources_match(evidence.source, chunk_source):
        return True
    return False


def sources_match(expected: str, actual: str) -> bool:
    """比较 source 路径，兼容相对路径和大小写差异。"""
    if not expected or not actual:
        return False
    if expected == actual:
        return True
    if expected.endswith(actual) or actual.endswith(expected):
        return True
    return Path(expected).name.lower() == Path(actual).name.lower()


def top_sources(results: list[SearchResult | HybridSearchResult]) -> list[str]:
    """提取召回结果中的来源文档，方便 badcase 查看。"""
    sources: list[str] = []
    for result in results:
        source = str(result.chunk.get("source") or result.chunk.get("doc_id") or "")
        if source and source not in sources:
            sources.append(source)
    return sources[:5]


def summarize_scores(scores: list[SampleScore]) -> dict[str, float]:
    """汇总逐样本分数。"""
    if not scores:
        return {"recall": 0.0, "hit_any": 0.0, "hit_all": 0.0}
    total = len(scores)
    return {
        "recall": sum(score.coverage for score in scores) / total,
        "hit_any": sum(1 for score in scores if score.hit_any) / total,
        "hit_all": sum(1 for score in scores if score.hit_all) / total,
    }


def summarize_by_type(scores: list[SampleScore]) -> dict[str, dict[str, float]]:
    """按问题类型汇总 Recall。"""
    grouped: dict[str, list[SampleScore]] = {}
    for score in scores:
        grouped.setdefault(score.question_type, []).append(score)
    return {question_type: summarize_scores(items) for question_type, items in sorted(grouped.items())}


def render_markdown(
    args: argparse.Namespace,
    eval_path: Path,
    samples: list[EvalSample],
    total_rows: int,
    skipped: int,
    elapsed_seconds: float,
    all_scores: dict[str, dict[int, list[SampleScore]]],
) -> str:
    """把评测结果渲染成 Markdown。"""
    ks = sorted(args.ks)
    lines = [
        "# Retrieval Evaluation",
        "",
        f"- evaluated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- eval_file: `{display_path(eval_path)}`",
        f"- index_dir: `{args.index_dir}`",
        f"- index_type: `{args.index_type}`",
        f"- match_level: `{args.match_level}`",
        f"- completed_samples: {len(samples)} / {total_rows}",
        f"- skipped_samples: {skipped}",
        f"- elapsed_seconds: {elapsed_seconds:.2f}",
        f"- fusion: `{args.fusion}`",
        f"- weights: vector={args.vector_weight}, bm25={args.bm25_weight}",
        "",
        "## Overall",
        "",
        "| scheme | " + " | ".join(f"Recall@{k}" for k in ks) + " | " + " | ".join(f"HitAll@{k}" for k in ks) + " |",
        "|---|" + "|".join("---:" for _ in range(len(ks) * 2)) + "|",
    ]

    for scheme, scheme_scores in all_scores.items():
        recall_cells = [format_rate(summarize_scores(scheme_scores[k])["recall"]) for k in ks]
        hit_all_cells = [format_rate(summarize_scores(scheme_scores[k])["hit_all"]) for k in ks]
        lines.append(f"| {scheme} | " + " | ".join(recall_cells + hit_all_cells) + " |")

    lines.extend(["", "## By Question Type", ""])
    for scheme, scheme_scores in all_scores.items():
        largest_k = max(ks)
        lines.extend([
            f"### {scheme} @ {largest_k}",
            "",
            "| question_type | count | Recall | HitAny | HitAll |",
            "|---|---:|---:|---:|---:|",
        ])
        grouped: dict[str, list[SampleScore]] = {}
        for score in scheme_scores[largest_k]:
            grouped.setdefault(score.question_type, []).append(score)
        for question_type, items in sorted(grouped.items()):
            summary = summarize_scores(items)
            lines.append(
                f"| {question_type} | {len(items)} | {format_rate(summary['recall'])} | "
                f"{format_rate(summary['hit_any'])} | {format_rate(summary['hit_all'])} |"
            )
        lines.append("")

    lines.extend(render_badcases(args, all_scores, max(ks)))
    return "\n".join(lines).rstrip() + "\n"


def render_badcases(
    args: argparse.Namespace,
    all_scores: dict[str, dict[int, list[SampleScore]]],
    k: int,
) -> list[str]:
    """渲染每一路在最大 K 下仍未完全命中的样本。"""
    lines = ["## Badcases", ""]
    for scheme, scheme_scores in all_scores.items():
        misses = [score for score in scheme_scores[k] if not score.hit_all]
        lines.extend([f"### {scheme} @ {k}", ""])
        if not misses:
            lines.extend(["No badcases.", ""])
            continue
        for score in misses[: args.badcase_limit]:
            lines.extend(
                [
                    f"- `{score.question_id}` {score.question_type} coverage={score.matched}/{score.total}",
                    f"  query: {score.query}",
                    f"  top_sources: {score.top_sources}",
                ]
            )
        lines.append("")
    return lines


def format_rate(value: float) -> str:
    """把 0-1 浮点数格式化为百分比。"""
    return f"{value * 100:.2f}%"


def normalize_doc_id(value: str) -> str:
    """规范化 doc_id。"""
    return value.strip().lower()


def normalize_source(value: str) -> str:
    """规范化 source 路径。"""
    return value.strip().replace("\\", "/").lower()


def write_details(path: Path, all_scores: dict[str, dict[int, list[SampleScore]]]) -> None:
    """把逐样本评测结果写成 JSON。"""
    payload: dict[str, dict[str, list[dict]]] = {}
    for scheme, scheme_scores in all_scores.items():
        payload[scheme] = {}
        for k, scores in scheme_scores.items():
            payload[scheme][str(k)] = [score.__dict__ for score in scores]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    """加载索引和评测集，输出三路召回指标。"""
    args = parse_args()
    args.ks = sorted(set(args.ks))
    max_k = max(args.ks)
    eval_path = resolve_path(args.eval)
    index_dir = resolve_path(args.index_dir)
    bm25_path = resolve_path(args.bm25_path) if args.bm25_path else index_dir / "bm25.pkl"

    samples, total_rows, skipped = load_eval_samples(eval_path)
    if not samples:
        print(f"No completed eval samples found in {display_path(eval_path)}.")
        print("请至少填写 query，以及 ground_truth 里的 doc_id 或 source。")
        return

    start = time.perf_counter()
    vector_results: dict[str, list[SearchResult]] = {}
    bm25_results: dict[str, list[SearchResult]] = {}

    if any(scheme in args.schemes for scheme in {"vector", "hybrid"}):
        embedder, index, metadata, vector_top_k = load_vector_resources(args, index_dir, max_k)
        vector_results = run_vector_searches(samples, embedder, index, metadata, top_k=vector_top_k)

    if any(scheme in args.schemes for scheme in {"bm25", "hybrid"}):
        if not bm25_path.exists():
            raise SystemExit(f"BM25 index not found: {bm25_path}\n请先运行 scripts/build_bm25_index.py")
        bm25_store = BM25Store.load(bm25_path)
        bm25_top_k = max(max_k, args.bm25_top_k)
        bm25_results = run_bm25_searches(samples, bm25_store, top_k=bm25_top_k)

    raw_results: dict[str, dict[str, list[SearchResult | HybridSearchResult]]] = {}
    if "vector" in args.schemes:
        raw_results["vector"] = vector_results
    if "bm25" in args.schemes:
        raw_results["bm25"] = bm25_results
    if "hybrid" in args.schemes:
        raw_results["hybrid"] = run_hybrid_searches(samples, vector_results, bm25_results, args, max_k=max_k)

    all_scores = {
        scheme: score_scheme(samples, results_by_id, args.ks, match_level=args.match_level)
        for scheme, results_by_id in raw_results.items()
    }
    elapsed_seconds = time.perf_counter() - start
    report = render_markdown(args, eval_path, samples, total_rows, skipped, elapsed_seconds, all_scores)
    print(report)

    if args.output:
        output_path = resolve_path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(f"wrote: {display_path(output_path)}")
    if args.details_output:
        details_path = resolve_path(args.details_output)
        write_details(details_path, all_scores)
        print(f"wrote: {display_path(details_path)}")


if __name__ == "__main__":
    main()
