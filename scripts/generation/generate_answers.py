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
from types import SimpleNamespace


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
EVALUATION = ROOT / "scripts" / "evaluation"
if str(EVALUATION) not in sys.path:
    sys.path.insert(0, str(EVALUATION))

import evaluate_retrieval as eval_base  # noqa: E402
import evaluate_routed_retrieval as routed_eval  # noqa: E402

from financial_report_rag.generation.context_formatter import ContextFormatConfig, format_contexts  # noqa: E402
from financial_report_rag.generation.llm_client import OpenAIChatClient, OpenAIChatConfig  # noqa: E402
from financial_report_rag.generation.prompt_builder import build_answer_messages, build_summary_evidence_messages  # noqa: E402
from financial_report_rag.generation.summary_evidence import SummaryEvidenceConfig, build_summary_evidence_pack  # noqa: E402


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
    parser.add_argument("--only-question-type", choices=["fact", "compare", "summary"], default="", help="批量模式只处理某类问题。")
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
    parser.add_argument("--score-activation", choices=["none", "sigmoid"], default="none")
    parser.add_argument("--score-threshold", type=float, default=None)
    parser.add_argument("--relative-drop-threshold", type=float, default=None)
    parser.add_argument("--use-fp16", action="store_true")
    parser.add_argument("--no-normalize", action="store_true")
    parser.add_argument("--vector-weight", type=float, default=0.6)
    parser.add_argument("--bm25-weight", type=float, default=0.4)
    parser.add_argument("--fusion", choices=["weighted", "rrf"], default="weighted")
    parser.add_argument("--rrf-k", type=int, default=60)

    parser.add_argument("--parent-window-pages", type=int, default=1)
    parser.add_argument("--parent-max-chars", type=int, default=0)
    parser.add_argument("--fact-top-k", type=int, default=5)
    parser.add_argument("--compare-candidate-top-k", type=int, default=20)
    parser.add_argument("--compare-entity-top-k", type=int, default=8)
    parser.add_argument("--compare-rewrite-file", default="", help="可选：compare query rewrite JSONL。")
    parser.add_argument("--compare-rewrite-top-k", type=int, default=8)
    parser.add_argument("--compare-rewrite-mode", choices=["separate", "supplement"], default="separate")
    parser.add_argument("--compare-rewrite-per-query-keep", type=int, default=2)
    parser.add_argument("--compare-rewrite-include-merged", action="store_true")
    parser.add_argument("--compare-parent-fill", action="store_true")
    parser.add_argument("--compare-parent-fill-pool", type=int, default=12)
    parser.add_argument("--compare-coarse-to-fine-supplement", action="store_true")
    parser.add_argument("--compare-coarse-doc-top-n", type=int, default=2)
    parser.add_argument("--compare-coarse-adaptive-doc-ratio", type=float, default=3.0)
    parser.add_argument("--compare-coarse-page-top-k", type=int, default=12)
    parser.add_argument("--compare-coarse-per-entity-keep", type=int, default=4)
    parser.add_argument("--compare-coarse-guarantee-per-entity", type=int, default=1)
    parser.add_argument("--compare-top-k", type=int, default=5)
    parser.add_argument("--summary-candidate-top-k", type=int, default=50)
    parser.add_argument("--summary-top-k", type=int, default=8)
    parser.add_argument("--summary-per-source", type=int, default=2)
    parser.add_argument("--summary-subtopic-slots", action="store_true", help="实验开关：summary 子主题槽位。默认不启用。")
    parser.add_argument("--summary-subtopic-top-k", type=int, default=12)
    parser.add_argument("--summary-subtopic-max-queries", type=int, default=6)
    parser.add_argument("--summary-subtopic-guarantee-per-query", type=int, default=1)
    parser.add_argument("--summary-subtopic-per-query-keep", type=int, default=2)
    parser.add_argument("--summary-subtopic-per-source", type=int, default=1)

    parser.add_argument("--max-contexts", type=int, default=8)
    parser.add_argument("--max-chars-per-context", type=int, default=1800)
    parser.add_argument("--max-total-context-chars", type=int, default=9000)
    parser.add_argument("--summary-evidence-pack", action="store_true", help="仅对 summary 题启用证据包压缩和专属 prompt。")
    parser.add_argument("--summary-evidence-points-per-context", type=int, default=6)
    parser.add_argument("--summary-evidence-max-chars", type=int, default=7000)
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析为绝对路径。"""
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def display_path(path: Path) -> str:
    """优先显示项目相对路径，项目外路径则原样显示。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


