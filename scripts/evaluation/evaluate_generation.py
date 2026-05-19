#!/usr/bin/env python
"""评估生成答案的引用覆盖、数字覆盖和基础可用性。"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

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


@dataclass
class GenerationScore:
    """保存单条生成结果的自动评测信息。"""

    question_id: str
    question_type: str
    query: str
    expected_answer: str
    generated_answer: str
    generated: bool
    dry_run: bool
    has_answer: bool
    has_citation: bool
    used_citations: list[str]
    reference_coverage: float
    reference_matched: int
    reference_total: int
    reference_hit_any: bool
    reference_hit_all: bool
    expected_numbers: list[str]
    matched_numbers: list[str]
    missing_numbers: list[str]
    numeric_coverage: float | None
    sources: list[str]
    judge: dict | None = None


def parse_args() -> argparse.Namespace:
    """读取生成评测命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval", default="data/eval/financial_qa_dev.jsonl")
    parser.add_argument("--pred", required=True, help="generate_answers.py 输出的 JSONL。")
    parser.add_argument("--output", default="docs/experiments/generation/generation_eval.md")
    parser.add_argument("--details-output", default="docs/experiments/generation/details/generation_eval.details.json")
    parser.add_argument("--only-question-type", choices=["fact", "compare", "summary"], default="", help="只评估某一类问题。")
    parser.add_argument("--badcase-limit", type=int, default=30)
    parser.add_argument("--match-level", choices=["doc", "page"], default="page")
    parser.add_argument("--llm-judge", action="store_true", help="启用 LLM judge，对答案正确性和完整性打分。")
    parser.add_argument("--judge-api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--judge-base-url", default="", help="默认读取 OPENAI_BASE_URL，缺省为 https://api.vveai.com/v1。")
    parser.add_argument("--judge-model", default="", help="默认读取 OPENAI_JUDGE_MODEL 或 OPENAI_MODEL。")
    parser.add_argument("--judge-temperature", type=float, default=0.0)
    parser.add_argument("--judge-max-tokens", type=int, default=700)
    parser.add_argument("--judge-timeout", type=float, default=120.0)
    parser.add_argument("--judge-sleep-seconds", type=float, default=0.0)
    parser.add_argument("--judge-limit", type=int, default=0, help="最多 judge 多少条生成结果，0 表示不限制。")
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析为绝对路径。"""
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


def load_generated_rows(path: Path) -> tuple[dict[str, dict], dict[str, dict], int]:
    """读取生成结果，重复 question_id 时保留最后一次。"""
    by_id: dict[str, dict] = {}
    by_query: dict[str, dict] = {}
    total = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            total += 1
            question_id = str(row.get("question_id") or "")
            query_key = normalize_text_key(row.get("query") or "")
            if question_id:
                by_id[question_id] = row
            if query_key:
                by_query[query_key] = row
    return by_id, by_query, total


def score_generation(
    samples: list[eval_base.EvalSample],
    generated_by_id: dict[str, dict],
    generated_by_query: dict[str, dict],
    match_level: str,
) -> list[GenerationScore]:
    """逐条计算生成效果指标。"""
    scores: list[GenerationScore] = []
    for sample in samples:
        row = generated_by_id.get(sample.question_id) or generated_by_query.get(normalize_text_key(sample.query)) or {}
        answer = str(row.get("answer") or "").strip()
        references = row.get("references") or []
        ref_coverage, ref_matched, ref_total = score_references(sample, references, match_level=match_level)
        expected_numbers = extract_numbers(sample.answer)
        matched_numbers = [number for number in expected_numbers if number_in_answer(number, answer)]
        missing_numbers = [number for number in expected_numbers if number not in matched_numbers]
        numeric_coverage = len(matched_numbers) / len(expected_numbers) if expected_numbers else None
        used_citations = extract_citations(answer)
        scores.append(
            GenerationScore(
                question_id=sample.question_id,
                question_type=sample.question_type,
                query=sample.query,
                expected_answer=sample.answer,
                generated_answer=answer,
                generated=bool(row),
                dry_run=bool(row.get("dry_run")),
                has_answer=bool(answer),
                has_citation=bool(used_citations),
                used_citations=used_citations,
                reference_coverage=ref_coverage,
                reference_matched=ref_matched,
                reference_total=ref_total,
                reference_hit_any=ref_matched > 0,
                reference_hit_all=ref_total > 0 and ref_matched == ref_total,
                expected_numbers=expected_numbers,
                matched_numbers=matched_numbers,
                missing_numbers=missing_numbers,
                numeric_coverage=numeric_coverage,
                sources=top_reference_sources(references),
                judge=None,
            )
        )
    return scores


def score_references(sample: eval_base.EvalSample, references: list[dict], match_level: str) -> tuple[float, int, int]:
    """用生成结果保存的 references 计算证据覆盖率。"""
    matched = 0
    chunks = [reference_to_chunk(reference) for reference in references if isinstance(reference, dict)]
    for evidence in sample.evidences:
        if any(eval_base.evidence_matches_chunk(evidence, chunk, match_level=match_level) for chunk in chunks):
            matched += 1
    total = len(sample.evidences)
    coverage = matched / total if total else 0.0
    return coverage, matched, total


def reference_to_chunk(reference: dict) -> dict:
    """把生成结果里的 reference 转成 retrieval 评测可复用的 chunk 结构。"""
    return {
        "doc_id": reference.get("doc_id") or "",
        "source": reference.get("source") or "",
        "pages": reference.get("pages") or [],
    }


def extract_numbers(text: str) -> list[str]:
    """从标准答案中抽取需要核对的数字。"""
    normalized = remove_period_labels(normalize_number_text(text))
    numbers = re.findall(r"[-+]?\d+(?:\.\d+)?%?", normalized)
    return dedupe_keep_order(numbers)


def number_in_answer(number: str, answer: str) -> bool:
    """判断标准答案数字是否出现在生成答案中。"""
    normalized_answer = normalize_number_text(answer)
    candidates = {number, number.rstrip("%")}
    if "." in number:
        candidates.add(number.rstrip("0").rstrip("."))
    return any(candidate and candidate in normalized_answer for candidate in candidates)


def extract_citations(answer: str) -> list[str]:
    """抽取答案中显式使用的资料编号。"""
    return dedupe_keep_order(re.findall(r"\[资料\d+\]", answer))


def top_reference_sources(references: list[dict]) -> list[str]:
    """提取生成结果引用的来源文档。"""
    sources: list[str] = []
    for reference in references:
        source = str(reference.get("source") or "")
        if source and source not in sources:
            sources.append(source)
    return sources[:6]


def summarize(scores: list[GenerationScore]) -> dict[str, float]:
    """汇总生成评测指标。"""
    if not scores:
        return empty_summary()
    total = len(scores)
    numeric_scores = [score.numeric_coverage for score in scores if score.numeric_coverage is not None]
    return {
        "count": total,
        "generated_rate": average_bool(score.generated for score in scores),
        "answer_rate": average_bool(score.has_answer for score in scores),
        "citation_rate": average_bool(score.has_citation for score in scores),
        "reference_recall": sum(score.reference_coverage for score in scores) / total,
        "reference_hit_any": average_bool(score.reference_hit_any for score in scores),
        "reference_hit_all": average_bool(score.reference_hit_all for score in scores),
        "numeric_coverage": sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0.0,
        "numeric_count": len(numeric_scores),
    }


def empty_summary() -> dict[str, float]:
    """返回空指标。"""
    return {
        "count": 0,
        "generated_rate": 0.0,
        "answer_rate": 0.0,
        "citation_rate": 0.0,
        "reference_recall": 0.0,
        "reference_hit_any": 0.0,
        "reference_hit_all": 0.0,
        "numeric_coverage": 0.0,
        "numeric_count": 0,
    }


def summarize_by_type(scores: list[GenerationScore]) -> dict[str, dict[str, float]]:
    """按问题类型汇总生成指标。"""
    return {question_type: summarize(items) for question_type, items in group_scores_by_type(scores).items()}


def group_scores_by_type(scores: list[GenerationScore]) -> dict[str, list[GenerationScore]]:
    """按问题类型分组。"""
    grouped: dict[str, list[GenerationScore]] = {}
    for score in scores:
        grouped.setdefault(score.question_type, []).append(score)
    return dict(sorted(grouped.items()))


def summarize_judge(scores: list[GenerationScore]) -> dict[str, float]:
    """汇总 LLM judge 指标。"""
    judged = [score.judge for score in scores if isinstance(score.judge, dict) and not score.judge.get("error")]
    if not judged:
        return {
            "judged_count": 0.0,
            "correct_rate": 0.0,
            "avg_score": 0.0,
            "avg_correctness": 0.0,
            "avg_completeness": 0.0,
            "avg_faithfulness": 0.0,
        }
    return {
        "judged_count": float(len(judged)),
        "correct_rate": average_bool(bool(item.get("is_correct")) for item in judged),
        "avg_score": average_number(item.get("score") for item in judged),
        "avg_correctness": average_number(item.get("correctness") for item in judged),
        "avg_completeness": average_number(item.get("completeness") for item in judged),
        "avg_faithfulness": average_number(item.get("faithfulness") for item in judged),
    }


def render_report(
    args: argparse.Namespace,
    eval_path: Path,
    pred_path: Path,
    samples: list[eval_base.EvalSample],
    total_eval_rows: int,
    skipped_eval_rows: int,
    total_pred_rows: int,
    scores: list[GenerationScore],
) -> str:
    """把生成评测结果渲染成 Markdown。"""
    overall = summarize(scores)
    judge_summary = summarize_judge(scores)
    lines = [
        "# Generation Evaluation",
        "",
        f"- evaluated_at: {datetime.now().isoformat(timespec='seconds')}",
        f"- eval_file: `{display_path(eval_path)}`",
        f"- pred_file: `{display_path(pred_path)}`",
        f"- match_level: `{args.match_level}`",
        f"- eval_samples: {len(samples)} / {total_eval_rows}",
        f"- skipped_eval_rows: {skipped_eval_rows}",
        f"- prediction_rows: {total_pred_rows}",
        "",
        "## Overall",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| generated_rate | {format_rate(overall['generated_rate'])} |",
        f"| answer_rate | {format_rate(overall['answer_rate'])} |",
        f"| citation_rate | {format_rate(overall['citation_rate'])} |",
        f"| reference_recall | {format_rate(overall['reference_recall'])} |",
        f"| reference_hit_any | {format_rate(overall['reference_hit_any'])} |",
        f"| reference_hit_all | {format_rate(overall['reference_hit_all'])} |",
        f"| numeric_coverage | {format_rate(overall['numeric_coverage'])} |",
        f"| numeric_count | {int(overall['numeric_count'])} |",
    ]
    if judge_summary["judged_count"]:
        lines.extend(
            [
                f"| judge_correct_rate | {format_rate(judge_summary['correct_rate'])} |",
                f"| judge_avg_score | {judge_summary['avg_score']:.2f} |",
                f"| judge_judged_count | {int(judge_summary['judged_count'])} |",
            ]
        )
    lines.extend([
        "",
        "## By Question Type",
        "",
        "| question_type | count | answer_rate | citation_rate | reference_recall | reference_hit_all | numeric_coverage | numeric_count |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for question_type, summary in summarize_by_type(scores).items():
        lines.append(
            f"| {question_type} | {int(summary['count'])} | "
            f"{format_rate(summary['answer_rate'])} | {format_rate(summary['citation_rate'])} | "
            f"{format_rate(summary['reference_recall'])} | {format_rate(summary['reference_hit_all'])} | "
            f"{format_rate(summary['numeric_coverage'])} | {int(summary['numeric_count'])} |"
        )

    if judge_summary["judged_count"]:
        lines.extend(render_judge_summary(scores))
    lines.extend(render_badcases(scores, args.badcase_limit))
    lines.extend(render_metric_notes())
    return "\n".join(lines).rstrip() + "\n"


def render_judge_summary(scores: list[GenerationScore]) -> list[str]:
    """渲染 LLM judge 分项结果。"""
    lines = [
        "",
        "## LLM Judge",
        "",
        "| question_type | judged | correct_rate | avg_score | avg_correctness | avg_completeness | avg_faithfulness |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for question_type, items in group_scores_by_type(scores).items():
        summary = summarize_judge(items)
        if not summary["judged_count"]:
            continue
        lines.append(
            f"| {question_type} | {int(summary['judged_count'])} | "
            f"{format_rate(summary['correct_rate'])} | {summary['avg_score']:.2f} | "
            f"{summary['avg_correctness']:.2f} | {summary['avg_completeness']:.2f} | {summary['avg_faithfulness']:.2f} |"
        )
    return lines


def render_badcases(scores: list[GenerationScore], limit: int) -> list[str]:
    """渲染生成 badcase。"""
    badcases = [
        score for score in scores
        if not score.has_answer
        or not score.has_citation
        or not score.reference_hit_all
        or (score.numeric_coverage is not None and score.numeric_coverage < 1.0)
        or judge_failed(score)
    ]
    lines = ["", "## Badcases", ""]
    if not badcases:
        lines.extend(["No badcases.", ""])
        return lines
    for score in badcases[:limit]:
        reasons = badcase_reasons(score)
        lines.extend(
            [
                f"- `{score.question_id}` {score.question_type} reasons={','.join(reasons)}",
                f"  query: {score.query}",
                f"  expected: {score.expected_answer}",
                f"  answer: {shorten(score.generated_answer, 220)}",
                f"  reference_coverage: {score.reference_matched}/{score.reference_total}",
                f"  missing_numbers: {score.missing_numbers}",
                f"  judge: {shorten(json.dumps(score.judge, ensure_ascii=False), 260) if score.judge else None}",
                f"  sources: {score.sources}",
            ]
        )
    lines.append("")
    return lines


def badcase_reasons(score: GenerationScore) -> list[str]:
    """说明一条样本为什么是 badcase。"""
    reasons: list[str] = []
    if not score.generated:
        reasons.append("missing_prediction")
    if score.dry_run:
        reasons.append("dry_run")
    if not score.has_answer:
        reasons.append("empty_answer")
    if not score.has_citation:
        reasons.append("no_citation")
    if not score.reference_hit_all:
        reasons.append("reference_not_hit_all")
    if score.numeric_coverage is not None and score.numeric_coverage < 1.0:
        reasons.append("number_miss")
    if judge_failed(score):
        reasons.append("judge_failed")
    return reasons


def judge_failed(score: GenerationScore) -> bool:
    """判断 LLM judge 是否认为答案没有通过。"""
    if not isinstance(score.judge, dict) or score.judge.get("error"):
        return False
    return not bool(score.judge.get("is_correct"))


def render_metric_notes() -> list[str]:
    """解释第一版自动指标的含义。"""
    return [
        "## Metric Notes",
        "",
        "- `answer_rate`：生成答案非空的比例。",
        "- `citation_rate`：答案文本中显式出现 `[资料1]` 这类引用编号的比例。",
        "- `reference_recall` / `reference_hit_all`：用生成文件保存的 `references` 对齐评测集 ground_truth 的 source/pages。",
        "- `numeric_coverage`：标准答案中抽出的数字在生成答案中出现的比例，只在标准答案含数字的样本上统计。",
        "- `LLM judge`：启用 `--llm-judge` 后，由模型比较问题、标准答案和生成答案，输出正确性、完整性和忠实度评分。",
        "- 当前 judge 主要判断答案与 ground truth 的一致性；是否完全被原文支撑仍需结合引用覆盖和人工抽查。",
        "",
    ]


def run_llm_judge(args: argparse.Namespace, scores: list[GenerationScore]) -> None:
    """按需调用 LLM judge，并把结果写回 score.judge。"""
    if not args.llm_judge:
        return
    client = build_judge_client(args)
    judged_count = 0
    for score in scores:
        if not score.generated or score.dry_run or not score.has_answer:
            continue
        if args.judge_limit > 0 and judged_count >= args.judge_limit:
            break
        score.judge = judge_one(client, args, score)
        judged_count += 1
        print(f"judged {judged_count}: {score.question_id}")
        if args.judge_sleep_seconds > 0:
            time.sleep(args.judge_sleep_seconds)


def build_judge_client(args: argparse.Namespace) -> OpenAIChatClient:
    """构建 OpenAI-compatible judge 客户端。"""
    api_key = os.getenv(args.judge_api_key_env, "")
    base_url = args.judge_base_url or os.getenv("OPENAI_BASE_URL", "https://api.vveai.com/v1")
    model = args.judge_model or os.getenv("OPENAI_JUDGE_MODEL") or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
    return OpenAIChatClient(
        OpenAIChatConfig(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=args.judge_temperature,
            max_tokens=args.judge_max_tokens,
            timeout=args.judge_timeout,
        )
    )


def judge_one(client: OpenAIChatClient, args: argparse.Namespace, score: GenerationScore) -> dict:
    """用 LLM judge 评估单条生成答案。"""
    messages = build_judge_messages(score)
    try:
        raw = client.generate(messages)
        parsed = parse_judge_json(raw)
        parsed["raw"] = raw
        parsed["model"] = args.judge_model or os.getenv("OPENAI_JUDGE_MODEL") or os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
        return normalize_judge_result(parsed)
    except Exception as exc:  # noqa: BLE001
        return {"error": type(exc).__name__, "message": str(exc)}


def build_judge_messages(score: GenerationScore) -> list[dict[str, str]]:
    """构造 LLM judge prompt。"""
    system = """你是严格的金融问答评测员。
