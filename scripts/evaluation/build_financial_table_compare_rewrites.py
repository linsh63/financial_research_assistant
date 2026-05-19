#!/usr/bin/env python
"""为财务预测表述生成 compare 检索改写缓存。

本脚本保留已有 compare rewrite，只对“预计 2026 年营收/营业收入”这类问题
调用一次 LLM API 批量归一化为更贴近财务表的检索表述，例如：

    普蕊斯 2026E 营收 营业收入 主营业务收入
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import replace
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

from financial_report_rag.generation.llm_client import OpenAIChatClient, OpenAIChatConfig  # noqa: E402
from financial_report_rag.retrieval.compare_rewriter import (  # noqa: E402
    CompareQueryRewrite,
    dump_compare_rewrite,
    extract_json_object,
    load_compare_rewrites,
    normalize_string_list,
)


FINANCIAL_REVENUE_ASPECT = "2026E 营收/营业收入"
FINANCIAL_REVENUE_QUERY_TAIL = "2026E 营收 营业收入 主营业务收入"


def parse_args() -> argparse.Namespace:
    """读取财务表述改写参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", default="data/eval/financial_qa_dev.jsonl")
    parser.add_argument("--base-rewrite", default="data/processed/query_rewrites/compare_gpt54mini.jsonl")
    parser.add_argument("--output", default="data/processed/query_rewrites/compare_financial_table_gpt54mini.jsonl")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--base-url", default="", help="默认读取 OPENAI_BASE_URL。")
    parser.add_argument("--model", default="", help="默认读取 OPENAI_MODEL。")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="只展示会改写哪些问题，不调用 API。")
    parser.add_argument(
        "--fallback-without-api",
        action="store_true",
        help="不调用 API，直接按同一目标格式生成可复现实验用 rewrite。",
    )
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析为绝对路径。"""
    path = Path(path_text)
    return path if path.is_absolute() else ROOT / path


def display_path(path: Path) -> str:
    """优先输出项目相对路径。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def is_financial_forecast_revenue_compare(sample: eval_base.EvalSample) -> bool:
    """识别需要改成财务预测表字段的 compare 问题。"""
    query = sample.query
    if sample.question_type != "compare":
        return False
    if "预计" not in query:
        return False
    if "2026" not in query:
        return False
    if "Q1" in query or "一季度" in query:
        return False
    return "营收" in query or "营业收入" in query


def build_batch_messages(samples: list[eval_base.EvalSample]) -> list[dict[str, str]]:
    """构造一次性批量改写 prompt。"""
    items = [{"question_id": sample.question_id, "query": sample.query} for sample in samples]
    system_prompt = (
        "你是金融研报 RAG 系统中的检索查询改写器，只负责提升召回。"
        "请把财务预测类 compare 问题改写成贴近研报预测表字段的检索 query。"
        "不要回答问题，不要引入外部知识，不要改变公司名称。"
        "必须只输出一个 JSON 对象。"
    )
    user_prompt = f"""
下面的问题都属于“预计/预测 2026 年营收或营业收入”的 compare 检索改写任务。

改写规则：
- 年份口径统一写成：2026E
- 指标召回词统一包含：营收、营业收入、主营业务收入
- 不要在 query 中加入“（百万元）”或“(百万元)”。
- 每个 sub_queries 必须分别面向一个公司，格式尽量为：“公司名 2026E 营收 营业收入 主营业务收入”
- merged_query 保留两个公司名，并包含 “2026E 营收 营业收入 主营业务收入 对比”
- entities 必须从原问题中抽取，不要改公司名。
- aspect 必须写成：2026E 营收/营业收入

待改写问题 JSON：
{json.dumps(items, ensure_ascii=False, indent=2)}

请输出 JSON：
{{
  "rewrites": [
    {{
      "question_id": "compare_xxx",
      "entities": ["公司A", "公司B"],
      "aspect": "2026E 营收/营业收入",
      "sub_queries": [
        "公司A 2026E 营收 营业收入 主营业务收入",
        "公司B 2026E 营收 营业收入 主营业务收入"
      ],
      "merged_query": "公司A 公司B 2026E 营收 营业收入 主营业务收入 对比"
    }}
  ]
}}
""".strip()
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_client(args: argparse.Namespace) -> OpenAIChatClient:
    """构建 OpenAI-compatible 客户端。"""
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


