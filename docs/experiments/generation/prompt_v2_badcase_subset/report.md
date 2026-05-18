# Generation Evaluation

- evaluated_at: 2026-05-18T18:37:22
- eval_file: `data/eval/badcase_prompt_v2_subset.jsonl`
- pred_file: `data/generated/eval_runs/prompt_v2_badcase_subset_answers.jsonl`
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
| reference_recall | 85.83% |
| reference_hit_any | 100.00% |
| reference_hit_all | 66.67% |
| numeric_coverage | 34.52% |
| numeric_count | 12 |
| judge_correct_rate | 16.67% |
| judge_avg_score | 38.58 |
| judge_judged_count | 12 |

## By Question Type

| question_type | count | answer_rate | citation_rate | reference_recall | reference_hit_all | numeric_coverage | numeric_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| compare | 4 | 100.00% | 100.00% | 75.00% | 50.00% | 68.75% | 4 |
| fact | 5 | 100.00% | 100.00% | 100.00% | 100.00% | 0.00% | 5 |
| summary | 3 | 100.00% | 100.00% | 76.67% | 33.33% | 46.43% | 3 |

## LLM Judge

| question_type | judged | correct_rate | avg_score | avg_correctness | avg_completeness | avg_faithfulness |
|---|---:|---:|---:|---:|---:|---:|
| compare | 4 | 25.00% | 44.00 | 2.00 | 1.75 | 3.25 |
| fact | 5 | 0.00% | 12.40 | 0.20 | 0.00 | 1.60 |
| summary | 3 | 33.33% | 75.00 | 4.00 | 3.33 | 3.33 |

## Badcases