class GenerationRoutedRetriever:
    """生成阶段复用 routed 检索评测中已经验证的完整流程。"""

    def __init__(self, args: argparse.Namespace):
        """一次性加载索引、BM25、embedding、reranker 和 rewrite 缓存。"""
        self.args = normalize_retrieval_args(args)
        self.config = routed_eval.routed_config_from_args(self.args)
        self.index_dir = resolve_path(self.args.index_dir)
        self.bm25_path = resolve_path(self.args.bm25_path) if self.args.bm25_path else self.index_dir / "bm25.pkl"
        self.compare_rewrite_path = resolve_path(self.args.compare_rewrite_file) if self.args.compare_rewrite_file else None
        if self.compare_rewrite_path and not self.compare_rewrite_path.exists():
            raise SystemExit(f"Compare rewrite file not found: {self.compare_rewrite_path}")
        self.rewrite_by_id = (
            routed_eval.load_compare_rewrites(self.compare_rewrite_path)
            if self.compare_rewrite_path
            else {}
        )
        self.embedder, self.index, self.metadata, _manifest = routed_eval.load_vector_resources(self.args, self.index_dir)
        if not self.bm25_path.exists():
            raise SystemExit(f"BM25 index not found: {self.bm25_path}")
        self.bm25_store = routed_eval.BM25Store.load(self.bm25_path)
        self.parent_store = routed_eval.ParentDocumentStore(self.metadata)
        self._reranker = None

    def retrieve_question(self, question: dict) -> SimpleNamespace:
        """按题目字典执行一次检索，保留与旧生成脚本兼容的输出字段。"""
        sample = eval_base.EvalSample(
            question_id=str(question.get("question_id") or "manual_001"),
            question_type=str(question.get("question_type") or "fact"),
            query=str(question.get("query") or ""),
            answer="",
            evidences=[],
            raw=question,
        )
        return self.retrieve_sample(sample)

    def retrieve_sample(self, sample: eval_base.EvalSample) -> SimpleNamespace:
        """复刻 evaluate_routed_retrieval.py 的单样本 routed 流程。"""
        candidate_top_k = routed_eval.max_candidate_top_k(self.config)
        vector_results = routed_eval.run_vector_searches(
            [sample],
            self.embedder,
            self.index,
            self.metadata,
            top_k=candidate_top_k,
        )
        bm25_results = {sample.question_id: self.bm25_store.search(sample.query, top_k=candidate_top_k)}
        hybrid_results = routed_eval.run_hybrid_searches(
            self.args,
            [sample],
            vector_results,
            bm25_results,
            top_k=candidate_top_k,
        )
        hybrid_results, compare_rerank_results = self.run_compare_rerank(sample, hybrid_results)
        hybrid_results = routed_eval.expand_summary_hybrid_results(
            self.args,
            [sample],
            self.embedder,
            self.index,
            self.metadata,
            self.bm25_store,
            hybrid_results,
            self.config,
        )
        routed_results = routed_eval.run_routed_searches(
            [sample],
            hybrid_results,
            compare_rerank_results,
            self.parent_store,
            self.config,
            args=self.args,
        )
        return SimpleNamespace(
            query=sample.query,
            question_type=sample.question_type,
            strategy=routed_eval.routed_strategy_name(sample.question_type, self.args, self.config),
            results=routed_results.get(sample.question_id, []),
            hybrid_results=hybrid_results.get(sample.question_id, []),
            rerank_results=compare_rerank_results.get(sample.question_id, []),
        )

    def run_compare_rerank(
        self,
        sample: eval_base.EvalSample,
        hybrid_results: dict[str, list],
    ) -> tuple[dict[str, list], dict[str, list]]:
        """为单条 compare 问题执行最新的 rewrite、粗到细槽位和 rerank 流程。"""
        if sample.question_type != "compare":
            return hybrid_results, {}
        if self.rewrite_by_id and self.args.compare_rewrite_mode == "separate":
            return hybrid_results, {sample.question_id: self.rerank_compare_with_rewrites(sample, hybrid_results)}

        expanded = routed_eval.expand_compare_hybrid_results(
            self.args,
            [sample],
            self.embedder,
            self.index,
            self.metadata,
            self.bm25_store,
            hybrid_results,
            self.config,
            self.rewrite_by_id,
        )
        merge_top_k = routed_eval.compare_merge_top_k(self.args, self.config)
        base_reranked = self.reranker.rerank(
            sample.query,
            expanded.get(sample.question_id, []),
            top_k=merge_top_k if self.args.compare_coarse_to_fine_supplement else self.config.compare_top_k,
        )
        coarse_guaranteed, coarse_supplemental = routed_eval.run_compare_coarse_to_fine_slots(
            self.args,
            sample,
            self.metadata,
            self.reranker,
            self.rewrite_by_id,
            self.config,
        )
        merged = (
            routed_eval.merge_rerank_results([*coarse_guaranteed, *coarse_supplemental], base_reranked, top_k=merge_top_k)
            if coarse_guaranteed or coarse_supplemental
            else base_reranked
        )
        return expanded, {sample.question_id: merged}

    def rerank_compare_with_rewrites(
        self,
        sample: eval_base.EvalSample,
        hybrid_results: dict[str, list],
    ) -> list:
        """复用 17 号实验的 compare 子查询配额、raw entity slots 和 parent fill 候选池。"""
        rewrite = self.rewrite_by_id.get(sample.question_id)
        base_results = hybrid_results.get(sample.question_id, [])[: self.config.compare_candidate_top_k]
        merge_top_k = routed_eval.compare_merge_top_k(self.args, self.config)
        original_reranked = self.reranker.rerank(sample.query, base_results, top_k=merge_top_k)
        coarse_guaranteed, coarse_supplemental = routed_eval.run_compare_coarse_to_fine_slots(
            self.args,
            sample,
            self.metadata,
            self.reranker,
            self.rewrite_by_id,
            self.config,
        )
        if rewrite is None:
            return (
                routed_eval.merge_rerank_results(
                    [*coarse_guaranteed, *coarse_supplemental],
                    original_reranked,
                    top_k=merge_top_k,
                )
                if coarse_guaranteed or coarse_supplemental
                else original_reranked
            )

        per_query_results = []
        for subquery, entity in routed_eval.compare_rewrite_subqueries_with_entities(
            rewrite,
            include_merged=self.args.compare_rewrite_include_merged,
        ):
            subquery_hybrid = routed_eval.recall_hybrid_for_query(
                self.args,
                subquery,
                self.embedder,
                self.index,
                self.metadata,
                self.bm25_store,
                top_k=self.args.compare_rewrite_top_k,
            )
            reranked = self.reranker.rerank(
                subquery,
                subquery_hybrid,
                top_k=max(self.args.compare_rewrite_per_query_keep, self.config.compare_top_k),
            )
            per_query_results.append(routed_eval.prefer_entity_results(reranked, entity))

        quota_selected = routed_eval.interleave_rewrite_results(
            per_query_results,
            per_query_keep=self.args.compare_rewrite_per_query_keep,
        )
        return routed_eval.merge_rerank_results(
            [*coarse_guaranteed, *quota_selected, *coarse_supplemental],
            original_reranked,
            top_k=merge_top_k,
        )

    @property
    def reranker(self):
        """懒加载并复用 reranker，避免批量生成时重复加载模型。"""
        if self._reranker is None:
            self._reranker = routed_eval.build_reranker(self.args)
        return self._reranker


