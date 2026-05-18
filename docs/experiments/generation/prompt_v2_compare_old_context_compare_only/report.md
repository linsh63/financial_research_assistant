# Generation Evaluation

- evaluated_at: 2026-05-19T00:08:04
- eval_file: `data/eval/financial_qa_dev.jsonl`
- pred_file: `data/generated/eval_runs/prompt_v2_compare_old_context_compare_only_answers.jsonl`
- match_level: `page`
- eval_samples: 120 / 120
- skipped_eval_rows: 0
- prediction_rows: 30

## Overall

| metric | value |
|---|---:|
| generated_rate | 25.00% |
| answer_rate | 25.00% |
| citation_rate | 25.00% |
| reference_recall | 22.92% |
| reference_hit_any | 24.17% |
| reference_hit_all | 21.67% |
| numeric_coverage | 24.84% |
| numeric_count | 106 |
| judge_correct_rate | 73.33% |
| judge_avg_score | 81.53 |
| judge_judged_count | 30 |

## By Question Type

| question_type | count | answer_rate | citation_rate | reference_recall | reference_hit_all | numeric_coverage | numeric_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| compare | 30 | 100.00% | 100.00% | 91.67% | 86.67% | 87.78% | 30 |
| fact | 70 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 68 |
| summary | 20 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 8 |

## LLM Judge

| question_type | judged | correct_rate | avg_score | avg_correctness | avg_completeness | avg_faithfulness |
|---|---:|---:|---:|---:|---:|---:|
| compare | 30 | 73.33% | 81.53 | 4.03 | 4.00 | 4.17 |

## Badcases

- `fact_001` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 比亚迪2026 Q1 营收多少
  expected: 1502.25亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['1502.25']
  judge: None
  sources: []
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
- `fact_005` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 隆基绿能 26Q1 费用率同比提升了多少？
  expected: 26Q1 费用率同比提升 8.3pct。
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['8.3']
  judge: None
  sources: []
- `fact_006` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 朗信电气电子风扇及电机总成在 2025 年的产能是多少？
  expected: 695.64 万套
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['695.64']
  judge: None
  sources: []
- `fact_007` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 林洋能源Q1毛利率是多少？
  expected: 20.72%
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['20.72%']
  judge: None
  sources: []
- `fact_008` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 麦加芯彩 2026E 归母净利润预计是多少
  expected: 272.43 百万元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['272.43']
  judge: None
  sources: []
- `fact_009` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 山高环能2025 年供暖业务实现营收多少
  expected: 3.12 亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['3.12']
  judge: None
  sources: []
- `fact_010` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 崧盛股份主业方面，2026Q1 营收为 多少
  expected: 2.75 亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['2.75']
  judge: None
  sources: []
- `fact_011` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 威贸电子近 3 个月换手率是多少？
  expected: 69.24%
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['69.24%']
  judge: None
  sources: []
- `fact_012` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 安井食品26Q1 公司毛利率为多少
  expected: 25%
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['25%']
  judge: None
  sources: []
- `fact_013` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 安琪酵母2025A净利润为多少
  expected: 15.89亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['15.89']
  judge: None
  sources: []
- `fact_014` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 珀莱雅洗护品类中OR同比增长多少
  expected: 102.19%
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['102.19%']
  judge: None
  sources: []
- `fact_015` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 东鹏饮料的“东鹏补水啦”电解质水在 2025 年营收同比增长多少
  expected: 118.99%
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['118.99%']
  judge: None
  sources: []
- `fact_016` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 格力电器2026年预计的营业收入为多少
  expected: 178,510.20百万元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['178510.20']
  judge: None
  sources: []
- `fact_017` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 贵州茅台26Q1 毛利率同比下降至多少？
  expected: 89.8%
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['89.8%']
  judge: None
  sources: []
- `fact_018` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 海尔智家2026Q1 欧洲冰箱销额份额分别同比提高多少
  expected: 1.3pct
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['1.3']
  judge: None
  sources: []
- `fact_019` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 海天味业26Q1 净利率同比增长多少
  expected: 0.5pp
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['0.5']
  judge: None
  sources: []
- `fact_020` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 海信家电北美区家电收入同比增长多少
  expected: 13%
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['13%']
  judge: None
  sources: []
- `fact_021` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 爱尔眼科归属母公司净利润是多少
  expected: 11.81 亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['11.81']
  judge: None
  sources: []
- `fact_022` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all
  query: 百奥赛图成立于哪一年
  expected: 2009
  answer: 
  reference_coverage: 0/1
  missing_numbers: []
  judge: None
  sources: []
- `fact_023` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 截至 2025 年底，百诚医药的新药研发团队硕博比例达到多少
  expected: 65.29%
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['65.29%']
  judge: None
  sources: []
- `fact_024` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 毕得医药2024A 营业收入同比增速是多少
  expected: 0.9%
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['0.9%']
  judge: None
  sources: []
- `fact_025` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 博腾股份2025年小分子原料药业务收入是多少
  expected: 30.92 亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['30.92']
  judge: None
  sources: []
- `fact_026` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 国际医学公司2025年营收是多少
  expected: 40.7 亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['40.7']
  judge: None
  sources: []
- `fact_027` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 华厦眼科2025年营业收入为多少
  expected: 41.39 亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['41.39']
  judge: None
  sources: []
- `fact_028` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 皓元医药2025年实现营收多少
  expected: 28.77亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['28.77']
  judge: None
  sources: []
- `fact_029` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 金域医学2026Q1实现归母净利润多少
  expected: 0.43 亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['0.43']
  judge: None
  sources: []
- `fact_030` fact reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 九洲药业特色原料药及中间体业务实现收入多少
  expected: 11.59 亿元
  answer: 
  reference_coverage: 0/1
  missing_numbers: ['11.59']
  judge: None
  sources: []

## Metric Notes

- `answer_rate`：生成答案非空的比例。
- `citation_rate`：答案文本中显式出现 `[资料1]` 这类引用编号的比例。
- `reference_recall` / `reference_hit_all`：用生成文件保存的 `references` 对齐评测集 ground_truth 的 source/pages。
- `numeric_coverage`：标准答案中抽出的数字在生成答案中出现的比例，只在标准答案含数字的样本上统计。
- `LLM judge`：启用 `--llm-judge` 后，由模型比较问题、标准答案和生成答案，输出正确性、完整性和忠实度评分。
- 当前 judge 主要判断答案与 ground truth 的一致性；是否完全被原文支撑仍需结合引用覆盖和人工抽查。