你只根据问题、标准答案和生成答案进行评分。
不要因为生成答案说得更长就给高分；只看是否与标准答案一致、是否完整、是否有明显编造。
必须只输出一个 JSON 对象，不要输出 Markdown。"""
    user = f"""请评估下面的生成答案。

评分规则：
- correctness：0-5，生成答案与标准答案是否一致。
- completeness：0-5，生成答案是否覆盖标准答案的关键点。
- faithfulness：0-5，生成答案是否避免无依据扩展或编造。若答案加入标准答案没有的信息但不影响结论，可轻微扣分。
- score：0-100，综合分。
- is_correct：布尔值，答案核心结论正确且无重大遗漏时为 true。

请输出 JSON，字段必须包含：
{{"is_correct": true/false, "score": 0-100, "correctness": 0-5, "completeness": 0-5, "faithfulness": 0-5, "reason": "简短中文原因"}}

问题类型：{score.question_type}
问题：{score.query}
标准答案：{score.expected_answer}
生成答案：{score.generated_answer}
规则评测提示：
- 是否有引用：{score.has_citation}
- 引用证据覆盖：{score.reference_matched}/{score.reference_total}
- 标准答案数字：{score.expected_numbers}
- 缺失数字：{score.missing_numbers}
"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def parse_judge_json(raw: str) -> dict:
    """从 judge 返回中解析 JSON 对象。"""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("judge 返回不是 JSON object")
    return data