- `fact_002` fact reasons=number_miss,judge_failed
  query: 恩捷股份2025A 的 P/E 是多少？
  expected: 514.94 倍。
  answer: 直接答案：2025A 对应 PE 为 33x。 依据：资料中“盈利预测与投资评级”部分写明“我们预计公司2026-2027 年归母净利润22.5/42.5 亿元（原预期25.4/31.5 亿元），新增28 年归母净利润预测51.9 亿元……对应 PE 为 33x/17x/14x”。其中资料未单独给出 2025A 的 P/E；若按该段落中最接近的年度口径，给出的 PE 数值是 33x，但其对应的是 2026E，不是 2025A。[资料1]
  reference_coverage: 1/1
  missing_numbers: ['514.94']
  judge: {"is_correct": false, "score": 12.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 1.0, "reason": "标准答案是2025A的P/E为514.94倍，但生成答案给出33x且承认并非2025A，核心数值完全不一致；同时还加入了与问题无关且无依据的推断。", "raw": "{\"is_correct\":false,\"score\":12,\"correctness\":0,\"completenes...
  sources: ['data/raw/new_energy/EJGF.pdf', 'data/raw/real_estate/CJFZ.pdf', 'data/raw/new_energy/赛力斯_202601.pdf']
- `fact_004` fact reasons=number_miss,judge_failed
  query: 国轩高科 2024A 的 PB 估值是多少倍
  expected: 2.7 倍。
  answer: 直接答案：根据现有资料无法确定 2024A 的 PB 估值倍数。 依据：资料中未给出国轩高科 2024A 的 PB 估值，只有“当前股价对应PE 26x/17x/12x”等 PE 信息，以及部分财务预测表；未提供与 2024A 对应的 PB 数值。[资料1][资料2]
  reference_coverage: 1/1
  missing_numbers: ['2.7']
  judge: {"is_correct": false, "score": 12.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 2.0, "reason": "标准答案是2.7倍，但生成答案称无法确定，直接否定了正确数值，结论错误且缺失关键数字；同时还加入了未必成立的资料判断。", "raw": "{\"is_correct\":false,\"score\":12,\"correctness\":0,\"completeness\":0,\"faithf...
  sources: ['data/raw/new_energy/GXGK.pdf', 'data/raw/consumer/WLY.pdf', 'data/raw/real_estate/XCKG.pdf']
- `fact_008` fact reasons=number_miss,judge_failed
  query: 麦加芯彩 2026E 归母净利润预计是多少
  expected: 272.43 百万元
  answer: 直接答案：2.10 亿元，2026E 归母净利润预计值；但资料中未单独给出麦加芯彩“2026E”这一年度的归母净利润预测值。 依据：资料1仅披露了麦加芯彩2025年全年归母净利润为2.10亿元，以及2026年一季度归母净利润0.10亿元；未提供“2026E 归母净利润”预测表或对应数值，因此根据现有资料无法确定该口径的2026E预测值。[资料1]
  reference_coverage: 1/1
  missing_numbers: ['272.43']
  judge: {"is_correct": false, "score": 25.0, "correctness": 1.0, "completeness": 0.0, "faithfulness": 2.0, "reason": "生成答案给出2.10亿元，实际标准答案为272.43百万元（约2.7243亿元），数值不一致；且还明确说无法确定该预测值，与标准答案冲突。", "raw": "{\"is_correct\":false,\"score\":25,\"correctness\":1,\"completeness\":...
  sources: ['data/raw/new_energy/MJXC.pdf', 'data/raw/consumer/HXJD.pdf', 'data/raw/semiconductor/HWJ.pdf', 'data/raw/consumer/DPYL.pdf']
- `fact_036` fact reasons=number_miss,judge_failed
  query: 截至 2025 年末，金地集团有息负债多少
  expected: 672亿元
  answer: 直接答案：根据现有资料，金地集团截至 2025 年末的有息负债为 **1231 亿元**。 依据：资料中“有息负债及增速”图表显示 2025 年对应“有息负债（亿元）”为 **1231**。[资料2]
  reference_coverage: 1/1
  missing_numbers: ['672']
  judge: {"is_correct": false, "score": 5.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 0.0, "reason": "生成答案与标准答案严重不一致：标准答案为672亿元，生成答案给出1231亿元，且属于明显编造/误读数据。", "raw": "{\"is_correct\":false,\"score\":5,\"correctness\":0,\"completeness\":0,\"faithfulness\":...
  sources: ['data/raw/real_estate/JDJT.pdf', 'data/raw/real_estate/HFGF.pdf']
- `fact_043` fact reasons=number_miss,judge_failed
  query: 深圳皓飞新材2026年Q1实现产品销售收入多少
  expected: 1.57亿元
  answer: 直接答案：根据现有资料无法确定“深圳皓飞新材2026年Q1实现产品销售收入”这一指标。 依据：资料中未出现“深圳皓飞新材”及其2026年Q1“产品销售收入”的对应披露；可用资料里只有其他公司或其他指标的数据，无法匹配到该公司该口径。 [资料1][资料2][资料3][资料4][资料5]
  reference_coverage: 1/1
  missing_numbers: ['1.57']
  judge: {"is_correct": false, "score": 8.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 3.0, "reason": "标准答案为1.57亿元，但生成答案称无法确定，未给出正确数值，核心结论错误且缺失关键答案；同时未明显编造具体数字，忠实性尚可。", "raw": "{\"is_correct\":false,\"score\":8,\"correctness\":0,\"completeness\":0,\"fait...
  sources: ['data/raw/semiconductor/DLGF.pdf', 'data/raw/new_energy/SSGF.pdf', 'data/raw/real_estate/ZSSK.pdf', 'data/raw/new_energy/赛力斯_202601.pdf', 'data/raw/new_energy/广汽集团_202601.pdf']
- `compare_002` compare reasons=reference_not_hit_all,number_miss,judge_failed
  query: 泸州老窖 vs 五粮液，哪家公司的2025年营业总收入更高？
  expected: 五粮液。泸州老窖2025年公司实现营业总收入 257.3 亿元，五粮液2025年公司实现营收 405.29亿元。
  answer: - 对象A（泸州老窖）：2025年营业总收入 **257.3亿元**，口径为“2025年公司实现营业总收入”，引用见[资料2]。 - 对象B（五粮液）：**根据现有资料无法确定**其2025年营业总收入。当前提供的资料中未包含五粮液的2025年营业总收入数据。 结论：根据现有资料，**无法比较泸州老窖与五粮液哪家2025年营业总收入更高**，因为资料中缺少五粮液对应的2025年营业总收入。
  reference_coverage: 1/2
  missing_numbers: ['405.29']
  judge: {"is_correct": false, "score": 32.0, "correctness": 1.0, "completeness": 1.0, "faithfulness": 4.0, "reason": "生成答案只给出泸州老窖数据，未提供五粮液2025年营收405.29亿元，反而说无法比较，与标准答案“ 五粮液更高”不一致；且结论存在关键遗漏。", "raw": "{\"is_correct\":false,\"score\":32,\"correctness\":1,\"completeness\...
  sources: ['data/raw/consumer/SXFJ.pdf', 'data/raw/consumer/LZLJ.pdf']
- `compare_003` compare reasons=reference_not_hit_all,number_miss,judge_failed
  query: 千禾味业 vs 神农集团，哪家公司的26Q1营收 更高
  expected: 神农集团。在26Q1，千禾味业实现营收 8.2 亿元，神农集团实现营收 13.22 亿元
  answer: - 对象A：千禾味业，26Q1 营收 **8.2亿元**，口径为“26Q1公司实现营收”，引用：**[资料1]** - 对象B：神农集团，**根据现有资料无法确定其26Q1营收**；当前可用资料中未提供神农集团26Q1营收数据，只有海天味业等其他公司的数据，无法用于对比。引用：**[资料2]** 结论：**根据现有资料无法判断千禾味业 vs 神农集团哪家公司的26Q1营收更高**，因为资料中缺少**神农集团26Q1营收**这一同口径数据...
  reference_coverage: 1/2
  missing_numbers: ['13.22']
  judge: {"is_correct": false, "score": 28.0, "correctness": 1.0, "completeness": 1.0, "faithfulness": 4.0, "reason": "生成答案只给出了千禾味业的8.2亿元，未给出且还否定了神农集团26Q1营收，导致结论与标准答案“神农集团更高”不一致；同时存在依据不足的保守判断，但未明显编造关键数字。", "raw": "{\"is_correct\": false,\"score\": 28,\"correctness\": 1...
  sources: ['data/raw/consumer/QHWY.pdf', 'data/raw/consumer/HTWY.pdf']
- `compare_013` compare reasons=number_miss
  query: 中集集团 vs 中自科技，预计哪家公司2026年营业收入更高
  expected: 中集集团。中集集团2026E年营业收入168832百万元，中自科技2026E年营业收入2337百万元
  answer: - 对象A：中集集团，2026E 营业收入/主营收入为 **168,832 百万元**，即资料中“**预测公司2026-2028 年收入分别为1688.32、1811.69、1945.23 亿元**”以及“**主营收入（百万元） | 2025A 156,611 | 2026E 168,832 | 2027E 181,169 | 2028E 194,523**”对应的 2026E 收入口径。[资料1] - 对象B：中自科技，**2026...
  reference_coverage: 2/2
  missing_numbers: ['2337']
  judge: {"is_correct": true, "score": 88.0, "correctness": 5.0, "completeness": 4.0, "faithfulness": 3.0, "reason": "结论与标准答案一致，明确判断中集集团2026年营业收入更高；但中自科技给出的“25亿元”为目标值而非标准答案中的2026E 2337百万元，且加入了额外口径说明，存在一定偏离与扩展。", "raw": "{\"is_correct\": true,\"score\": 88,\"correctness...
  sources: ['data/raw/new_energy/ZJJT.pdf', 'data/raw/new_energy/ZZKJ.pdf']
- `compare_029` compare reasons=number_miss,judge_failed
  query: 保利发展 vs 华发股份，哪家公司2025年实现营收更高
  expected: 保利发展。保利发展2025年公司实现营业收入308144百万元，华发股份2025年实现收入834.3亿元
  answer: - 对象A（保利发展）：2025A 营业总收入 **308,144 百万元**，口径为“营业总收入”，年份为 **2025A**。[资料1] - 对象B（华发股份）：2025 年营业收入 **512.4 亿元**，口径为“营业收入”，年份为 **2025**。[资料3] 结论：**根据现有资料无法直接严格比较**，因为两家公司给出的不是完全同口径数字：保利发展披露的是**营业总收入**，华发股份披露的是**营业收入**，不能按要求用不同...
  reference_coverage: 2/2
  missing_numbers: ['834.3']
  judge: {"is_correct": false, "score": 28.0, "correctness": 1.0, "completeness": 1.0, "faithfulness": 2.0, "reason": "标准答案明确是保利发展2025年营收更高；生成答案却以口径不同为由给出无法比较，结论错误。虽提到保利发展308144百万元，但华发股份数字与标准答案不一致，且缺少正确结论。", "raw": "{\"is_correct\":false,\"score\":28,\"correctness\":1,...
  sources: ['data/raw/real_estate/BLFZ.pdf', 'data/raw/real_estate/HFGF.pdf']
- `summary_001` summary reasons=reference_not_hit_all,number_miss,judge_failed
  query: 结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  expected: 主要方向包括：坚持清洁低碳、安全充裕、经济高效、供需协同、灵活智能的基本原则，2024—2027年重点开展9项专项行动，提升电网对清洁能源的接纳、配置、调控能力；健全煤电、抽水蓄能、新型储能等调节性资源容量电价机制，完善体现分时价值差异的零售市场价格机制；突破新能源高效发电利用、系统灵活调节、电网高效仿真和稳定运行控制、智能化调控等技术；通过调节能力建设优化，支撑2025—2027年年均新增2亿千瓦以上新能源合理消纳利用，全国新能源利用率不低于90%；推动新型储能到2027年基本实现规模化、市场化发展，全国装机规模达到1.8亿千瓦以上。
  answer: 结合相关政策，新能源消纳与新型电力系统建设主要从以下方向推进： 1. 要点：坚持“系统观念”，统筹电源与电网、可再生能源与传统化石能源、可再生能源开发与消纳的关系，加快构建新型电力系统，提升可再生能源消纳和存储能力，实现能源绿色低碳转型与安全可靠供应相统一。[资料1] 2. 要点：通过“提高可再生能源消纳和存储能力”，实施可再生能源替代行动，促进可再生能源大规模、高比例、市场化、高质量发展，并“加快构建新型电力系统”。[资料1] 3....
  reference_coverage: 2/4
  missing_numbers: ['2024', '2027', '9', '2025', '90%', '1.8']
  judge: {"is_correct": false, "score": 56.0, "correctness": 3.0, "completeness": 2.0, "faithfulness": 3.0, "reason": "生成答案抓住了源网荷储协同、储能、虚拟电厂、需求侧响应等方向，但与标准答案相比，缺少“9项专项行动”“容量电价机制”“分时电价机制”“关键技术突破”以及2025—2027年、90%、1.8亿千瓦等核心政策数字和结论，且加入了部分标准答案未明确展开的内容。", "raw": "{\"is_correc...
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020210421528000000606.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf']
- `summary_002` summary reasons=reference_not_hit_all
  query: 新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？
  expected: 新型储能被定位为支撑新型电力系统的重要技术和基础装备。目标上，到2025年实现从商业化初期向规模化发展转变、装机规模达3000万千瓦以上，到2030年实现全面市场化发展；专项行动进一步提出到2027年基本实现规模化、市场化发展。应用场景上，鼓励电源侧、电网侧、用户侧多元发展，拓展“新能源+储能”、智能微电网、虚拟电厂等场景。技术上，坚持多元化路线，推动锂离子电池规模化应用，推动压缩空气、液流电池、钠离子电池、飞轮、氢储能、热储能等试点示范和商业化发展。市场机制上，推动储能作为独立主体参与电力市场、辅助服务市场，完善容量电价、分时电价和成本疏导机制，并健全标准体系、并网流程和安全监管。
  answer: 1. 要点：发展目标是“到2025年，新型储能由商业化初期步入规模化发展阶段，具备大规模商业化应用条件”，并要求“技术创新能力显著提高、核心技术装备自主可控水平大幅提升、标准体系基本完善、产业体系日趋完备、市场环境和商业模式基本成熟”；《指导意见》还明确“装机规模达3000万千瓦以上”，到“2030年，实现新型储能全面市场化发展”，标准体系、市场机制、商业模式成熟健全。[资料1][资料2] 2. 要点：应用场景安排上，重点覆盖电源侧、电...
  reference_coverage: 4/5
  missing_numbers: []
  judge: {"is_correct": true, "score": 91.0, "correctness": 5.0, "completeness": 5.0, "faithfulness": 4.0, "reason": "生成答案与标准答案核心结论一致，覆盖了发展目标、应用场景、技术路线和市场机制四部分，且关键数字也都包含。少量加入了标准答案未明确展开的场景和机制细节，但不影响总体结论，故真实性略扣分。", "raw": "{\"is_correct\":true,\"score\":91,\"correctness\...
  sources: ['data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/202210114475091.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/P020210421528000346108.pdf', 'data/raw/policy/P020250106570227369979.pdf']
- `summary_005` summary reasons=number_miss,judge_failed
  query: 大规模设备更新和消费品以旧换新政策主要支持哪些领域，资金和补贴如何安排？
  expected: 政策统筹安排3000亿元左右超长期特别国债资金，加力支持大规模设备更新和消费品以旧换新。设备更新方面，支持范围从工业、环境基础设施、交通运输、物流、教育、文旅、医疗、回收循环利用，扩大到能源电力、老旧电梯等领域设备更新以及重点行业节能降碳和安全改造，并降低申报门槛、支持中小企业设备更新。具体补贴包括老旧营运船舶报废更新、老旧营运货车报废更新、农业机械报废更新、新能源公交车及动力电池更新等。消费品方面，重点支持汽车报废更新和乘用车置换更新、家电产品和电动自行车以旧换新、旧房装修和厨卫局部改造、居家适老化改造、智能家居消费等，要求真金白银优惠直达消费者。能源设备更新另提出到2027年能源重点领域设备投资规模较2023年增长25%以上。
  answer: 大规模设备更新和消费品以旧换新政策主要支持两大方向：一是设备更新，二是消费品以旧换新，并通过超长期特别国债和中央财政资金安排支持。[资料1][资料3] 1. 设备更新支持的重点领域包括：工业、环境基础设施、交通运输、物流、教育、文旅、医疗等领域设备更新，以及回收循环利用；并将支持范围扩大到能源电力、老旧电梯等领域设备更新，以及重点行业节能降碳和安全改造。[资料1] 2. 具体支持还包括老旧营运船舶报废更新、老旧营运货车报废更新、农业机械...
  reference_coverage: 4/4
  missing_numbers: ['2027', '2023', '25%']
  judge: {"is_correct": false, "score": 78.0, "correctness": 4.0, "completeness": 3.0, "faithfulness": 3.0, "reason": "生成答案总体方向正确，覆盖了设备更新、消费品以旧换新、3000亿元超长期特别国债等核心内容，但对标准答案中的“旧房装修和厨卫局部改造、居家适老化改造、智能家居消费”“降低申报门槛、支持中小企业设备更新”以及“能源重点领域到2027年投资规模较2023年增长25%以上”等关键点覆盖不足；同时加入了较多...
  sources: ['data/raw/policy/ndrc_2024_equipment_update_consumer_trade_in.pdf', 'data/raw/policy/P020240726413585348997.pdf', 'data/raw/policy/ndrc_2024_energy_equipment_update_plan.pdf', 'data/raw/policy/P020240821593575195639.pdf']

## Metric Notes

- `answer_rate`：生成答案非空的比例。
- `citation_rate`：答案文本中显式出现 `[资料1]` 这类引用编号的比例。
- `reference_recall` / `reference_hit_all`：用生成文件保存的 `references` 对齐评测集 ground_truth 的 source/pages。
- `numeric_coverage`：标准答案中抽出的数字在生成答案中出现的比例，只在标准答案含数字的样本上统计。
- `LLM judge`：启用 `--llm-judge` 后，由模型比较问题、标准答案和生成答案，输出正确性、完整性和忠实度评分。
- 当前 judge 主要判断答案与 ground truth 的一致性；是否完全被原文支撑仍需结合引用覆盖和人工抽查。