def parse_batch_response(
    response_text: str,
    samples_by_id: dict[str, eval_base.EvalSample],
    model: str,
) -> dict[str, CompareQueryRewrite]:
    """解析批量改写结果。"""
    data = extract_json_object(response_text)
    raw_items = data.get("rewrites")
    if not isinstance(raw_items, list):
        return {}

    rewritten_at = datetime.now().isoformat(timespec="seconds")
    rewrites: dict[str, CompareQueryRewrite] = {}
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        question_id = str(item.get("question_id") or "").strip()
        sample = samples_by_id.get(question_id)
        if sample is None:
            continue
        entities = normalize_string_list(item.get("entities"))[:2]
        aspect = str(item.get("aspect") or FINANCIAL_REVENUE_ASPECT).strip()
        sub_queries = normalize_string_list(item.get("sub_queries"))
        merged_query = str(item.get("merged_query") or "").strip()
        if len(entities) >= 2 and len(sub_queries) < 2:
            sub_queries = [f"{entity} {FINANCIAL_REVENUE_QUERY_TAIL}" for entity in entities]
        if len(entities) >= 2 and not merged_query:
            merged_query = f"{entities[0]} {entities[1]} {FINANCIAL_REVENUE_QUERY_TAIL} 对比"
        rewrites[question_id] = CompareQueryRewrite(
            question_id=question_id,
            original_query=sample.query,
            entities=entities,
            aspect=aspect,
            sub_queries=sub_queries,
            merged_query=merged_query,
            model=model,
            raw_response=response_text,
            rewritten_at=rewritten_at,
        )
    return rewrites


def fallback_rewrite_from_base(
    base: CompareQueryRewrite,
    sample: eval_base.EvalSample,
    model: str,
) -> CompareQueryRewrite:
    """API 返回不完整时，用旧实体生成保守财务表述改写。"""
    entities = base.entities[:2]
    sub_queries = [f"{entity} {FINANCIAL_REVENUE_QUERY_TAIL}" for entity in entities]
    merged_query = f"{' '.join(entities)} {FINANCIAL_REVENUE_QUERY_TAIL} 对比".strip()
    raw_response = json.dumps(
        {
            "mode": model,
            "source": "fallback_without_api",
            "rule": "normalize_forecast_revenue_without_unit",
            "entities": entities,
            "aspect": FINANCIAL_REVENUE_ASPECT,
            "sub_queries": sub_queries,
            "merged_query": merged_query,
        },
        ensure_ascii=False,
    )
    return replace(
        base,
        original_query=sample.query,
        aspect=FINANCIAL_REVENUE_ASPECT,
        sub_queries=sub_queries,
        merged_query=merged_query,
        model=model,
        raw_response=raw_response,
        rewritten_at=datetime.now().isoformat(timespec="seconds"),
    )


def write_rewrites(path: Path, rewrites: dict[str, CompareQueryRewrite]) -> None:
    """按 question_id 排序写出完整 rewrite JSONL。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for question_id in sorted(rewrites):
            f.write(dump_compare_rewrite(rewrites[question_id]) + "\n")


def main() -> None:
    """读取旧 rewrite，批量归一化财务预测题，并输出新 rewrite 文件。"""
    args = parse_args()
    eval_path = resolve_path(args.eval)
    base_path = resolve_path(args.base_rewrite)
    output_path = resolve_path(args.output)
    if output_path.exists() and not args.overwrite and not args.dry_run:
        raise SystemExit(f"输出文件已存在，请加 --overwrite：{display_path(output_path)}")

    samples, _total_rows, _skipped = eval_base.load_eval_samples(eval_path)
    targets = [sample for sample in samples if is_financial_forecast_revenue_compare(sample)]
    base_rewrites = load_compare_rewrites(base_path)
    print(f"base rewrites: {len(base_rewrites)}")
    print(f"targets: {len(targets)}")
    for sample in targets:
        print(f"- {sample.question_id}: {sample.query}")
    if args.dry_run:
        return

    api_rewrites: dict[str, CompareQueryRewrite]
    model_name: str
    if args.fallback_without_api:
        api_rewrites = {}
        model_name = "financial_table_rule_fallback"
    else:
        client = build_client(args)
        model_name = client.config.model
        response = client.generate(build_batch_messages(targets))
        api_rewrites = parse_batch_response(
            response,
            samples_by_id={sample.question_id: sample for sample in targets},
            model=model_name,
        )

    merged_rewrites = dict(base_rewrites)
    for sample in targets:
        base = base_rewrites.get(sample.question_id)
        if sample.question_id in api_rewrites:
            merged_rewrites[sample.question_id] = api_rewrites[sample.question_id]
        elif base is not None:
            merged_rewrites[sample.question_id] = fallback_rewrite_from_base(base, sample, model_name)
        else:
            raise RuntimeError(f"缺少 {sample.question_id} 的基础 rewrite，且 API 未返回该项。")

    write_rewrites(output_path, merged_rewrites)
    print(f"api rewrites: {len(api_rewrites)}")
    print(f"wrote: {display_path(output_path)}")


if __name__ == "__main__":
    main()
