#!/usr/bin/env python
"""基于 routed 检索结果调用 LLM 生成答案。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path


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

from financial_report_rag.generation.context_formatter import ContextFormatConfig, format_contexts  # noqa: E402
from financial_report_rag.generation.llm_client import OpenAIChatClient, OpenAIChatConfig  # noqa: E402
from financial_report_rag.generation.prompt_builder import build_answer_messages  # noqa: E402
from financial_report_rag.retrieval.routed_retriever import (  # noqa: E402
    RoutedRetrievalConfig,
    RoutedRetriever,
    RoutedRetrieverConfig,
)


def parse_args() -> argparse.Namespace:
    """读取回答生成参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--query", help="单条问题。")
    input_group.add_argument("--eval", help="评测集 JSON/JSONL，批量生成答案。")
    parser.add_argument("--question-type", choices=["fact", "compare", "summary"], default="fact")
    parser.add_argument("--output", default="data/generated/routed_answers.jsonl")
    parser.add_argument("--limit", type=int, default=0, help="批量模式最多处理多少条，0 表示不限制。")
    parser.add_argument("--start", type=int, default=0, help="批量模式从第几条开始处理。")
    parser.add_argument("--dry-run", action="store_true", help="只保存 prompt 和上下文，不调用 API。")

    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--base-url", default="", help="默认读 OPENAI_BASE_URL，缺省为 https://api.vveai.com/v1。")
    parser.add_argument("--model", default="", help="默认读 OPENAI_MODEL，缺省为 gpt-4o-mini。")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=900)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)

    parser.add_argument("--index-dir", default="data/processed/indexes/bge_large_zh_v15")
    parser.add_argument("--index-type", choices=["flat", "ivf", "hnsw"], default="flat")
    parser.add_argument("--bm25-path", default="")
    parser.add_argument("--embedding-model", default="models/bge-large-zh-v1.5")
    parser.add_argument("--embedding-backend", choices=["sentence-transformers", "flagembedding"], default="sentence-transformers")
    parser.add_argument("--embedding-batch-size", type=int, default=16)
    parser.add_argument("--embedding-max-length", type=int, default=512)
    parser.add_argument("--reranker-model", default="models/bge-reranker-v2-m3")
    parser.add_argument("--reranker-backend", choices=["flagembedding", "transformers"], default="transformers")
    parser.add_argument("--reranker-batch-size", type=int, default=2)
    parser.add_argument("--reranker-max-length", type=int, default=512)
    parser.add_argument("--use-fp16", action="store_true")
    parser.add_argument("--vector-weight", type=float, default=0.6)
    parser.add_argument("--bm25-weight", type=float, default=0.4)
    parser.add_argument("--fusion", choices=["weighted", "rrf"], default="weighted")
    parser.add_argument("--rrf-k", type=int, default=60)

    parser.add_argument("--parent-window-pages", type=int, default=1)
    parser.add_argument("--parent-max-chars", type=int, default=0)
    parser.add_argument("--fact-top-k", type=int, default=5)
    parser.add_argument("--compare-candidate-top-k", type=int, default=20)
    parser.add_argument("--compare-top-k", type=int, default=5)
    parser.add_argument("--summary-candidate-top-k", type=int, default=50)
    parser.add_argument("--summary-top-k", type=int, default=8)
    parser.add_argument("--summary-per-source", type=int, default=2)

    parser.add_argument("--max-contexts", type=int, default=8)
    parser.add_argument("--max-chars-per-context", type=int, default=1800)
    parser.add_argument("--max-total-context-chars", type=int, default=9000)
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析为绝对路径。"""
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def build_retriever(args: argparse.Namespace) -> RoutedRetriever:
    """构建默认 routed 检索器。"""
    runtime_config = RoutedRetrieverConfig(
        index_dir=args.index_dir,
        index_type=args.index_type,
        bm25_path=args.bm25_path,
        embedding_model=args.embedding_model,
        embedding_backend=args.embedding_backend,
        embedding_batch_size=args.embedding_batch_size,
        embedding_max_length=args.embedding_max_length,
        use_fp16=args.use_fp16,
        reranker_model=args.reranker_model,
        reranker_backend=args.reranker_backend,
        reranker_batch_size=args.reranker_batch_size,
        reranker_max_length=args.reranker_max_length,
        vector_weight=args.vector_weight,
        bm25_weight=args.bm25_weight,
        fusion=args.fusion,
        rrf_k=args.rrf_k,
    )
    route_config = RoutedRetrievalConfig(
        parent_window_pages=args.parent_window_pages,
        parent_max_chars=args.parent_max_chars,
        fact_top_k=args.fact_top_k,
        compare_candidate_top_k=args.compare_candidate_top_k,
        compare_top_k=args.compare_top_k,
        summary_candidate_top_k=args.summary_candidate_top_k,
        summary_top_k=args.summary_top_k,
        summary_per_source=args.summary_per_source,
    )
    return RoutedRetriever(runtime_config, route_config, base_dir=ROOT)


def build_llm_client(args: argparse.Namespace) -> OpenAIChatClient | None:
    """按需构建 OpenAI-compatible 客户端。"""
    if args.dry_run:
        return None
    api_key = os.getenv(args.api_key_env, "")
    base_url = args.base_url or os.getenv("OPENAI_BASE_URL", "https://api.vveai.com/v1")
    model = args.model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return OpenAIChatClient(
        OpenAIChatConfig(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
        )
    )


def iter_questions(args: argparse.Namespace) -> list[dict]:
    """读取单条问题或批量评测集问题。"""
    if args.query:
        return [
            {
                "question_id": "manual_001",
                "question_type": args.question_type,
                "query": args.query,
            }
        ]

    rows = load_rows(resolve_path(args.eval))
    questions = []
    for row in rows:
        query = str(row.get("query") or "").strip()
        if not query:
            continue
        questions.append(
            {
                "question_id": str(row.get("question_id") or f"sample_{len(questions) + 1:03d}"),
                "question_type": str(row.get("question_type") or "fact"),
                "query": query,
            }
        )
    if args.start:
        questions = questions[args.start :]
    if args.limit > 0:
        questions = questions[: args.limit]
    return questions


def load_rows(path: Path) -> list[dict]:
    """读取 JSON 数组或 JSONL 文件。"""
    if path.suffix.lower() == ".jsonl":
        rows: list[dict] = []
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
    raise ValueError(f"不支持的评测集格式：{path}")


def generate_one(
    question: dict,
    retriever: RoutedRetriever,
    client: OpenAIChatClient | None,
    context_config: ContextFormatConfig,
    dry_run: bool,
) -> dict:
    """完成一条问题的检索、prompt 构造和回答生成。"""
    routed = retriever.retrieve(question["query"], question_type=question["question_type"])
    formatted = format_contexts(
        routed.results,
        context_config,
        query=question["query"],
        question_type=routed.question_type,
    )
    messages = build_answer_messages(question["query"], routed.question_type, formatted.text)
    answer = "" if dry_run else client.generate(messages)
    return {
        "question_id": question["question_id"],
        "question_type": routed.question_type,
        "query": question["query"],
        "strategy": routed.strategy,
        "answer": answer,
        "dry_run": dry_run,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "references": formatted.references,
        "messages": messages,
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    """追加写入 JSONL。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()


def main() -> None:
    """执行回答生成。"""
    args = parse_args()
    questions = iter_questions(args)
    if not questions:
        raise SystemExit("没有可处理的问题。")

    retriever = build_retriever(args)
    client = build_llm_client(args)
    context_config = ContextFormatConfig(
        max_contexts=args.max_contexts,
        max_chars_per_context=args.max_chars_per_context,
        max_total_chars=args.max_total_context_chars,
    )
    output_path = resolve_path(args.output)

    for index, question in enumerate(questions, start=1):
        row = generate_one(question, retriever, client, context_config, dry_run=args.dry_run)
        write_jsonl(output_path, [row])
        print(f"[{index}/{len(questions)}] wrote {question['question_id']} -> {output_path.relative_to(ROOT)}")
        if row["answer"]:
            print(row["answer"])
        if args.sleep_seconds > 0 and index < len(questions):
            time.sleep(args.sleep_seconds)


if __name__ == "__main__":
    main()
