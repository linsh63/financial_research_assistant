# Generation Evaluation

- evaluated_at: 2026-05-18T19:22:40
- eval_file: `data/eval/badcase_prompt_v2_subset.jsonl`
- pred_file: `data/generated/eval_runs/prompt_v2_context_fix_badcase_subset_answers.jsonl`
- match_level: `page`
- eval_samples: 12 / 12
- skipped_eval_rows: 0
- prediction_rows: 12

## Overall

| metric | value |
|---|---:|
| generated_rate | 100.00% |
| answer_rate | 100.00% |
| citation_rate | 100.00% |
| reference_recall | 80.00% |
| reference_hit_any | 100.00% |
| reference_hit_all | 58.33% |
| numeric_coverage | 66.47% |
| numeric_count | 12 |
| judge_correct_rate | 41.67% |
| judge_avg_score | 64.83 |
| judge_judged_count | 12 |

## By Question Type

| question_type | count | answer_rate | citation_rate | reference_recall | reference_hit_all | numeric_coverage | numeric_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| compare | 4 | 100.00% | 100.00% | 75.00% | 50.00% | 77.08% | 4 |
| fact | 5 | 100.00% | 100.00% | 100.00% | 100.00% | 80.00% | 5 |
| summary | 3 | 100.00% | 100.00% | 53.33% | 0.00% | 29.76% | 3 |

## LLM Judge

| question_type | judged | correct_rate | avg_score | avg_correctness | avg_completeness | avg_faithfulness |
|---|---:|---:|---:|---:|---:|---:|
| compare | 4 | 25.00% | 43.50 | 2.00 | 2.00 | 3.75 |
| fact | 5 | 80.00% | 83.20 | 4.00 | 4.00 | 4.80 |
| summary | 3 | 0.00% | 62.67 | 3.00 | 2.67 | 2.00 |

## Badcases

