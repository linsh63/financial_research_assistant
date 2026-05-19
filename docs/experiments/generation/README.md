# 生成效果评测

本目录保存回答生成阶段的自动评测结果。

## 目录结构

- `smoke/`：单条问题的冒烟测试报告。
- `details/`：逐样本评测详情 JSON。
- `routed_gpt54mini_full/`：GPT-5.4 mini 全量生成评测。
- `routed_v17_deepseek_full/`：DeepSeek 全量生成规则评测。
- `routed_v17_deepseek_full_judge/`：DeepSeek 全量生成 LLM judge。
- `badcase_analysis/`：生成阶段 badcase 分析。

## 当前正式结果

当前正式生成链路使用：

```text
检索：17_routed_compare_raw_entity_slots
生成：默认 prompt 约束
模型：DeepSeek deepseek-chat
```

全量 120 条结果：

| metric | value |
|---|---:|
| answer_rate | 100.00% |
| citation_rate | 97.50% |
| reference_hit_all | 93.33% |
| numeric_coverage | 86.31% |
| judge_correct_rate | 80.00% |
| judge_avg_score | 86.62 |

按题型：

| question_type | judge_correct_rate | judge_avg_score | reference_hit_all |
|---|---:|---:|---:|
| fact | 82.86% | 86.07 | 97.14% |
| compare | 93.33% | 96.17 | 100.00% |
| summary | 50.00% | 74.25 | 70.00% |

相关文档：

- `routed_v17_deepseek_full/report.md`
- `routed_v17_deepseek_full_judge/report.md`
- `badcase_analysis/report.md`

说明：`summary_evidence_pack_deepseek/` 是一次探索性实验，暂不作为正式链路。

## 当前自动指标

- `answer_rate`：生成答案非空的比例。
- `citation_rate`：答案文本中出现 `[资料1]` 这类显式引用的比例。
- `reference_recall` / `reference_hit_all`：生成文件中的 `references` 是否覆盖评测集 ground_truth 的 source/pages。
- `numeric_coverage`：标准答案中的关键数字是否出现在生成答案中。

这些规则指标用于发现硬错误，例如未生成、未引用、引用页码未覆盖、关键数字缺失。

## LLM judge

`evaluate_generation.py` 支持可选的 LLM judge。启用后，脚本会把问题、标准答案、生成答案和规则评测提示发给 judge 模型，并要求返回 JSON：

- `is_correct`
- `score`
- `correctness`
- `completeness`
- `faithfulness`
- `reason`

示例：

```bash
.venv-brew/bin/python scripts/evaluation/evaluate_generation.py \
  --eval data/eval/financial_qa_dev.jsonl \
  --pred data/generated/eval_runs/routed_answers_full_2026-05-18.jsonl \
  --output docs/experiments/generation/routed_gpt54mini_full_judge/report.md \
  --details-output docs/experiments/generation/details/routed_gpt54mini_full_judge/details.json \
  --llm-judge \
  --judge-model gpt-5.4-mini
```

LLM judge 主要判断生成答案与 ground truth 是否一致。它不能完全替代人工检查，尤其是汇总型问题仍需要抽查答案是否真正被原文支撑。
