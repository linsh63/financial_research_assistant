# Generation Evaluation

- evaluated_at: 2026-05-18T17:42:43
- eval_file: `data/eval/financial_qa_dev.jsonl`
- pred_file: `data/generated/eval_runs/routed_answers_full_2026-05-18.jsonl`
- match_level: `page`
- eval_samples: 120 / 120
- skipped_eval_rows: 0
- prediction_rows: 120

## Overall

| metric | value |
|---|---:|
| generated_rate | 100.00% |
| answer_rate | 100.00% |
| citation_rate | 100.00% |
| reference_recall | 93.89% |
| reference_hit_any | 97.50% |
| reference_hit_all | 90.00% |
| numeric_coverage | 83.69% |
| numeric_count | 106 |
| judge_correct_rate | 67.50% |
| judge_avg_score | 81.17 |
| judge_judged_count | 120 |

## By Question Type

| question_type | count | answer_rate | citation_rate | reference_recall | reference_hit_all | numeric_coverage | numeric_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| compare | 30 | 100.00% | 100.00% | 91.67% | 86.67% | 90.83% | 30 |
| fact | 70 | 100.00% | 100.00% | 97.14% | 97.14% | 85.29% | 68 |
| summary | 20 | 100.00% | 100.00% | 85.83% | 70.00% | 43.24% | 8 |

## LLM Judge

| question_type | judged | correct_rate | avg_score | avg_correctness | avg_completeness | avg_faithfulness |
|---|---:|---:|---:|---:|---:|---:|
| compare | 30 | 73.33% | 80.73 | 4.10 | 4.03 | 3.97 |
| fact | 70 | 84.29% | 86.81 | 4.29 | 4.27 | 4.33 |
| summary | 20 | 0.00% | 62.10 | 2.85 | 2.75 | 2.20 |

## Badcases

