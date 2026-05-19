# Generation Evaluation

- evaluated_at: 2026-05-19T15:57:20
- eval_file: `data/eval/financial_qa_dev.jsonl`
- pred_file: `data/generated/dry_runs/summary_evidence_pack_smoke_v3.jsonl`
- match_level: `page`
- eval_samples: 20 / 120
- skipped_eval_rows: 0
- prediction_rows: 1

## Overall

| metric | value |
|---|---:|
| generated_rate | 5.00% |
| answer_rate | 0.00% |
| citation_rate | 0.00% |
| reference_recall | 2.50% |
| reference_hit_any | 5.00% |
| reference_hit_all | 0.00% |
| numeric_coverage | 0.00% |
| numeric_count | 8 |

## By Question Type

| question_type | count | answer_rate | citation_rate | reference_recall | reference_hit_all | numeric_coverage | numeric_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| summary | 20 | 0.00% | 0.00% | 2.50% | 0.00% | 0.00% | 8 |

## Badcases

- `summary_001` summary reasons=dry_run,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  expected: 主要方向包括：坚持清洁低碳、安全充裕、经济高效、供需协同、灵活智能的基本原则，2024—2027年重点开展9项专项行动，提升电网对清洁能源的接纳、配置、调控能力；健全煤电、抽水蓄能、新型储能等调节性资源容量电价机制，完善体现分时价值差异的零售市场价格机制；突破新能源高效发电利用、系统灵活调节、电网高效仿真和稳定运行控制、智能化调控等技术；通过调节能力建设优化，支撑2025—2027年年均新增2亿千瓦以上新能源合理消纳利用，全国新能源利用率不低于90%；推动新型储能到2027年基本实现规模化、市场化发展，全国装机规模达到1.8亿千瓦以上。
  answer: 
  reference_coverage: 2/4
  missing_numbers: ['2024', '2027', '9', '2025', '2', '90%', '1.8']
  judge: None
  sources: ['data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020210421528000000606.pdf', 'data/raw/policy/P020240806534738672970.pdf']
- `summary_002` summary reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: 新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？
  expected: 新型储能被定位为支撑新型电力系统的重要技术和基础装备。目标上，到2025年实现从商业化初期向规模化发展转变、装机规模达3000万千瓦以上，到2030年实现全面市场化发展；专项行动进一步提出到2027年基本实现规模化、市场化发展。应用场景上，鼓励电源侧、电网侧、用户侧多元发展，拓展“新能源+储能”、智能微电网、虚拟电厂等场景。技术上，坚持多元化路线，推动锂离子电池规模化应用，推动压缩空气、液流电池、钠离子电池、飞轮、氢储能、热储能等试点示范和商业化发展。市场机制上，推动储能作为独立主体参与电力市场、辅助服务市场，完善容量电价、分时电价和成本疏导机制，并健全标准体系、并网流程和安全监管。
  answer: 
  reference_coverage: 0/5
  missing_numbers: ['2025', '3000', '2030', '2027']
  judge: None
  sources: []
- `summary_003` summary reasons=missing_prediction,empty_answer,no_citation,reference_not_hit_all,number_miss
  query: “十四五”可再生能源规划和氢能规划分别怎样服务能源绿色低碳转型？
  expected: 可再生能源规划提出，加快发展可再生能源、实施可再生能源替代行动，是推进能源革命和构建清洁低碳、安全高效能源体系的重大举措；到2025年，可再生能源消费总量达到10亿吨标准煤左右，年发电量达到3.3万亿千瓦时左右，全国可再生能源电力总量消纳责任权重达到33%左右，非水电消纳责任权重达到18%左右。规划还要求推动绿色直供电、可再生能源供暖、非电直接利用和高比例可再生能源应用示范，健全消纳责任权重和长效机制。氢能规划将氢能界定为来源丰富、绿色低碳、应用广泛的二次能源，要求构建清洁化、低碳化、低成本的多元制氢体系，开展可再生能源制氢示范，构建安全、稳定、高效的氢能供应网络，并形成“1+N”政策体系。
  answer: 
  reference_coverage: 0/3
  missing_numbers: ['2025', '10', '3.3', '33%', '18%', '1']
  judge: None
  sources: []

## Metric Notes

- `answer_rate`：生成答案非空的比例。
- `citation_rate`：答案文本中显式出现 `[资料1]` 这类引用编号的比例。
- `reference_recall` / `reference_hit_all`：用生成文件保存的 `references` 对齐评测集 ground_truth 的 source/pages。
- `numeric_coverage`：标准答案中抽出的数字在生成答案中出现的比例，只在标准答案含数字的样本上统计。
- `LLM judge`：启用 `--llm-judge` 后，由模型比较问题、标准答案和生成答案，输出正确性、完整性和忠实度评分。
- 当前 judge 主要判断答案与 ground truth 的一致性；是否完全被原文支撑仍需结合引用覆盖和人工抽查。