def normalize_retrieval_args(args: argparse.Namespace) -> argparse.Namespace:
    """补齐复用评测脚本所需的参数别名。"""
    args.max_length = args.embedding_max_length
    return args


def build_retriever(args: argparse.Namespace) -> GenerationRoutedRetriever:
    """构建生成阶段 routed 检索器。"""
    return GenerationRoutedRetriever(args)


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
        question_type = str(row.get("question_type") or "fact")
        if args.only_question_type and question_type != args.only_question_type:
            continue
        questions.append(
            {
                "question_id": str(row.get("question_id") or f"sample_{len(questions) + 1:03d}"),
                "question_type": question_type,
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
    retriever: GenerationRoutedRetriever,
    client: OpenAIChatClient | None,
    context_config: ContextFormatConfig,
    args: argparse.Namespace,
    dry_run: bool,
) -> dict:
    """完成一条问题的检索、prompt 构造和回答生成。"""
    routed = retriever.retrieve_question(question)
    formatted = format_contexts(
        routed.results,
        context_config,
        query=question["query"],
        question_type=routed.question_type,
    )
    if args.summary_evidence_pack and routed.question_type == "summary":
        evidence_pack = build_summary_evidence_pack(
            question["query"],
            formatted,
            SummaryEvidenceConfig(
                max_points_per_context=args.summary_evidence_points_per_context,
                max_total_chars=args.summary_evidence_max_chars,
            ),
        )
        messages = build_summary_evidence_messages(question["query"], evidence_pack)
        context_text = evidence_pack
        generation_mode = "summary_evidence_pack"
    else:
        messages = build_answer_messages(question["query"], routed.question_type, formatted.text)
        context_text = formatted.text
        generation_mode = "default"
    answer = "" if dry_run else client.generate(messages)
    return {
        "question_id": question["question_id"],
        "question_type": routed.question_type,
        "query": question["query"],
        "strategy": routed.strategy,
        "generation_mode": generation_mode,
        "answer": answer,
        "dry_run": dry_run,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "references": formatted.references,
        "context_text": context_text if dry_run else "",
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
        row = generate_one(question, retriever, client, context_config, args=args, dry_run=args.dry_run)
        write_jsonl(output_path, [row])
        print(f"[{index}/{len(questions)}] wrote {question['question_id']} -> {display_path(output_path)}")
        if row["answer"]:
            print(row["answer"])
        if args.sleep_seconds > 0 and index < len(questions):
            time.sleep(args.sleep_seconds)


if __name__ == "__main__":
    main()