def normalize_judge_result(data: dict) -> dict:
    """规范化 judge 字段类型和范围。"""
    normalized = dict(data)
    normalized["is_correct"] = bool(normalized.get("is_correct"))
    normalized["score"] = clamp_float(normalized.get("score"), 0.0, 100.0)
    normalized["correctness"] = clamp_float(normalized.get("correctness"), 0.0, 5.0)
    normalized["completeness"] = clamp_float(normalized.get("completeness"), 0.0, 5.0)
    normalized["faithfulness"] = clamp_float(normalized.get("faithfulness"), 0.0, 5.0)
    normalized["reason"] = str(normalized.get("reason") or "")
    return normalized


def write_details(path: Path, scores: list[GenerationScore]) -> None:
    """写入逐样本详情。"""
    payload = {
        "scores": [asdict(score) for score in scores],
        "summary": summarize(scores),
        "judge_summary": summarize_judge(scores),
        "by_type": summarize_by_type(scores),
        "judge_by_type": {question_type: summarize_judge(items) for question_type, items in group_scores_by_type(scores).items()},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def average_bool(values: Iterable[bool]) -> float:
    """计算布尔值均值。"""
    items = list(values)
    if not items:
        return 0.0
    return sum(1 for item in items if item) / len(items)


def average_number(values: Iterable[object]) -> float:
    """计算数值均值，跳过不可解析项。"""
    numbers: list[float] = []
    for value in values:
        try:
            numbers.append(float(value))
        except (TypeError, ValueError):
            continue
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def clamp_float(value: object, lower: float, upper: float) -> float:
    """把数值限制到指定范围。"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = lower
    return max(lower, min(upper, number))


def format_rate(value: float) -> str:
    """把 0-1 浮点数格式化为百分比。"""
    return f"{value * 100:.2f}%"


def normalize_text_key(text: str) -> str:
    """规范化 query 文本，便于 smoke test 按 query 对齐。"""
    return re.sub(r"\s+", "", str(text)).lower()


def normalize_number_text(text: str) -> str:
    """规范化答案文本，便于数字匹配。"""
    return str(text).replace(",", "").replace("，", "").replace("％", "%")


def remove_period_labels(text: str) -> str:
    """去掉 2025A、26Q1 这类时间口径，避免误当成答案数字。"""
    text = re.sub(r"\b20\d{2}[A-Za-z]?\b", " ", text)
    text = re.sub(r"\b\d{2}Q[1-4]\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b20\d{2}Q[1-4]\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bQ[1-4]\b", " ", text, flags=re.IGNORECASE)
    return text


def dedupe_keep_order(items: list[str]) -> list[str]:
    """按原顺序去重。"""
    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def shorten(text: str, max_chars: int) -> str:
    """截断过长文本用于 badcase 展示。"""
    text = " ".join(str(text).split())
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def main() -> None:
    """执行生成效果评测。"""
    args = parse_args()
    eval_path = resolve_path(args.eval)
    pred_path = resolve_path(args.pred)
    output_path = resolve_path(args.output)
    details_path = resolve_path(args.details_output)

    samples, total_rows, skipped = eval_base.load_eval_samples(eval_path)
    if args.only_question_type:
        samples = [sample for sample in samples if sample.question_type == args.only_question_type]
    generated_by_id, generated_by_query, total_pred_rows = load_generated_rows(pred_path)
    scores = score_generation(samples, generated_by_id, generated_by_query, match_level=args.match_level)
    run_llm_judge(args, scores)
    report = render_report(args, eval_path, pred_path, samples, total_rows, skipped, total_pred_rows, scores)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    write_details(details_path, scores)
    print(report)
    print(f"wrote: {display_path(output_path)}")
    print(f"wrote: {display_path(details_path)}")


if __name__ == "__main__":
    main()
