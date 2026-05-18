# Generation Evaluation

- evaluated_at: 2026-05-18T17:29:28
- eval_file: `data/eval/financial_qa_dev.jsonl`
- pred_file: `data/generated/smoke_tests/routed_answer_smoke.jsonl`
- match_level: `page`
- eval_samples: 120 / 120
- skipped_eval_rows: 0
- prediction_rows: 1

## Overall

| metric | value |
|---|---:|
| generated_rate | 0.83% |
| answer_rate | 0.83% |
| citation_rate | 0.83% |
| reference_recall | 0.83% |
| reference_hit_any | 0.83% |
| reference_hit_all | 0.83% |
| numeric_coverage | 0.94% |
| numeric_count | 106 |

## By Question Type

| question_type | count | answer_rate | citation_rate | reference_recall | reference_hit_all | numeric_coverage | numeric_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| compare | 30 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 30 |
| fact | 70 | 1.43% | 1.43% | 1.43% | 1.43% | 1.47% | 68 |
| summary | 20 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 8 |

## Badcases

- `fact_002` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 恩捷股份2025A 的 P/E 是多少？
  expected: 514.94 倍。
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['514.94']
  judge: None
  sources: []
- `fact_003` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 格林美一季度公司回收钨资源销售收入是多少？
  expected: 14.19 亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['14.19']
  judge: None
  sources: []
- `fact_004` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 国轩高科 2024A 的 PB 估值是多少倍
  expected: 2.7 倍。
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['2.7']
  judge: None
  sources: []

## Metric Notes

- `answer_rate`：生成答案非空的比例。
- `citation_rate`：答案文本中显式出现 `[资料1]` 这类引用编号的比例。
- `reference_recall` / `reference_hit_all`：用生成文件保存的 `references` 对齐评测集 ground_truth 的 source/pages。
- `numeric_coverage`：标准答案中抽出的数字在生成答案中出现的比例，只在标准答案含数字的样本上统计。
- `LLM judge`：启用 `--llm-judge` 后，由模型比较问题、标准答案和生成答案，输出正确性、完整性和忠实度评分。
- 当前 judge 主要判断答案与 ground truth 的一致性；是否完全被原文支撑仍需结合引用覆盖和人工抽查。
