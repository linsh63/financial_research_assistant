#!/usr/bin/env python
"""为 compare 样本生成 LLM 检索改写缓存。"""

from __future__ import annotations

import argparse
import os
import sys
import time
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
    build_compare_rewrite_messages,
    dump_compare_rewrite,
    load_compare_rewrites,
    parse_compare_rewrite_response,
)


def parse_args() -> argparse.Namespace:
    """读取生成 compare 改写缓存所需参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", default="data/eval/financial_qa_dev.jsonl")
    parser.add_argument("--output", default="data/processed/query_rewrites/compare_gpt54mini.jsonl")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--base-url", default="", help="默认读取 OPENAI_BASE_URL。")
    parser.add_argument("--model", default="", help="默认读取 OPENAI_MODEL。")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=500)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--overwrite", action="store_true", help="覆盖已存在的输出文件。")
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析为绝对路径。"""
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def display_path(path: Path) -> str:
    """优先输出项目相对路径。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


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


def main() -> None:
    """调用 LLM 生成 compare 问题改写，并以 JSONL 缓存。"""
    args = parse_args()
    eval_path = resolve_path(args.eval)
    output_path = resolve_path(args.output)
    samples, _total_rows, _skipped = eval_base.load_eval_samples(eval_path)
    compare_samples = [sample for sample in samples if sample.question_type == "compare"]
    if args.limit > 0:
        compare_samples = compare_samples[: args.limit]
    if not compare_samples:
        raise SystemExit("没有可改写的 compare 样本。")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if args.overwrite and output_path.exists():
        output_path.unlink()
    existing = load_compare_rewrites(output_path)
    client = build_client(args)

    written = 0
    with output_path.open("a", encoding="utf-8") as f:
        for index, sample in enumerate(compare_samples, start=1):
            if sample.question_id in existing:
                print(f"[{index}/{len(compare_samples)}] skip existing {sample.question_id}")
                continue
            messages = build_compare_rewrite_messages(sample.query)
            response = client.generate(messages)
            rewrite = parse_compare_rewrite_response(
                sample.question_id,
                sample.query,
                response,
                model=client.config.model,
            )
            f.write(dump_compare_rewrite(rewrite) + "\n")
            f.flush()
            written += 1
            print(f"[{index}/{len(compare_samples)}] wrote {sample.question_id} -> {display_path(output_path)}")
            if args.sleep_seconds > 0 and index < len(compare_samples):
                time.sleep(args.sleep_seconds)

    print(f"done: wrote {written}, total cached {len(load_compare_rewrites(output_path))}")


if __name__ == "__main__":
    main()