- `fact_002` fact reasons=number_miss,judge_failed
  query: 恩捷股份2025A 的 P/E 是多少？
  expected: 514.94 倍。
  answer: 恩捷股份 **2025A 的 P/E 约为 492 倍**。 依据是：资料中给出 **2025 年归母净利 1.4 亿元**、**总市值 68,906.37 百万元**，据此测算 **P/E = 68,906.37 / 140 ≈ 492.2x**。[资料1] 如果按 **收盘价 70.16 元** 和 **总股本 982.13 百万股** 反推，结果也约为 **492 倍**。[资料1]
  reference_coverage: 1/1
  missing_numbers: ['514.94']
  judge: {"is_correct": false, "score": 38.0, "correctness": 1.0, "completeness": 1.0, "faithfulness": 1.0, "reason": "标准答案是514.94倍，生成答案给出约492倍，核心数值不一致。且加入了与标准答案不同的推算过程，属于无依据扩展并导致结论偏差。", "raw": "{\"is_correct\":false,\"score\":38,\"correctness\":1,\"completeness\":1,\"...
  sources: ['data/raw/new_energy/EJGF.pdf', 'data/raw/real_estate/CJFZ.pdf', 'data/raw/new_energy/赛力斯_202601.pdf']
- `fact_004` fact reasons=number_miss,judge_failed
  query: 国轩高科 2024A 的 PB 估值是多少倍
  expected: 2.7 倍。
  answer: 根据现有资料无法确定国轩高科 **2024A 的 PB 估值**。 目前可见资料中仅披露了 **2026~2028 年对应 PE 为 26x/17x/12x**，未明确给出 **2024A PB** 数值。[资料1][资料2]
  reference_coverage: 1/1
  missing_numbers: ['2.7']
  judge: {"is_correct": false, "score": 18.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 4.0, "reason": "标准答案是“2.7倍”，生成答案未给出该数值，反而说无法确定，核心结论错误且关键信息缺失。虽未明显编造2024A PB，但加入了与题目无关的PE信息。", "raw": "{\"is_correct\":false,\"score\":18,\"correctness\":0,\"completen...
  sources: ['data/raw/new_energy/GXGK.pdf', 'data/raw/consumer/WLY.pdf', 'data/raw/real_estate/XCKG.pdf']
- `fact_008` fact reasons=number_miss,judge_failed
  query: 麦加芯彩 2026E 归母净利润预计是多少
  expected: 272.43 百万元
  answer: 根据现有资料无法确定。 资料1仅披露了麦加芯彩 **2025 年归母净利润为 2.10 亿元**，以及 **2026 年一季度归母净利润为 0.10 亿元**，未给出 **2026E 归母净利润预测值**。[资料1]
  reference_coverage: 1/1
  missing_numbers: ['272.43']
  judge: {"is_correct": false, "score": 12.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 4.0, "reason": "标准答案要求给出2026E归母净利润272.43百万元，生成答案未给出该数值，而是称无法确定，核心结论不一致。虽未明显编造，但遗漏关键答案。", "raw": "{\"is_correct\":false,\"score\":12,\"correctness\":0,\"completeness\"...
  sources: ['data/raw/new_energy/MJXC.pdf', 'data/raw/consumer/HXJD.pdf', 'data/raw/semiconductor/HWJ.pdf', 'data/raw/consumer/DPYL.pdf']
- `fact_013` fact reasons=number_miss,judge_failed
  query: 安琪酵母2025A净利润为多少
  expected: 15.89亿元
  answer: 安琪酵母 **2025A 归母净利润为 15.44 亿元** [资料1]。 如果你问的是“净利润”口径而非“归母净利润”，根据现有资料无法确定。
  reference_coverage: 1/1
  missing_numbers: ['15.89']
  judge: {"is_correct": false, "score": 42.0, "correctness": 2.0, "completeness": 1.0, "faithfulness": 3.0, "reason": "标准答案是15.89亿元，但生成答案给出15.44亿元，核心数字不一致；虽然提示了口径差异，但未回答标准答案所问的净利润数值，存在偏差。", "raw": "{\"is_correct\":false,\"score\":42,\"correctness\":2,\"completeness\":1...
  sources: ['data/raw/consumer/AQJM.pdf', 'data/raw/healthcare/SYXY.pdf']
- `fact_021` fact reasons=judge_failed
  query: 爱尔眼科归属母公司净利润是多少
  expected: 11.81 亿元
  answer: 爱尔眼科**2025年归母净利润为32.40亿元**，同比下降**8.9%**；**2026Q1归母净利润为11.81亿元**，同比增长**12.5%**。[资料1]
  reference_coverage: 1/1
  missing_numbers: []
  judge: {"is_correct": false, "score": 48.0, "correctness": 2.0, "completeness": 2.0, "faithfulness": 1.0, "reason": "标准答案只要“归属母公司净利润为11.81亿元”，生成答案虽包含11.81亿元，但把它说成了2026Q1归母净利润，并额外加入2025年32.40亿元等无关信息，结论对应不准确，存在一定编造和错位。", "raw": "{\"is_correct\":false,\"score\":48,\"cor...
  sources: ['data/raw/healthcare/AEYK.pdf']
- `fact_036` fact reasons=number_miss,judge_failed
  query: 截至 2025 年末，金地集团有息负债多少
  expected: 672亿元
  answer: 截至 2025 年末，金地集团有息负债为 **1231 亿元**，同比 **下降 10.2%**。[资料4]
  reference_coverage: 1/1
  missing_numbers: ['672']
  judge: {"is_correct": false, "score": 8.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 1.0, "reason": "标准答案为672亿元，生成答案给出1231亿元且与标准答案明显不符，属于错误回答；虽有引用但数值与结论不一致。", "raw": "{\"is_correct\":false,\"score\":8,\"correctness\":0,\"completeness\":0,\"faithfulness...
  sources: ['data/raw/real_estate/JDJT.pdf', 'data/raw/real_estate/HFGF.pdf']
- `fact_043` fact reasons=number_miss,judge_failed
  query: 深圳皓飞新材2026年Q1实现产品销售收入多少
  expected: 1.57亿元
  answer: 根据现有资料无法确定“深圳皓飞新材2026年Q1实现产品销售收入”这一数字。资料中未提供深圳皓飞新材的相关数据；现有材料主要涉及鼎龙股份、崧盛股份、招商蛇口、赛力斯、广汽集团等公司。[资料1][资料2][资料3][资料4][资料5]
  reference_coverage: 1/1
  missing_numbers: ['1.57']
  judge: {"is_correct": false, "score": 10.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 2.0, "reason": "标准答案是1.57亿元，生成答案未给出该数字，反而称无法确定，核心结论错误且缺失关键数值。", "raw": "{\"is_correct\":false,\"score\":10,\"correctness\":0,\"completeness\":0,\"faithfulness\":2,\"r...
  sources: ['data/raw/semiconductor/DLGF.pdf', 'data/raw/new_energy/SSGF.pdf', 'data/raw/real_estate/ZSSK.pdf', 'data/raw/new_energy/赛力斯_202601.pdf', 'data/raw/new_energy/广汽集团_202601.pdf']
- `fact_045` fact reasons=number_miss,judge_failed
  query: 飞荣达公司2025主营收入为多少
  expected: 6527百万元
  answer: 根据现有资料，**飞荣达2025年主营收入无法直接确定**。 资料中仅明确给出了飞荣达**2026年一季度营业收入16.44亿元**及同比增长情况[资料2]，未提供**2025年主营收入/主营业务收入**的明确数值。 如果你需要，我也可以继续帮你从资料里查找**2025年营业收入**或**分业务收入**的相关表述。
  reference_coverage: 1/1
  missing_numbers: ['6527']
  judge: {"is_correct": false, "score": 18.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 2.0, "reason": "标准答案明确为6527百万元，生成答案却称无法确定，直接与标准答案不一致，且缺少关键数字；同时还引入了2026年一季度收入等无关信息。", "raw": "{\"is_correct\":false,\"score\":18,\"correctness\":0,\"completeness\":0,...
  sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/FRD.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YKSW.pdf']
- `fact_047` fact reasons=reference_not_hit_all,number_miss,judge_failed
  query: 2025 年，海达尔公司研发费用为多少
  expected: 1401万元
  answer: 2025 年，海达尔公司的研发费用为 **4,410.76 万元** [资料1]。
  reference_coverage: 0/1
  missing_numbers: ['1401']
  judge: {"is_correct": false, "score": 20.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 1.0, "reason": "生成答案给出的研发费用为4410.76万元，与标准答案1401万元明显不一致，且存在数值编造/误答。", "raw": "{\"is_correct\":false,\"score\":20,\"correctness\":0,\"completeness\":0,\"faithfulness\":...
  sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/DLGF.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/healthcare/SYXY.pdf']
- `fact_049` fact reasons=reference_not_hit_all,number_miss,judge_failed
  query: 海光信息公司2024A销售毛利率为多少
  expected: 63.7%
  answer: 根据现有资料无法确定海光信息公司2024A销售毛利率。[资料1][资料2][资料3][资料4]
  reference_coverage: 0/1
  missing_numbers: ['63.7%']
  judge: {"is_correct": false, "score": 12.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 4.0, "reason": "标准答案为63.7%，生成答案却称无法确定，未给出正确数值，属于核心结论错误且缺失关键信息。", "raw": "{\"is_correct\":false,\"score\":12,\"correctness\":0,\"completeness\":0,\"faithfulness\":4,\"...
  sources: ['data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/new_energy/SGHN.pdf']
- `fact_055` fact reasons=number_miss,judge_failed
  query: 到2030年，基本建成全国统⼀电⼒市场体系，各类型电源和除保障性⽤户外的电⼒⽤户全部直接参与电⼒市场，市场化交易电量在全社会⽤电量的占比大概是多少
  expected: 70%
  answer: 截至2030年，**市场化交易电量占全社会用电量的比例**，根据现有资料**无法直接确定**。[资料1] 资料只提到到**2025年底**这一口径：市场化交易电量达**6.6万亿千瓦时**，占全社会用电量比重由**不足15%**上升至**64%**，并且“除保障性和自发自用电量外全部通过市场实现”。[资料1] 但资料中**没有给出2030年的具体占比数字**，只能说明《意见》对未来**5—10年**作了安排部署。[资料1]
  reference_coverage: 1/1
  missing_numbers: ['70%']
  judge: {"is_correct": false, "score": 22.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 2.0, "reason": "标准答案是70%，而生成答案没有给出该数值，反而称无法直接确定，核心结论错误且缺失关键数字；同时加入了无必要的资料推断，可信度较低。", "raw": "{\"is_correct\":false,\"score\":22,\"correctness\":0,\"completeness\":0,\...
  sources: ['data/raw/policy/ndrc_unified_power_market_interview.pdf']
- `compare_002` compare reasons=reference_not_hit_all,number_miss,judge_failed
  query: 泸州老窖 vs 五粮液，哪家公司的2025年营业总收入更高？
  expected: 五粮液。泸州老窖2025年公司实现营业总收入 257.3 亿元，五粮液2025年公司实现营收 405.29亿元。
  answer: 根据现有资料，**无法确定五粮液的2025年营业总收入**，因此也**无法直接判断泸州老窖 vs 五粮液谁更高**。 - **泸州老窖**：2025年营业总收入为 **257.3亿元** [资料2][资料3] - **五粮液**：当前提供的资料中**没有2025年营业总收入数据** [资料1] **结论：根据现有资料无法确定哪家公司2025年营业总收入更高。**
  reference_coverage: 1/2
  missing_numbers: ['405.29']
  judge: {"is_correct": false, "score": 18.0, "correctness": 1.0, "completeness": 1.0, "faithfulness": 4.0, "reason": "生成答案未给出标准答案中的关键结论“五粮液更高”，反而声称无法确定，且缺少五粮液405.29亿元这一核心数字。", "raw": "{\"is_correct\":false,\"score\":18,\"correctness\":1,\"completeness\":1,\"faithfulne...
  sources: ['data/raw/consumer/SXFJ.pdf', 'data/raw/consumer/LZLJ.pdf']
- `compare_003` compare reasons=reference_not_hit_all,number_miss,judge_failed
  query: 千禾味业 vs 神农集团，哪家公司的26Q1营收 更高
  expected: 神农集团。在26Q1，千禾味业实现营收 8.2 亿元，神农集团实现营收 13.22 亿元
  answer: 千禾味业与神农集团的26Q1营收对比，**根据现有资料无法确定**。 - **千禾味业**：26Q1实现营收 **8.2亿元** [资料1] - **神农集团**：你提供的资料中**没有神农集团26Q1营收数据**，因此无法与千禾味业直接比较 [资料1][资料2] **结论：**由于缺少神农集团26Q1营收的可用数据，**根据现有资料无法确定哪家公司26Q1营收更高**。
  reference_coverage: 1/2
  missing_numbers: ['13.22']
  judge: {"is_correct": false, "score": 18.0, "correctness": 1.0, "completeness": 1.0, "faithfulness": 4.0, "reason": "生成答案未给出标准答案中的关键结论：神农集团26Q1营收更高（13.22亿元），反而声称无法确定，属于与标准答案不一致。虽引用了千禾味业8.2亿元，但缺少神农集团13.22亿元这一关键数字，且没有明显编造。", "raw": "{\"is_correct\": false, \"score\": 1...
  sources: ['data/raw/consumer/QHWY.pdf', 'data/raw/consumer/HTWY.pdf']
- `compare_005` compare reasons=number_miss
  query: 珀莱雅 vs 伊利股份，哪家公司2025年的毛利率更高
  expected: 珀莱雅。25 年珀莱雅毛利率为 73.26%，2025/2026Q1 伊利股份毛利率为 34.58%/38.37%
  answer: 根据现有资料，**珀莱雅 2025 年的毛利率更高**。 ### 对比依据 - **珀莱雅**：2025 年毛利率为 **73.26%**，同比提升 **1.87pct**。[资料2] - **伊利股份**：2025 年毛利率为 **34.58%**，同比提升 **0.70pct**。[资料1] ### 结论 珀莱雅 2025 年毛利率 **73.26%**，明显高于伊利股份的 **34.58%**，因此**珀莱雅更高**。[资料2][...
  reference_coverage: 2/2
  missing_numbers: ['38.37%']
  judge: {"is_correct": true, "score": 92.0, "correctness": 5.0, "completeness": 4.0, "faithfulness": 4.0, "reason": "核心结论正确，珀莱雅毛利率更高；也给出了关键数值对比。但标准答案还包含伊利股份2026Q1毛利率38.37%，生成答案未覆盖，且加入了同比提升信息，略有扩展。", "raw": "{\"is_correct\":true,\"score\":92,\"correctness\":5,\"complet...
  sources: ['data/raw/consumer/YLGF.pdf', 'data/raw/consumer/BLY.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/SYXY.pdf']
- `compare_007` compare reasons=reference_not_hit_all,number_miss,judge_failed
  query: 普蕊斯 vs 普瑞眼科，预计哪家公司在2026年的营收更高
  expected: 普瑞眼科。普蕊斯2026E营收为931.69百万元，普瑞眼科2026E营收为3136百万元
  answer: 对比 2026 年营收，**普瑞眼科更高**。 ### 依据数字对比 - **普瑞眼科**：资料中给出其 2026 年归母净利润预测为 **1.76 亿元**，并给出 2026-2028 年归母净利润预测，但**未直接给出 2026 年营收预测值**；同时 2025 年营业收入为 **27.97 亿元**，[资料1] - **普蕊斯**：当前可用资料里**没有提供普蕊斯的 2026 年营收或可推算营收数据**，因此无法与普瑞眼科进行直接...
  reference_coverage: 1/2
  missing_numbers: ['931.69', '3136']
  judge: {"is_correct": false, "score": 18.0, "correctness": 1.0, "completeness": 0.0, "faithfulness": 2.0, "reason": "标准答案明确为普瑞眼科2026年营收更高，但生成答案最后却说无法确定，核心结论错误且缺失关键营收数字；同时还加入了与问题无关的利润和2025营收信息。", "raw": "{\"is_correct\":false,\"score\":18,\"correctness\":1,\"completen...
  sources: ['data/raw/healthcare/PRYK.pdf', 'data/raw/healthcare/HXYK.pdf', 'data/raw/healthcare/AEYK.pdf']
- `compare_008` compare reasons=reference_not_hit_all,number_miss,judge_failed
  query: 昭衍新药 vs 通策医疗，预计哪家公司在2026年的营收更高
  expected: 通策医疗。昭衍新药2026E营收为2141百万元，通策医疗2026E主营业务收入为3591百万元
  answer: 根据现有资料，**预计 2026 年昭衍新药的营收更高**。 ### 依据数字对比 - **昭衍新药**：资料显示其 **2026E 营业收入为 21.41 亿元**（2,141 百万元）[资料5] - **通策医疗**：你提供的资料中**没有通策医疗 2026 年营收预测数据**，因此无法直接列出其 2026 年营收数字 [资料1][资料2][资料3][资料4][资料5] ### 结论 基于现有资料，**只能确认昭衍新药 2026E...
  reference_coverage: 0/2
  missing_numbers: ['3591']
  judge: {"is_correct": false, "score": 15.0, "correctness": 0.0, "completeness": 0.0, "faithfulness": 2.0, "reason": "标准答案明确是通策医疗营收更高（3591百万元 vs 2141百万元），生成答案却判断为昭衍新药更高，并声称无法比较，核心结论完全错误且遗漏了通策医疗的关键数字。", "raw": "{\"is_correct\":false,\"score\":15,\"correctness\":0,\"com...
  sources: ['data/raw/healthcare/YKSW.pdf', 'data/raw/healthcare/SYXY.pdf']
- `compare_013` compare reasons=number_miss,judge_failed
  query: 中集集团 vs 中自科技，预计哪家公司2026年营业收入更高
  expected: 中集集团。中集集团2026E年营业收入168832百万元，中自科技2026E年营业收入2337百万元
  answer: 根据现有资料，**预计中集集团2026年营业收入更高**。[资料1][资料2] 对比依据如下： - **中集集团**：资料给出2026E收入为 **1688.32亿元**，对应“主营收入（百万元）”为 **168,832**。[资料1] - **中自科技**：资料显示公司2026年营收考核目标为 **25亿元**，对应2026年营收约 **25亿元**。[资料2] **结论：** 按资料中的2026年预测/目标收入口径比较，**中集集团...
  reference_coverage: 2/2
  missing_numbers: ['2337']
  judge: {"is_correct": false, "score": 68.0, "correctness": 4.0, "completeness": 2.0, "faithfulness": 2.0, "reason": "结论与标准答案一致，都是中集集团2026年营收更高；但生成答案把中自科技的2026年营收写成25亿元，未覆盖标准答案中的2337百万元，且存在明显数字不一致，属于无依据扩展/编造。", "raw": "{\"is_correct\": false, \"score\": 68, \"correctn...
  sources: ['data/raw/new_energy/ZJJT.pdf', 'data/raw/new_energy/ZZKJ.pdf']
- `compare_021` compare reasons=number_miss,judge_failed
  query: 华源控股 vs 海光信息，哪家公司2026年Q1实现营收更高
  expected: 海光信息。华源控股2026Q1 公司实现营收 5.85 亿元，海光信息2026 年一季度公司实现收入 40.34 亿元
  answer: 对比结论：**海光信息 2026 年 Q1 营收更高**。[资料1][资料2] - **海光信息**：2026 年一季度实现收入 **40.34 亿元**。[资料1] - **华源控股**：资料中仅给出了 **2026-2028 年公司收入预测**，分别为 **27.21/31.10/35.37 亿元**，但**没有提供 2026 年 Q1 实际营收**，因此无法直接与海光信息的 2026 年 Q1 营收做同口径比较。[资料4][资料5...
  reference_coverage: 2/2
  missing_numbers: ['5.85']
  judge: {"is_correct": false, "score": 72.0, "correctness": 3.0, "completeness": 2.0, "faithfulness": 2.0, "reason": "结论与标准答案一致，但把华源控股2026Q1营收说成缺失，忽略了标准答案中的5.85亿元，属于关键遗漏且有一定编造/偏离。", "raw": "{\"is_correct\":false,\"score\":72,\"correctness\":3,\"completeness\":2,\"fait...
  sources: ['data/raw/semiconductor/HGXX.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `compare_028` compare reasons=judge_failed
  query: 隆基绿能 vs 格林美，哪家公司2026年Q1实现营收更高
  expected: 格林美。隆基绿能26Q1 营收 111.9 亿，格林美2026年Q1实现营收99.82 亿元
  answer: 从“2026年Q1实现营收”来看，隆基绿能更高。 - 隆基绿能：2026年Q1实现营收 **111.9亿元** [资料2] - 格林美：2026年Q1实现营业收入 **99.82亿元** [资料1] 结论：**隆基绿能 2026年Q1营收高于格林美**，高出约 **12.08亿元**（111.9亿元 - 99.82亿元）[资料1][资料2]
  reference_coverage: 2/2
  missing_numbers: []
  judge: {"is_correct": false, "score": 18.0, "correctness": 0.0, "completeness": 2.0, "faithfulness": 4.0, "reason": "标准答案为格林美更高，但生成答案给出隆基绿能更高，结论相反；虽列出两家公司营收数值，但未按标准答案给出正确比较结果。", "raw": "{\"is_correct\":false,\"score\":18,\"correctness\":0,\"completeness\":2,\"faithfu...
  sources: ['data/raw/new_energy/GLM.pdf', 'data/raw/new_energy/LJLN.pdf', 'data/raw/new_energy/宁德时代_202601.pdf']
- `compare_029` compare reasons=number_miss,judge_failed
  query: 保利发展 vs 华发股份，哪家公司2025年实现营收更高
  expected: 保利发展。保利发展2025年公司实现营业收入308144百万元，华发股份2025年实现收入834.3亿元
  answer: 根据现有资料，**2025年华发股份营收更高**。 对比依据如下： - **保利发展**：2025A 营业总收入为 **308,144 百万元**，即约 **3,081.44 亿元**。[资料1] - **华发股份**：2025 年营业收入为 **512.4 亿元**。[资料2][资料4] **结论**：按2025年营业收入口径对比，**华发股份（512.4亿元）高于保利发展（约3,081.44亿元）**，因此不是华发股份更高，而是**...
  reference_coverage: 2/2
  missing_numbers: ['834.3']
  judge: {"is_correct": false, "score": 45.0, "correctness": 3.0, "completeness": 4.0, "faithfulness": 1.0, "reason": "最终结论改正为保利发展更高，但前文先错误断言华发股份更高，并编造了华发股份512.4亿元，与标准答案834.3亿元不一致，且表述自相矛盾。", "raw": "{\"is_correct\":false,\"score\":45,\"correctness\":3,\"completeness\":...
  sources: ['data/raw/real_estate/BLFZ.pdf', 'data/raw/real_estate/HFGF.pdf']
- `summary_001` summary reasons=reference_not_hit_all,number_miss,judge_failed
  query: 结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  expected: 主要方向包括：坚持清洁低碳、安全充裕、经济高效、供需协同、灵活智能的基本原则，2024—2027年重点开展9项专项行动，提升电网对清洁能源的接纳、配置、调控能力；健全煤电、抽水蓄能、新型储能等调节性资源容量电价机制，完善体现分时价值差异的零售市场价格机制；突破新能源高效发电利用、系统灵活调节、电网高效仿真和稳定运行控制、智能化调控等技术；通过调节能力建设优化，支撑2025—2027年年均新增2亿千瓦以上新能源合理消纳利用，全国新能源利用率不低于90%；推动新型储能到2027年基本实现规模化、市场化发展，全国装机规模达到1.8亿千瓦以上。
  answer: 结合现有资料，新能源消纳与新型电力系统建设主要从以下几个方向推进： 1. **提升系统调节与储能能力** - 布局共享储能电站，完善调用和市场化运行机制，提升系统保供和新能源消纳能力。[资料2][资料4] - 探索液流电池、飞轮、压缩空气储能、重力储能、钠离子电池等多种新型储能技术路线，推动市场化投资运营。[资料2][资料4] - 推进“新能源+储能”项目，增强电源侧平滑出力和可靠支撑能力。[资料3][资料5] 2. **强化电网侧与源...
  reference_coverage: 2/4
  missing_numbers: ['2024', '2027', '9', '2025', '90%', '1.8']
  judge: {"is_correct": false, "score": 48.0, "correctness": 2.0, "completeness": 2.0, "faithfulness": 2.0, "reason": "生成答案覆盖了储能、电网协同、市场机制等部分方向，但遗漏了标准答案中的政策主线、2024—2027年9项专项行动，以及2025—2027年、90%和1.8亿千瓦等关键目标；同时加入了较多标准答案未提及的具体做法，存在一定扩展。", "raw": "{\"is_correct\": false, \"...
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020210421528000000606.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf']
- `summary_002` summary reasons=reference_not_hit_all,judge_failed
  query: 新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？
  expected: 新型储能被定位为支撑新型电力系统的重要技术和基础装备。目标上，到2025年实现从商业化初期向规模化发展转变、装机规模达3000万千瓦以上，到2030年实现全面市场化发展；专项行动进一步提出到2027年基本实现规模化、市场化发展。应用场景上，鼓励电源侧、电网侧、用户侧多元发展，拓展“新能源+储能”、智能微电网、虚拟电厂等场景。技术上，坚持多元化路线，推动锂离子电池规模化应用，推动压缩空气、液流电池、钠离子电池、飞轮、氢储能、热储能等试点示范和商业化发展。市场机制上，推动储能作为独立主体参与电力市场、辅助服务市场，完善容量电价、分时电价和成本疏导机制，并健全标准体系、并网流程和安全监管。
  answer: 新型储能政策总体上围绕“发展目标—应用场景—技术路线—市场机制”四个方面进行安排，核心是推动新型储能从商业化初期走向规模化、市场化发展，并服务新型电力系统和碳达峰碳中和目标。[资料1][资料2][资料4] **一、发展目标：从规模化到全面市场化** - 《“十四五”新型储能发展实施方案》提出，到 **2025年** 新型储能由商业化初期步入**规模化发展阶段**，具备大规模商业化应用条件，技术创新能力显著提高，核心技术装备自主可控水平大...
  reference_coverage: 4/5
  missing_numbers: []
  judge: {"is_correct": false, "score": 82.0, "correctness": 4.0, "completeness": 4.0, "faithfulness": 3.0, "reason": "整体方向基本一致，目标、场景和技术路线覆盖较全，但市场机制部分未完整对应标准答案，且加入了较多标准答案未明确提及的细节与数字，末尾还存在表述未收完的情况，影响忠实度。", "raw": "{\"is_correct\": false, \"score\": 82, \"correctness\":...
  sources: ['data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/202210114475091.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/P020210421528000346108.pdf', 'data/raw/policy/P020250106570227369979.pdf']
- `summary_003` summary reasons=reference_not_hit_all,number_miss,judge_failed
  query: “十四五”可再生能源规划和氢能规划分别怎样服务能源绿色低碳转型？
  expected: 可再生能源规划提出，加快发展可再生能源、实施可再生能源替代行动，是推进能源革命和构建清洁低碳、安全高效能源体系的重大举措；到2025年，可再生能源消费总量达到10亿吨标准煤左右，年发电量达到3.3万亿千瓦时左右，全国可再生能源电力总量消纳责任权重达到33%左右，非水电消纳责任权重达到18%左右。规划还要求推动绿色直供电、可再生能源供暖、非电直接利用和高比例可再生能源应用示范，健全消纳责任权重和长效机制。氢能规划将氢能界定为来源丰富、绿色低碳、应用广泛的二次能源，要求构建清洁化、低碳化、低成本的多元制氢体系，开展可再生能源制氢示范，构建安全、稳定、高效的氢能供应网络，并形成“1+N”政策体系。
  answer: 根据现有资料，两份规划都围绕“能源绿色低碳转型”提供支撑，但侧重点不同： 1. **“十四五”可再生能源发展规划** 重点是把可再生能源作为能源转型的“主力增量”，通过**大规模开发、提升消纳、扩大替代**来服务绿色低碳转型。规划明确提出，加快发展可再生能源、实施可再生能源替代行动，是推进能源革命、构建**清洁低碳、安全高效能源体系**的重大举措，也是落实应对气候变化国家自主贡献目标的攻坚任务。[资料2] 具体看，规划从三方面发力：一是...
  reference_coverage: 2/3
  missing_numbers: ['2025', '10', '3.3', '33%', '18%']
  judge: {"is_correct": false, "score": 68.0, "correctness": 3.0, "completeness": 3.0, "faithfulness": 3.0, "reason": "答案抓住了两份规划分别通过可再生能源扩张和氢能作为载体来服务绿色低碳转型的主旨，但遗漏了标准答案中的关键量化目标和部分具体要求（如10亿吨标准煤、3.3万亿千瓦时、33%/18%责任权重、绿色直供电等）。同时加入了较多标准答案未提及的扩展内容，整体与标准答案不完全一致。", "raw": "{\"i...
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020220323314396580505.pdf', 'data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/P020210421528000346108.pdf']
- `summary_004` summary reasons=reference_not_hit_all,number_miss,judge_failed
  query: 电网建设、电力市场和容量电价政策如何支撑新能源消纳与系统可靠运行？
  expected: 配电网政策要求适度超前建设配电网，提升承载力，满足分布式新能源和电动汽车充电基础设施发展。全国统一电力市场提出到2030年基本建成全国统一电力市场体系，市场化交易电量占全社会用电量的70%左右，并推动跨省跨区和省内联合交易。容量机制方面，煤电、抽水蓄能、新型储能等支撑性、调节性资源在高比例新能源消纳和新型电力系统中发挥重要作用，政策通过可靠容量补偿、容量市场探索和发电侧容量电价机制，保障其收益、增强电力安全保供能力。新能源报价政策则要求规范集中报价、价格预警和数字化监管，防范市场力滥用，维护市场公平竞争。
  answer: 电网建设、电力市场和容量电价政策，主要从“提升系统承载与调节能力、优化新能源配置、保障调节性电源收益”三方面支撑新能源消纳和系统可靠运行： 1. **电网建设：增强接网、输送和调节能力** - 通过加快构建新型电力系统，统筹**电源与电网、开发与消纳**，提升新能源消纳和存储能力，实现“能源绿色低碳转型与安全可靠供应相统一”[资料1]。 - 在电网侧，通过**配电网高质量发展**，开展新能源接网影响分析、建立可开放容量定期发布和预警机制...
  reference_coverage: 1/5
  missing_numbers: ['70%']
  judge: {"is_correct": false, "score": 72.0, "correctness": 3.0, "completeness": 3.0, "faithfulness": 2.0, "reason": "答案整体方向基本对，但与标准答案不完全一致。遗漏了全国统一电力市场到2030年基本建成、市场化交易电量占70%左右这一关键数字；同时加入了较多标准答案未提及的细节和表述，存在一定扩展编造。", "raw": "{\"is_correct\": false, \"score\": 72, \"corr...
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf', 'data/raw/policy/ndrc_generation_capacity_price_qna.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf']
- `summary_005` summary reasons=number_miss,judge_failed
  query: 大规模设备更新和消费品以旧换新政策主要支持哪些领域，资金和补贴如何安排？
  expected: 政策统筹安排3000亿元左右超长期特别国债资金，加力支持大规模设备更新和消费品以旧换新。设备更新方面，支持范围从工业、环境基础设施、交通运输、物流、教育、文旅、医疗、回收循环利用，扩大到能源电力、老旧电梯等领域设备更新以及重点行业节能降碳和安全改造，并降低申报门槛、支持中小企业设备更新。具体补贴包括老旧营运船舶报废更新、老旧营运货车报废更新、农业机械报废更新、新能源公交车及动力电池更新等。消费品方面，重点支持汽车报废更新和乘用车置换更新、家电产品和电动自行车以旧换新、旧房装修和厨卫局部改造、居家适老化改造、智能家居消费等，要求真金白银优惠直达消费者。能源设备更新另提出到2027年能源重点领域设备投资规模较2023年增长25%以上。
  answer: 大规模设备更新和消费品以旧换新政策，主要支持两大方向：设备更新和消费品以旧换新，并以超长期特别国债和中央财政资金为主安排资金，部分领域实行央地共担。[资料1][资料3] **一、设备更新主要支持领域** 1. **存量设备更新扩围**：在工业、环境基础设施、交通运输、物流、教育、文旅、医疗、回收循环利用等领域基础上，扩大到**能源电力、老旧电梯**等领域，以及**重点行业节能降碳和安全改造**，并支持**中小企业设备更新**。[资料1]...
  reference_coverage: 4/4
  missing_numbers: ['2027', '2023', '25%']
  judge: {"is_correct": false, "score": 76.0, "correctness": 3.0, "completeness": 3.0, "faithfulness": 2.0, "reason": "答案覆盖了设备更新、消费品以旧换新的主要方向，也提到3000亿元超长期特别国债资金，但对标准答案中的关键补贴安排和消费端重点支持内容概括不够准确，且加入了大量标准答案未要求的细化补贴金额与条目，存在一定扩展。另缺少“真金白银优惠直达消费者”和能源重点领域到2027年设备投资较2023年增长25%以上...
  sources: ['data/raw/policy/ndrc_2024_equipment_update_consumer_trade_in.pdf', 'data/raw/policy/P020240726413585348997.pdf', 'data/raw/policy/ndrc_2024_energy_equipment_update_plan.pdf', 'data/raw/policy/P020240821593575195639.pdf']
- `summary_006` summary reasons=judge_failed
  query: 培育消费新场景和新型消费的政策重点有哪些？
  expected: 消费新场景政策要求围绕居民吃穿住用行等传统消费和服务消费，培育一批带动性广、显示度高的消费新场景，推广特色鲜明、市场引领突出的典型案例，推动消费新业态、新模式、新产品不断涌现。重点包括餐饮消费细分领域、文旅体育消费、购物消费多元融合、利用人工智能大模型、虚拟现实和数字人等技术拓展购物体验、健康消费、银发消费、育幼消费等。新型消费政策强调线上线下消费有机融合，培育壮大零售新业态，拓展“互联网+”医疗、教育、体育等服务产品，推动数字化、网络化、智能化消费发展。
  answer: 培育消费新场景和新型消费的政策重点，主要可归纳为以下几类： 1. **围绕传统消费和服务消费，打造带动性强的新场景** 重点围绕居民“吃穿住用行”等领域，培育一批带动性广、显示度高的消费新场景，推广特色鲜明、市场引领突出的典型案例，支持创新能力强的消费端领军企业发展，推动新业态、新模式、新产品不断涌现。[资料1][资料2] 2. **餐饮消费：细分化、下沉化、智能化、融合化** 包括挖掘地方特色美食，打造“美食名村”“美食名镇”，鼓励大...
  reference_coverage: 4/4
  missing_numbers: []
  judge: {"is_correct": false, "score": 58.0, "correctness": 3.0, "completeness": 3.0, "faithfulness": 2.0, "reason": "生成答案覆盖了传统消费场景、餐饮、文旅体育、线上线下融合和新技术应用等部分重点，但加入了大量标准答案未提及的细化内容与政策措施，偏离较多；同时对“新型消费”中零售新业态、互联网+医疗/教育/体育、数字化网络化智能化消费等关键点覆盖不够完整。", "raw": "{\"is_correct\":fal...
  sources: ['data/raw/policy/ndrc_2024_consumer_new_scenarios.pdf', 'data/raw/policy/P020240624569333510920.pdf', 'data/raw/policy/P020210325504120315428.pdf', 'data/raw/policy/P020201029597065666501.pdf', 'data/raw/policy/W020190905514280441190.pdf']
- `summary_007` summary reasons=judge_failed
  query: 绿色消费、汽车消费和电子产品消费政策分别提出了哪些重点措施？
  expected: 绿色消费政策要求促进绿色产品消费、扩大绿色低碳产品供给、完善绿色消费制度保障，围绕衣食住行用等领域推动消费方式绿色转型。汽车消费政策强调优化汽车限购管理、支持老旧汽车更新消费、加快培育二手车市场、加强新能源汽车配套设施建设、降低新能源汽车购置使用成本。电子产品消费政策提出加快推动电子产品升级换代，支持可穿戴设备、智能产品、虚拟现实设备等消费，完善电子产品回收体系，促进绿色智能电子产品消费。
  answer: 根据现有资料，三类消费政策的重点措施可归纳为： ### 1）绿色消费政策重点措施 - **提升食品消费绿色化水平**：完善粮食、蔬菜、水果等农产品生产、储存、运输、加工标准；推广绿色有机食品、农产品；督促餐饮企业和外卖平台落实反食品浪费要求；推动机关、企事业单位、学校等建立防止食品浪费制度，深入开展“光盘”等行动；推进厨余垃圾回收处置和资源化利用。[资料6] - **推动重点领域消费绿色转型**：全面推动吃、穿、住、行、用、游等领域绿色...
  reference_coverage: 3/3
  missing_numbers: []
  judge: {"is_correct": false, "score": 42.0, "correctness": 2.0, "completeness": 2.0, "faithfulness": 2.0, "reason": "生成答案包含部分相关措施，但大量扩展到标准答案未提及的细节和其他政策内容，且未准确覆盖标准答案的核心要点，尤其汽车消费中的二手车市场、新能源汽车配套及购车成本、电子产品中的可穿戴/智能/VR设备和回收体系表述不够集中。绿色消费部分也偏离了标准答案的概括。", "raw": "{\"is_correc...
  sources: ['data/raw/policy/P020230721357059106134.pdf', 'data/raw/policy/P020220121303052384813.pdf', 'data/raw/policy/ndrc_2024_consumer_new_scenarios.pdf', 'data/raw/policy/P020240624569333510920.pdf', 'data/raw/policy/P020230721360399538898.pdf']
- `summary_008` summary reasons=judge_failed
  query: 早期扩内需促消费政策如何通过优化供给、提升服务和改善环境来形成强大国内市场？
  expected: 政策要求顺应居民消费升级大趋势，加快转型升级提升供给质量和水平，以高质量供给催生创造新的市场需求，促进形成强大国内市场。具体包括促进汽车消费、家电和电子产品消费、农村网购和乡村旅游消费、养老托育和家政服务供给、信息消费和超高清视频产品消费；同时提出“十大扩消费行动”，围绕城镇消费、农村消费、住房租赁、汽车消费、旅游休闲、文化体育、智慧家庭、分享经济等方向，增加高品质商品和服务供给，完善商贸物流、信息网络等基础设施，打通物流和信息障碍，加强消费市场信用体系建设。
  answer: 早期扩内需促消费政策主要通过“优化供给、提升服务、改善环境”三条主线来形成强大国内市场： 1. **优化供给：以高质量供给催生新需求，推动消费升级** - 围绕汽车、家电、信息消费、绿色智能产品等领域，推动更新换代和新品供给，支持高技术水平新能源汽车、绿色智能家电、超高清视频、5G相关产品等消费。[资料1][资料5] - 提升商品和服务供给质量，发展中高端消费载体、品牌商品、老字号、离境退税商品等，增强优质供给对消费的带动作用。[资料5...
  reference_coverage: 3/3
  missing_numbers: []
  judge: {"is_correct": false, "score": 56.0, "correctness": 3.0, "completeness": 3.0, "faithfulness": 2.0, "reason": "答案抓住了“优化供给、提升服务、改善环境”这一主线，但大量加入了标准答案没有的具体措施和表述，存在明显扩展；同时对标准答案中的关键点如“十大扩消费行动”、农村网购和乡村旅游、养老托育和家政服务、超高清视频产品等覆盖不全，因此完整性和忠实性都一般。", "raw": "{\"is_correct\":...
  sources: ['data/raw/policy/W020190905514280441190.pdf', 'data/raw/policy/P020201029597065666501.pdf', 'data/raw/policy/W020190906340655425738.pdf', 'data/raw/policy/P020220121303052384813.pdf', 'data/raw/policy/P020240726413585348997.pdf']
- `summary_009` summary reasons=judge_failed
  query: 绿色低碳转型产业指导目录覆盖了哪些主要产业方向？
  expected: 目录覆盖节能降碳产业、环境保护产业、资源循环利用产业、能源绿色低碳转型、生态保护修复和利用、基础设施绿色升级、绿色服务等方向。具体包括高效节能装备制造、温室气体控制、大气水土壤和固体废弃物治理、可再生能源和清洁能源相关领域、生态农林牧渔业、绿色数据中心建设和节能改造，以及绿色低碳项目咨询设计、合同能源管理、资源循环利用第三方服务、环境污染第三方治理、能耗和温室气体监测、绿色电力交易等。
  answer: 绿色低碳转型产业指导目录（2024年版）覆盖的主要产业方向，按主题可归纳为以下几类： 1. **节能降碳产业** 主要包括： - **高效节能装备制造**，如节能锅炉、窑炉、内燃机、高效发电机组、节能电机、风机、变压器、高效照明、余热余压余气利用设备、绿色建筑材料、能源计量检测监测控制设备等 [资料1] - **先进交通装备制造**，如新能源汽车关键零部件、绿色船舶、先进轨道交通装备、先进航空装备、先进港口装卸设备等 [资料1] - *...
  reference_coverage: 1/1
  missing_numbers: []
  judge: {"is_correct": false, "score": 68.0, "correctness": 3.0, "completeness": 4.0, "faithfulness": 3.0, "reason": "答案覆盖了节能降碳、环境保护、资源循环利用、能源绿色低碳转型、绿色数据中心和绿色服务等核心方向，整体较接近标准答案；但加入了大量标准答案未明确提及的内容，如绿色交通、工业绿色转型、海绵城市等，存在一定扩展和概括偏离，因此不算完全正确。", "raw": "{\"is_correct\":false,...
  sources: ['data/raw/policy/ndrc_2024_green_low_carbon_industry_catalog.pdf', 'data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_changzhutan_green_transition_interpretation.pdf', 'data/raw/policy/P020220323314396580505.pdf', 'data/raw/policy/P020220121303052384813.pdf']
- `summary_010` summary reasons=judge_failed
  query: 数据中心绿色低碳发展专项行动计划提出了哪些目标和重点任务？
  expected: 目标是到2025年底，全国数据中心布局更加合理，整体上架率不低于60%，平均电能利用效率降至1.5以下，可再生能源利用率年均增长10%；到2030年底，平均电能利用效率、单位算力能效和碳效达到国际先进水平。重点任务包括完善“东数西算”布局，推动小规模、低效率存量分散数据中心向集约化、高效率转变；严格新上项目能效水效要求，新建及改扩建大型和超大型数据中心电能利用效率降至1.25以内，国家枢纽节点项目不得高于1.2；推进存量项目节能降碳改造；推广液冷、蒸发冷却、热管、氟泵、人工智能节能、高效供配电和高效存储等技术装备；通过激励约束、项目清单、监督管理和宣传引导推动落实。
  answer: 《数据中心绿色低碳发展专项行动计划》提出的目标和重点任务，主要可归纳为以下几方面： **一、主要目标** - **到2025年底**：全国数据中心布局更加合理，整体上架率**不低于60%**，平均电能利用效率（PUE）降至**1.5以下**，可再生能源利用率**年均增长10%**，平均单位算力能效和碳效显著提高。[资料1] - **到2030年底**：全国数据中心平均PUE、单位算力能效和碳效达到**国际先进水平**，可再生能源利用率进...
  reference_coverage: 1/1
  missing_numbers: []
  judge: {"is_correct": false, "score": 62.0, "correctness": 3.0, "completeness": 3.0, "faithfulness": 2.0, "reason": "覆盖了主要目标和部分重点任务，关键数字基本一致，但加入了不少标准答案未提到的扩展内容（如余热利用、新能源微电网、技术创新示范等），且未完整体现‘激励约束、项目清单、监督管理和宣传引导’等落实措施，存在一定偏离。", "raw": "{\"is_correct\":false,\"score\":62...
  sources: ['data/raw/policy/ndrc_2024_green_low_carbon_data_center_action_plan.pdf', 'data/raw/policy/ndrc_2024_green_low_carbon_industry_catalog.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/ndrc_unified_power_market_interview.pdf', 'data/raw/policy/P020220602315650388122.pdf']

## Metric Notes

- `answer_rate`：生成答案非空的比例。
- `citation_rate`：答案文本中显式出现 `[资料1]` 这类引用编号的比例。
- `reference_recall` / `reference_hit_all`：用生成文件保存的 `references` 对齐评测集 ground_truth 的 source/pages。
- `numeric_coverage`：标准答案中抽出的数字在生成答案中出现的比例，只在标准答案含数字的样本上统计。
- `LLM judge`：启用 `--llm-judge` 后，由模型比较问题、标准答案和生成答案，输出正确性、完整性和忠实度评分。
- 当前 judge 主要判断答案与 ground truth 的一致性；是否完全被原文支撑仍需结合引用覆盖和人工抽查。