- `fact_036` fact reasons=number_miss,judge_failed
  query: 截至 2025 年末，金地集团有息负债多少
  expected: 672亿元
  answer: 直接答案：根据现有资料无法确定“截至 2025 年末，金地集团有息负债”的具体金额；资料仅能看到“截至2025年末，金地集团有息负债中短期有息负债占比为61%，长期有息负债占比为39%”，但未给出有息负债总额。 依据：[资料1]
  reference_coverage: 1/1
  missing_numbers: ['672']
  judge: {"is_correct": false, "score": 18.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 4.0, "reason": "标准答案是672亿元，但生成答案未给出总额，反而称无法确定；仅提供了占比信息，未覆盖关键数字，因此不正确且不完整。", "raw": "{\"is_correct\":false,\"score\":18,\"correctness\":0,\"completeness\":0,\"faithful...
  sources: ['data/raw/real_estate/JDJT.pdf', 'data/raw/real_estate/HFGF.pdf']
- `compare_002` compare reasons=reference_not_hit_all,number_miss,judge_failed
  query: 泸州老窖 vs 五粮液，哪家公司的2025年营业总收入更高？
  expected: 五粮液。泸州老窖2025年公司实现营业总收入 257.3 亿元，五粮液2025年公司实现营收 405.29亿元。
  answer: - 对象A：泸州老窖 2025年营业总收入为 **257.3亿元**，口径为“营业总收入”，时间为“2025年/2025A”，引用：[资料3]。 - 对象B：五粮液 资料中**未提供**“2025年营业总收入”这一同口径数字；[资料1] 仅给出了五粮液的估值表信息，未见营业总收入数据。引用：[资料1]。 结论：根据现有资料，**无法直接比较泸州老窖与五粮液2025年营业总收入高低**，因为五粮液的2025年营业总收入缺失。
  reference_coverage: 1/2
  missing_numbers: ['405.29']
  judge: {"is_correct": false, "score": 24.0, "correctness": 1.0, "completeness": 1.0, "faithfulness": 4.0, "reason": "生成答案承认五粮液2025年营业总收入缺失，未给出标准答案中的结论“五粮液更高”，属于核心结论错误且遗漏关键数字405.29亿元；但未明显编造数值，整体较为保守。", "raw": "{\"is_correct\":false,\"score\":24,\"correctness\":1,\"com...
  sources: ['data/raw/consumer/SXFJ.pdf', 'data/raw/consumer/LZLJ.pdf']
- `compare_003` compare reasons=reference_not_hit_all,number_miss,judge_failed
  query: 千禾味业 vs 神农集团，哪家公司的26Q1营收 更高
  expected: 神农集团。在26Q1，千禾味业实现营收 8.2 亿元，神农集团实现营收 13.22 亿元
  answer: - 对象A：千禾味业，26Q1 实现营收 **8.2亿元**，口径为“26Q1公司实现营收”，引用：[资料1] - 对象B：神农集团，**根据现有资料无法确定**其“26Q1营收”数值；当前可用资料中未提供神农集团26Q1营收这一同口径数据。引用：[资料2] 结论：**根据现有资料无法判断千禾味业 vs 神农集团哪家公司的26Q1营收更高**，因为资料中只明确给出了千禾味业的26Q1营收，未提供神农集团对应的26Q1营收数据。[资料1]...
  reference_coverage: 1/2
  missing_numbers: ['13.22']
  judge: {"is_correct": false, "score": 28.0, "correctness": 1.0, "completeness": 1.0, "faithfulness": 3.0, "reason": "生成答案未给出标准答案结论，反而称无法判断；且缺少神农集团26Q1营收13.22亿元这一关键数据，属于核心遗漏。", "raw": "{\"is_correct\":false,\"score\":28,\"correctness\":1,\"completeness\":1,\"faithfuln...
  sources: ['data/raw/consumer/QHWY.pdf', 'data/raw/consumer/HTWY.pdf']
- `compare_029` compare reasons=number_miss,judge_failed
  query: 保利发展 vs 华发股份，哪家公司2025年实现营收更高
  expected: 保利发展。保利发展2025年公司实现营业收入308144百万元，华发股份2025年实现收入834.3亿元
  answer: - 对象A（保利发展）：**2025A 营业总收入 308,144 百万元**，口径为“营业总收入”，时间为“2025A” [资料1] - 对象B（华发股份）：**2025 年营业收入 512.4 亿元**，口径为“营业收入”，时间为“2025” [资料4] 结论：**根据现有资料，保利发展和华发股份都提供了 2025 年营收数据，但两者口径不完全一致（“营业总收入” vs “营业收入”），且单位也不同，无法直接判断哪家公司 2025...
  reference_coverage: 2/2
  missing_numbers: ['834.3']
  judge: {"is_correct": false, "score": 22.0, "correctness": 1.0, "completeness": 1.0, "faithfulness": 3.0, "reason": "标准答案明确为保利发展营收更高；生成答案却因口径/单位不同而给出“无法直接判断”，结论错误。虽提到保利发展营收数值，但华发股份数字与标准答案不一致，且未给出正确比较结论。", "raw": "{\"is_correct\":false,\"score\":22,\"correctness\":1,\...
  sources: ['data/raw/real_estate/BLFZ.pdf', 'data/raw/real_estate/HFGF.pdf']
- `summary_001` summary reasons=reference_not_hit_all,number_miss,judge_failed
  query: 结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  expected: 主要方向包括：坚持清洁低碳、安全充裕、经济高效、供需协同、灵活智能的基本原则，2024—2027年重点开展9项专项行动，提升电网对清洁能源的接纳、配置、调控能力；健全煤电、抽水蓄能、新型储能等调节性资源容量电价机制，完善体现分时价值差异的零售市场价格机制；突破新能源高效发电利用、系统灵活调节、电网高效仿真和稳定运行控制、智能化调控等技术；通过调节能力建设优化，支撑2025—2027年年均新增2亿千瓦以上新能源合理消纳利用，全国新能源利用率不低于90%；推动新型储能到2027年基本实现规模化、市场化发展，全国装机规模达到1.8亿千瓦以上。
  answer: 结合相关政策，新能源消纳与新型电力系统建设主要从以下方向推进： 1. 统筹电源与电网、可再生能源与传统化石能源、可再生能源开发与消纳的关系，加快构建新型电力系统，提升可再生能源消纳和存储能力，实现能源绿色低碳转型与安全可靠供应相统一。[资料1] 2. 通过实施可再生能源替代行动，提高可再生能源消纳和存储能力，巩固提升可再生能源产业核心竞争力，促进可再生能源大规模、高比例、市场化、高质量发展。[资料1] 3. 通过建设共享储能电站、探索应...
  reference_coverage: 1/4
  missing_numbers: ['2024', '2027', '9', '2025', '90%', '1.8']
  judge: {"is_correct": false, "score": 48.0, "correctness": 2.0, "completeness": 2.0, "faithfulness": 2.0, "reason": "生成答案只部分覆盖了源网荷储协同、储能、需求侧响应等方向，但遗漏了标准答案中的关键政策要点，如基本原则、2024—2027年9项专项行动、容量电价和分时电价机制、关键技术突破，以及2025—2027年新能源利用率和2027年储能装机目标；同时加入了较多标准答案未明确列出的扩展内容，整体不够贴合。",...
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020210421528000000606.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/P020250912338143145278.pdf']
- `summary_002` summary reasons=reference_not_hit_all,number_miss,judge_failed
  query: 新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？
  expected: 新型储能被定位为支撑新型电力系统的重要技术和基础装备。目标上，到2025年实现从商业化初期向规模化发展转变、装机规模达3000万千瓦以上，到2030年实现全面市场化发展；专项行动进一步提出到2027年基本实现规模化、市场化发展。应用场景上，鼓励电源侧、电网侧、用户侧多元发展，拓展“新能源+储能”、智能微电网、虚拟电厂等场景。技术上，坚持多元化路线，推动锂离子电池规模化应用，推动压缩空气、液流电池、钠离子电池、飞轮、氢储能、热储能等试点示范和商业化发展。市场机制上，推动储能作为独立主体参与电力市场、辅助服务市场，完善容量电价、分时电价和成本疏导机制，并健全标准体系、并网流程和安全监管。
  answer: 1. 要点：发展目标上，政策明确新型储能“由商业化初期步入规模化发展阶段”，到2025年“具备大规模商业化应用条件”，技术创新能力、核心技术装备自主可控水平、标准体系、产业体系、市场环境和商业模式都要提升；到2030年则要“实现新型储能全面市场化发展”，标准体系、市场机制、商业模式“成熟健全”，与电力系统各环节深度融合。[资料1][资料2] 2. 要点：应用场景上，政策围绕电源侧、电网侧、用户侧及更多多场景应用推进；包括电源侧配置储能的...
  reference_coverage: 3/5
  missing_numbers: ['3000', '2027']
  judge: {"is_correct": false, "score": 78.0, "correctness": 4.0, "completeness": 3.0, "faithfulness": 3.0, "reason": "答案整体方向基本一致，覆盖了目标、场景、技术路线和市场机制，但遗漏了标准答案中的关键数字“3000万千瓦以上”和“2027年基本实现规模化、市场化发展”。同时加入了较多标准答案未明确提到的细化场景与表述，存在一定扩展。", "raw": "{\"is_correct\": false, \"scor...
  sources: ['data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/202210114475091.pdf', 'data/raw/policy/P020250912338143145278.pdf']
- `summary_005` summary reasons=reference_not_hit_all,number_miss,judge_failed
  query: 大规模设备更新和消费品以旧换新政策主要支持哪些领域，资金和补贴如何安排？
  expected: 政策统筹安排3000亿元左右超长期特别国债资金，加力支持大规模设备更新和消费品以旧换新。设备更新方面，支持范围从工业、环境基础设施、交通运输、物流、教育、文旅、医疗、回收循环利用，扩大到能源电力、老旧电梯等领域设备更新以及重点行业节能降碳和安全改造，并降低申报门槛、支持中小企业设备更新。具体补贴包括老旧营运船舶报废更新、老旧营运货车报废更新、农业机械报废更新、新能源公交车及动力电池更新等。消费品方面，重点支持汽车报废更新和乘用车置换更新、家电产品和电动自行车以旧换新、旧房装修和厨卫局部改造、居家适老化改造、智能家居消费等，要求真金白银优惠直达消费者。能源设备更新另提出到2027年能源重点领域设备投资规模较2023年增长25%以上。
  answer: 1. 要点：政策主要支持的领域包括工业、环境基础设施、交通运输、物流、教育、文旅、医疗等领域设备更新，以及回收循环利用；在此基础上，还将支持范围扩大到能源电力、老旧电梯等领域设备更新，以及重点行业节能降碳和安全改造。[资料1] 2. 要点：在消费品以旧换新方面，支持老旧营运船舶报废更新、老旧营运货车报废更新、农业机械报废更新、新能源公交车及动力电池更新、汽车报废更新和个人消费者乘用车置换更新、家电产品以旧换新；其中家电补贴为“产品销售价...
  reference_coverage: 3/4
  missing_numbers: ['2027', '2023', '25%']
  judge: {"is_correct": false, "score": 62.0, "correctness": 3.0, "completeness": 3.0, "faithfulness": 1.0, "reason": "覆盖了设备更新和部分消费品以旧换新的方向，也提到3000亿元超长期特别国债资金，但偏离标准答案较多：加入了大量标准答案未提及的具体补贴金额、中央财政275亿元、央地分担比例等内容；同时遗漏了旧房装修、厨卫改造、适老化改造、智能家居消费，以及能源设备更新到2027年投资增长25%以上等关键点。", "...
  sources: ['data/raw/policy/ndrc_2024_equipment_update_consumer_trade_in.pdf', 'data/raw/policy/P020240726413585348997.pdf', 'data/raw/policy/ndrc_2024_energy_equipment_update_plan.pdf']

## Metric Notes

- `answer_rate`：生成答案非空的比例。
- `citation_rate`：答案文本中显式出现 `[资料1]` 这类引用编号的比例。
- `reference_recall` / `reference_hit_all`：用生成文件保存的 `references` 对齐评测集 ground_truth 的 source/pages。
- `numeric_coverage`：标准答案中抽出的数字在生成答案中出现的比例，只在标准答案含数字的样本上统计。
- `LLM judge`：启用 `--llm-judge` 后，由模型比较问题、标准答案和生成答案，输出正确性、完整性和忠实度评分。
- 当前 judge 主要判断答案与 ground truth 的一致性；是否完全被原文支撑仍需结合引用覆盖和人工抽查。
