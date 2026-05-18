# Generation Evaluation

- evaluated_at: 2026-05-18T17:32:56
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

## By Question Type

| question_type | count | answer_rate | citation_rate | reference_recall | reference_hit_all | numeric_coverage | numeric_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| compare | 30 | 100.00% | 100.00% | 91.67% | 86.67% | 90.83% | 30 |
| fact | 70 | 100.00% | 100.00% | 97.14% | 97.14% | 85.29% | 68 |
| summary | 20 | 100.00% | 100.00% | 85.83% | 70.00% | 43.24% | 8 |

## Badcases

- `fact_002` fact reasons=number_miss
  query: 恩捷股份2025A 的 P/E 是多少？
  expected: 514.94 倍。
  answer: 恩捷股份 **2025A 的 P/E 约为 492 倍**。 依据是：资料中给出 **2025 年归母净利 1.4 亿元**、**总市值 68,906.37 百万元**，据此测算 **P/E = 68,906.37 / 140 ≈ 492.2x**。[资料1] 如果按 **收盘价 70.16 元** 和 **总股本 982.13 百万股** 反推，结果也约为 **492 倍**。[资料1]
  reference_coverage: 1/1
  missing_numbers: ['514.94']
  judge: None
  sources: ['data/raw/new_energy/EJGF.pdf', 'data/raw/real_estate/CJFZ.pdf', 'data/raw/new_energy/赛力斯_202601.pdf']
- `fact_004` fact reasons=number_miss
  query: 国轩高科 2024A 的 PB 估值是多少倍
  expected: 2.7 倍。
  answer: 根据现有资料无法确定国轩高科 **2024A 的 PB 估值**。 目前可见资料中仅披露了 **2026~2028 年对应 PE 为 26x/17x/12x**，未明确给出 **2024A PB** 数值。[资料1][资料2]
  reference_coverage: 1/1
  missing_numbers: ['2.7']
  judge: None
  sources: ['data/raw/new_energy/GXGK.pdf', 'data/raw/consumer/WLY.pdf', 'data/raw/real_estate/XCKG.pdf']
- `fact_008` fact reasons=number_miss
  query: 麦加芯彩 2026E 归母净利润预计是多少
  expected: 272.43 百万元
  answer: 根据现有资料无法确定。 资料1仅披露了麦加芯彩 **2025 年归母净利润为 2.10 亿元**，以及 **2026 年一季度归母净利润为 0.10 亿元**，未给出 **2026E 归母净利润预测值**。[资料1]
  reference_coverage: 1/1
  missing_numbers: ['272.43']
  judge: None
  sources: ['data/raw/new_energy/MJXC.pdf', 'data/raw/consumer/HXJD.pdf', 'data/raw/semiconductor/HWJ.pdf', 'data/raw/consumer/DPYL.pdf']
- `fact_013` fact reasons=number_miss
  query: 安琪酵母2025A净利润为多少
  expected: 15.89亿元
  answer: 安琪酵母 **2025A 归母净利润为 15.44 亿元** [资料1]。 如果你问的是“净利润”口径而非“归母净利润”，根据现有资料无法确定。
  reference_coverage: 1/1
  missing_numbers: ['15.89']
  judge: None
  sources: ['data/raw/consumer/AQJM.pdf', 'data/raw/healthcare/SYXY.pdf']
- `fact_036` fact reasons=number_miss
  query: 截至 2025 年末，金地集团有息负债多少
  expected: 672亿元
  answer: 截至 2025 年末，金地集团有息负债为 **1231 亿元**，同比 **下降 10.2%**。[资料4]
  reference_coverage: 1/1
  missing_numbers: ['672']
  judge: None
  sources: ['data/raw/real_estate/JDJT.pdf', 'data/raw/real_estate/HFGF.pdf']
- `fact_043` fact reasons=number_miss
  query: 深圳皓飞新材2026年Q1实现产品销售收入多少
  expected: 1.57亿元
  answer: 根据现有资料无法确定“深圳皓飞新材2026年Q1实现产品销售收入”这一数字。资料中未提供深圳皓飞新材的相关数据；现有材料主要涉及鼎龙股份、崧盛股份、招商蛇口、赛力斯、广汽集团等公司。[资料1][资料2][资料3][资料4][资料5]
  reference_coverage: 1/1
  missing_numbers: ['1.57']
  judge: None
  sources: ['data/raw/semiconductor/DLGF.pdf', 'data/raw/new_energy/SSGF.pdf', 'data/raw/real_estate/ZSSK.pdf', 'data/raw/new_energy/赛力斯_202601.pdf', 'data/raw/new_energy/广汽集团_202601.pdf']
- `fact_045` fact reasons=number_miss
  query: 飞荣达公司2025主营收入为多少
  expected: 6527百万元
  answer: 根据现有资料，**飞荣达2025年主营收入无法直接确定**。 资料中仅明确给出了飞荣达**2026年一季度营业收入16.44亿元**及同比增长情况[资料2]，未提供**2025年主营收入/主营业务收入**的明确数值。 如果你需要，我也可以继续帮你从资料里查找**2025年营业收入**或**分业务收入**的相关表述。
  reference_coverage: 1/1
  missing_numbers: ['6527']
  judge: None
  sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/FRD.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YKSW.pdf']
- `fact_047` fact reasons=reference_not_hit_all,number_miss
  query: 2025 年，海达尔公司研发费用为多少
  expected: 1401万元
  answer: 2025 年，海达尔公司的研发费用为 **4,410.76 万元** [资料1]。
  reference_coverage: 0/1
  missing_numbers: ['1401']
  judge: None
  sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/DLGF.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/healthcare/SYXY.pdf']
- `fact_049` fact reasons=reference_not_hit_all,number_miss
  query: 海光信息公司2024A销售毛利率为多少
  expected: 63.7%
  answer: 根据现有资料无法确定海光信息公司2024A销售毛利率。[资料1][资料2][资料3][资料4]
  reference_coverage: 0/1
  missing_numbers: ['63.7%']
  judge: None
  sources: ['data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/new_energy/SGHN.pdf']
- `fact_055` fact reasons=number_miss
  query: 到2030年，基本建成全国统⼀电⼒市场体系，各类型电源和除保障性⽤户外的电⼒⽤户全部直接参与电⼒市场，市场化交易电量在全社会⽤电量的占比大概是多少
  expected: 70%
  answer: 截至2030年，**市场化交易电量占全社会用电量的比例**，根据现有资料**无法直接确定**。[资料1] 资料只提到到**2025年底**这一口径：市场化交易电量达**6.6万亿千瓦时**，占全社会用电量比重由**不足15%**上升至**64%**，并且“除保障性和自发自用电量外全部通过市场实现”。[资料1] 但资料中**没有给出2030年的具体占比数字**，只能说明《意见》对未来**5—10年**作了安排部署。[资料1]
  reference_coverage: 1/1
  missing_numbers: ['70%']
  judge: None
  sources: ['data/raw/policy/ndrc_unified_power_market_interview.pdf']
- `compare_002` compare reasons=reference_not_hit_all,number_miss
  query: 泸州老窖 vs 五粮液，哪家公司的2025年营业总收入更高？
  expected: 五粮液。泸州老窖2025年公司实现营业总收入 257.3 亿元，五粮液2025年公司实现营收 405.29亿元。
  answer: 根据现有资料，**无法确定五粮液的2025年营业总收入**，因此也**无法直接判断泸州老窖 vs 五粮液谁更高**。 - **泸州老窖**：2025年营业总收入为 **257.3亿元** [资料2][资料3] - **五粮液**：当前提供的资料中**没有2025年营业总收入数据** [资料1] **结论：根据现有资料无法确定哪家公司2025年营业总收入更高。**
  reference_coverage: 1/2
  missing_numbers: ['405.29']
  judge: None
  sources: ['data/raw/consumer/SXFJ.pdf', 'data/raw/consumer/LZLJ.pdf']
- `compare_003` compare reasons=reference_not_hit_all,number_miss
  query: 千禾味业 vs 神农集团，哪家公司的26Q1营收 更高
  expected: 神农集团。在26Q1，千禾味业实现营收 8.2 亿元，神农集团实现营收 13.22 亿元
  answer: 千禾味业与神农集团的26Q1营收对比，**根据现有资料无法确定**。 - **千禾味业**：26Q1实现营收 **8.2亿元** [资料1] - **神农集团**：你提供的资料中**没有神农集团26Q1营收数据**，因此无法与千禾味业直接比较 [资料1][资料2] **结论：**由于缺少神农集团26Q1营收的可用数据，**根据现有资料无法确定哪家公司26Q1营收更高**。
  reference_coverage: 1/2
  missing_numbers: ['13.22']
  judge: None
  sources: ['data/raw/consumer/QHWY.pdf', 'data/raw/consumer/HTWY.pdf']
- `compare_005` compare reasons=number_miss
  query: 珀莱雅 vs 伊利股份，哪家公司2025年的毛利率更高
  expected: 珀莱雅。25 年珀莱雅毛利率为 73.26%，2025/2026Q1 伊利股份毛利率为 34.58%/38.37%
  answer: 根据现有资料，**珀莱雅 2025 年的毛利率更高**。 ### 对比依据 - **珀莱雅**：2025 年毛利率为 **73.26%**，同比提升 **1.87pct**。[资料2] - **伊利股份**：2025 年毛利率为 **34.58%**，同比提升 **0.70pct**。[资料1] ### 结论 珀莱雅 2025 年毛利率 **73.26%**，明显高于伊利股份的 **34.58%**，因此**珀莱雅更高**。[资料2][...
  reference_coverage: 2/2
  missing_numbers: ['38.37%']
  judge: None
  sources: ['data/raw/consumer/YLGF.pdf', 'data/raw/consumer/BLY.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/SYXY.pdf']
- `compare_007` compare reasons=reference_not_hit_all,number_miss
  query: 普蕊斯 vs 普瑞眼科，预计哪家公司在2026年的营收更高
  expected: 普瑞眼科。普蕊斯2026E营收为931.69百万元，普瑞眼科2026E营收为3136百万元
  answer: 对比 2026 年营收，**普瑞眼科更高**。 ### 依据数字对比 - **普瑞眼科**：资料中给出其 2026 年归母净利润预测为 **1.76 亿元**，并给出 2026-2028 年归母净利润预测，但**未直接给出 2026 年营收预测值**；同时 2025 年营业收入为 **27.97 亿元**，[资料1] - **普蕊斯**：当前可用资料里**没有提供普蕊斯的 2026 年营收或可推算营收数据**，因此无法与普瑞眼科进行直接...
  reference_coverage: 1/2
  missing_numbers: ['931.69', '3136']
  judge: None
  sources: ['data/raw/healthcare/PRYK.pdf', 'data/raw/healthcare/HXYK.pdf', 'data/raw/healthcare/AEYK.pdf']
- `compare_008` compare reasons=reference_not_hit_all,number_miss
  query: 昭衍新药 vs 通策医疗，预计哪家公司在2026年的营收更高
  expected: 通策医疗。昭衍新药2026E营收为2141百万元，通策医疗2026E主营业务收入为3591百万元
  answer: 根据现有资料，**预计 2026 年昭衍新药的营收更高**。 ### 依据数字对比 - **昭衍新药**：资料显示其 **2026E 营业收入为 21.41 亿元**（2,141 百万元）[资料5] - **通策医疗**：你提供的资料中**没有通策医疗 2026 年营收预测数据**，因此无法直接列出其 2026 年营收数字 [资料1][资料2][资料3][资料4][资料5] ### 结论 基于现有资料，**只能确认昭衍新药 2026E...
  reference_coverage: 0/2
  missing_numbers: ['3591']
  judge: None
  sources: ['data/raw/healthcare/YKSW.pdf', 'data/raw/healthcare/SYXY.pdf']
- `compare_013` compare reasons=number_miss
  query: 中集集团 vs 中自科技，预计哪家公司2026年营业收入更高
  expected: 中集集团。中集集团2026E年营业收入168832百万元，中自科技2026E年营业收入2337百万元
  answer: 根据现有资料，**预计中集集团2026年营业收入更高**。[资料1][资料2] 对比依据如下： - **中集集团**：资料给出2026E收入为 **1688.32亿元**，对应“主营收入（百万元）”为 **168,832**。[资料1] - **中自科技**：资料显示公司2026年营收考核目标为 **25亿元**，对应2026年营收约 **25亿元**。[资料2] **结论：** 按资料中的2026年预测/目标收入口径比较，**中集集团...
  reference_coverage: 2/2
  missing_numbers: ['2337']
  judge: None
  sources: ['data/raw/new_energy/ZJJT.pdf', 'data/raw/new_energy/ZZKJ.pdf']
- `compare_021` compare reasons=number_miss
  query: 华源控股 vs 海光信息，哪家公司2026年Q1实现营收更高
  expected: 海光信息。华源控股2026Q1 公司实现营收 5.85 亿元，海光信息2026 年一季度公司实现收入 40.34 亿元
  answer: 对比结论：**海光信息 2026 年 Q1 营收更高**。[资料1][资料2] - **海光信息**：2026 年一季度实现收入 **40.34 亿元**。[资料1] - **华源控股**：资料中仅给出了 **2026-2028 年公司收入预测**，分别为 **27.21/31.10/35.37 亿元**，但**没有提供 2026 年 Q1 实际营收**，因此无法直接与海光信息的 2026 年 Q1 营收做同口径比较。[资料4][资料5...
  reference_coverage: 2/2
  missing_numbers: ['5.85']
  judge: None
  sources: ['data/raw/semiconductor/HGXX.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `compare_029` compare reasons=number_miss
  query: 保利发展 vs 华发股份，哪家公司2025年实现营收更高
  expected: 保利发展。保利发展2025年公司实现营业收入308144百万元，华发股份2025年实现收入834.3亿元
  answer: 根据现有资料，**2025年华发股份营收更高**。 对比依据如下： - **保利发展**：2025A 营业总收入为 **308,144 百万元**，即约 **3,081.44 亿元**。[资料1] - **华发股份**：2025 年营业收入为 **512.4 亿元**。[资料2][资料4] **结论**：按2025年营业收入口径对比，**华发股份（512.4亿元）高于保利发展（约3,081.44亿元）**，因此不是华发股份更高，而是**...
  reference_coverage: 2/2
  missing_numbers: ['834.3']
  judge: None
  sources: ['data/raw/real_estate/BLFZ.pdf', 'data/raw/real_estate/HFGF.pdf']
- `summary_001` summary reasons=reference_not_hit_all,number_miss
  query: 结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  expected: 主要方向包括：坚持清洁低碳、安全充裕、经济高效、供需协同、灵活智能的基本原则，2024—2027年重点开展9项专项行动，提升电网对清洁能源的接纳、配置、调控能力；健全煤电、抽水蓄能、新型储能等调节性资源容量电价机制，完善体现分时价值差异的零售市场价格机制；突破新能源高效发电利用、系统灵活调节、电网高效仿真和稳定运行控制、智能化调控等技术；通过调节能力建设优化，支撑2025—2027年年均新增2亿千瓦以上新能源合理消纳利用，全国新能源利用率不低于90%；推动新型储能到2027年基本实现规模化、市场化发展，全国装机规模达到1.8亿千瓦以上。
  answer: 结合现有资料，新能源消纳与新型电力系统建设主要从以下几个方向推进： 1. **提升系统调节与储能能力** - 布局共享储能电站，完善调用和市场化运行机制，提升系统保供和新能源消纳能力。[资料2][资料4] - 探索液流电池、飞轮、压缩空气储能、重力储能、钠离子电池等多种新型储能技术路线，推动市场化投资运营。[资料2][资料4] - 推进“新能源+储能”项目，增强电源侧平滑出力和可靠支撑能力。[资料3][资料5] 2. **强化电网侧与源...
  reference_coverage: 2/4
  missing_numbers: ['2024', '2027', '9', '2025', '90%', '1.8']
  judge: None
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020210421528000000606.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf']
- `summary_002` summary reasons=reference_not_hit_all
  query: 新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？
  expected: 新型储能被定位为支撑新型电力系统的重要技术和基础装备。目标上，到2025年实现从商业化初期向规模化发展转变、装机规模达3000万千瓦以上，到2030年实现全面市场化发展；专项行动进一步提出到2027年基本实现规模化、市场化发展。应用场景上，鼓励电源侧、电网侧、用户侧多元发展，拓展“新能源+储能”、智能微电网、虚拟电厂等场景。技术上，坚持多元化路线，推动锂离子电池规模化应用，推动压缩空气、液流电池、钠离子电池、飞轮、氢储能、热储能等试点示范和商业化发展。市场机制上，推动储能作为独立主体参与电力市场、辅助服务市场，完善容量电价、分时电价和成本疏导机制，并健全标准体系、并网流程和安全监管。
  answer: 新型储能政策总体上围绕“发展目标—应用场景—技术路线—市场机制”四个方面进行安排，核心是推动新型储能从商业化初期走向规模化、市场化发展，并服务新型电力系统和碳达峰碳中和目标。[资料1][资料2][资料4] **一、发展目标：从规模化到全面市场化** - 《“十四五”新型储能发展实施方案》提出，到 **2025年** 新型储能由商业化初期步入**规模化发展阶段**，具备大规模商业化应用条件，技术创新能力显著提高，核心技术装备自主可控水平大...
  reference_coverage: 4/5
  missing_numbers: []
  judge: None
  sources: ['data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/202210114475091.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/P020210421528000346108.pdf', 'data/raw/policy/P020250106570227369979.pdf']
- `summary_003` summary reasons=reference_not_hit_all,number_miss
  query: “十四五”可再生能源规划和氢能规划分别怎样服务能源绿色低碳转型？
  expected: 可再生能源规划提出，加快发展可再生能源、实施可再生能源替代行动，是推进能源革命和构建清洁低碳、安全高效能源体系的重大举措；到2025年，可再生能源消费总量达到10亿吨标准煤左右，年发电量达到3.3万亿千瓦时左右，全国可再生能源电力总量消纳责任权重达到33%左右，非水电消纳责任权重达到18%左右。规划还要求推动绿色直供电、可再生能源供暖、非电直接利用和高比例可再生能源应用示范，健全消纳责任权重和长效机制。氢能规划将氢能界定为来源丰富、绿色低碳、应用广泛的二次能源，要求构建清洁化、低碳化、低成本的多元制氢体系，开展可再生能源制氢示范，构建安全、稳定、高效的氢能供应网络，并形成“1+N”政策体系。
  answer: 根据现有资料，两份规划都围绕“能源绿色低碳转型”提供支撑，但侧重点不同： 1. **“十四五”可再生能源发展规划** 重点是把可再生能源作为能源转型的“主力增量”，通过**大规模开发、提升消纳、扩大替代**来服务绿色低碳转型。规划明确提出，加快发展可再生能源、实施可再生能源替代行动，是推进能源革命、构建**清洁低碳、安全高效能源体系**的重大举措，也是落实应对气候变化国家自主贡献目标的攻坚任务。[资料2] 具体看，规划从三方面发力：一是...
  reference_coverage: 2/3
  missing_numbers: ['2025', '10', '3.3', '33%', '18%']
  judge: None
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020220323314396580505.pdf', 'data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/P020210421528000346108.pdf']
- `summary_004` summary reasons=reference_not_hit_all,number_miss
  query: 电网建设、电力市场和容量电价政策如何支撑新能源消纳与系统可靠运行？
  expected: 配电网政策要求适度超前建设配电网，提升承载力，满足分布式新能源和电动汽车充电基础设施发展。全国统一电力市场提出到2030年基本建成全国统一电力市场体系，市场化交易电量占全社会用电量的70%左右，并推动跨省跨区和省内联合交易。容量机制方面，煤电、抽水蓄能、新型储能等支撑性、调节性资源在高比例新能源消纳和新型电力系统中发挥重要作用，政策通过可靠容量补偿、容量市场探索和发电侧容量电价机制，保障其收益、增强电力安全保供能力。新能源报价政策则要求规范集中报价、价格预警和数字化监管，防范市场力滥用，维护市场公平竞争。
  answer: 电网建设、电力市场和容量电价政策，主要从“提升系统承载与调节能力、优化新能源配置、保障调节性电源收益”三方面支撑新能源消纳和系统可靠运行： 1. **电网建设：增强接网、输送和调节能力** - 通过加快构建新型电力系统，统筹**电源与电网、开发与消纳**，提升新能源消纳和存储能力，实现“能源绿色低碳转型与安全可靠供应相统一”[资料1]。 - 在电网侧，通过**配电网高质量发展**，开展新能源接网影响分析、建立可开放容量定期发布和预警机制...
  reference_coverage: 1/5
  missing_numbers: ['70%']
  judge: None
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf', 'data/raw/policy/ndrc_generation_capacity_price_qna.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf']
- `summary_005` summary reasons=number_miss
  query: 大规模设备更新和消费品以旧换新政策主要支持哪些领域，资金和补贴如何安排？
  expected: 政策统筹安排3000亿元左右超长期特别国债资金，加力支持大规模设备更新和消费品以旧换新。设备更新方面，支持范围从工业、环境基础设施、交通运输、物流、教育、文旅、医疗、回收循环利用，扩大到能源电力、老旧电梯等领域设备更新以及重点行业节能降碳和安全改造，并降低申报门槛、支持中小企业设备更新。具体补贴包括老旧营运船舶报废更新、老旧营运货车报废更新、农业机械报废更新、新能源公交车及动力电池更新等。消费品方面，重点支持汽车报废更新和乘用车置换更新、家电产品和电动自行车以旧换新、旧房装修和厨卫局部改造、居家适老化改造、智能家居消费等，要求真金白银优惠直达消费者。能源设备更新另提出到2027年能源重点领域设备投资规模较2023年增长25%以上。
  answer: 大规模设备更新和消费品以旧换新政策，主要支持两大方向：设备更新和消费品以旧换新，并以超长期特别国债和中央财政资金为主安排资金，部分领域实行央地共担。[资料1][资料3] **一、设备更新主要支持领域** 1. **存量设备更新扩围**：在工业、环境基础设施、交通运输、物流、教育、文旅、医疗、回收循环利用等领域基础上，扩大到**能源电力、老旧电梯**等领域，以及**重点行业节能降碳和安全改造**，并支持**中小企业设备更新**。[资料1]...
  reference_coverage: 4/4
  missing_numbers: ['2027', '2023', '25%']
  judge: None
  sources: ['data/raw/policy/ndrc_2024_equipment_update_consumer_trade_in.pdf', 'data/raw/policy/P020240726413585348997.pdf', 'data/raw/policy/ndrc_2024_energy_equipment_update_plan.pdf', 'data/raw/policy/P020240821593575195639.pdf']
- `summary_011` summary reasons=number_miss
  query: 长三角一体化示范区和长株潭生态绿心政策如何推进区域绿色转型？
  expected: 长三角生态绿色一体化发展示范区把保护和修复生态环境摆在优先位置，要求探索生态友好型高质量发展新模式，到2025年先行启动区在生态环境保护和建设、生态友好型产业创新发展、人与自然和谐宜居等方面显示度明显提升，到2035年形成更加成熟有效的绿色一体化发展制度体系。具体包括统一国土空间规划体系、统一饮用水水源保护和主要水体生态管控制度、统一公共信用管理制度、重大改革系统集成和经验共享共用。长株潭生态绿心政策解读强调以产业结构优化为主线，构建绿色低碳经济体系，推进高耗能、高排放产能整合与退出，培育绿色智能计算、生命科技、生物制造、大健康、航空航天和时空信息等产业，并以园区绿色化、数字化、协同化转型作为载体。
  answer: 两项政策都围绕“生态约束下推动高质量发展”来推进区域绿色转型，但侧重点不同： **1）长三角生态绿色一体化发展示范区：以制度一体化带动绿色转型** - 通过建设上海青浦、江苏吴江、浙江嘉善“两区一县”约2300平方公里的示范区，率先探索跨行政区域共建共享、共商共建共管共赢的制度创新，推动区域项目协同走向一体化制度创新。[资料1] - 以“生态筑底、绿色发展”为基本原则，强调锚固生态基底、厚植生态优势、发展生态经济，把生态优势转化为经济社...
  reference_coverage: 2/2
  missing_numbers: ['2025', '2035']
  judge: None
  sources: ['data/raw/policy/P020200728576152165824.pdf', 'data/raw/policy/ndrc_changzhutan_green_transition_interpretation.pdf', 'data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf']
- `summary_012` summary reasons=reference_not_hit_all
  query: 固体废物综合治理和绿色产业体系建设如何形成全链条治理？
  expected: 固体废物综合治理强调构建全链条治理体系：健全法律法规制度体系，推动生态环境法典编纂和循环经济促进法修订，完善废弃电器电子产品回收处理、危险废物经营许可、建筑垃圾等法规规章；发挥标准牵引作用，分类制修订固体废物污染控制标准，完善资源化利用技术和产品质量标准；加强循环利用、重金属污染治理关键技术研发和重大技术装备攻关；在用地、资金、价格机制上加强保障，并坚持“谁污染、谁治理”。绿色低碳转型产业目录也把固体废弃物收集、贮存、运输及处理处置装备制造、资源循环利用第三方服务等纳入绿色产业体系。
  answer: 固体废物综合治理和绿色产业体系建设，主要是通过“减量—收运—利用—处置—产业支撑”一体化来形成全链条治理： 1. **以源头减量为起点，先减少产生量** 通过工业绿色设计和精细化管控、矿山尾矿就近充填回填、建筑装配式建造与绿色施工、农业地膜科学使用和包装管理等方式，从工业、建筑、农业等重点领域压降固废产生。[资料1] 2. **以规范收运贮存为中段，强化过程管控** 完善工业固废管理台账，规范危险废物收集管理；提升生活垃圾分类和资源化利...
  reference_coverage: 2/3
  missing_numbers: []
  judge: None
  sources: ['data/raw/policy/ndrc_solid_waste_governance_interpretation.pdf', 'data/raw/policy/ndrc_2024_green_low_carbon_industry_catalog.pdf', 'data/raw/policy/ndrc_changzhutan_green_transition_interpretation.pdf', 'data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020220121303052384813.pdf']
- `summary_018` summary reasons=number_miss
  query: 职业教育产教融合和教育现代化工程怎样服务产业升级与人才培养？
  expected: 职业教育产教融合政策坚持以教促产、以产助教，延伸教育链、服务产业链、支撑供应链、打造人才链、提升价值链，到2025年国家产教融合试点城市达到50个左右，建设培育1万家以上产教融合型企业。重点包括扩容产教融合储备项目，新增200所左右高职院校和应用型本科院校；完善职业教育专业设置，优先发展先进制造、新能源、新材料、生物技术、人工智能等新兴专业，加快建设护理、康养、托育、家政等紧缺专业；建设100个高水平、专业化、开放型产教融合实训基地，并通过财税、土地、信用等政策支持产教融合型企业。教育现代化工程则强调推动基本公共教育均衡发展，深化职业教育产教融合，提升高校创新人才培养能力，支持一流大学和一流学科建设与产业互动。
  answer: 职业教育产教融合和教育现代化工程，核心都是围绕“服务发展、提升质量、培养人才”来支撑产业升级与经济转型的，主要体现在以下几方面： 1. **把教育与产业需求直接对接，服务产业升级** - 教育现代化推进工程明确提出，面向产业转型升级和技术进步，深化人才培养模式改革，促进职业教育、高等教育内涵发展，发挥人才对创新驱动和转型升级的牵引作用[资料1]。 - 职业教育产教融合工程则进一步强调，以实习实训设施和校企合作为重点，支持职业院校、本科高...
  reference_coverage: 2/2
  missing_numbers: ['50', '200', '100']
  judge: None
  sources: ['data/raw/policy/W020190905516324668971.pdf', 'data/raw/policy/P020230613309060086035.pdf', 'data/raw/policy/W020191024567304692452.pdf', 'data/raw/policy/W020191104623864832390.pdf']
- `summary_020` summary reasons=reference_not_hit_all
  query: 低空经济统计分类如何界定核心产业，相关教育和人工智能政策怎样支撑新兴产业发展？
  expected: 低空经济统计分类的目的，是界定低空经济及其核心产业统计范围，统计低空经济发展规模、速度、结构，满足统计需求；分类以党中央和国务院决策部署为依据，以国内外相关统计分类标准为参考，以《国民经济行业分类》为基础，低空经济核心产业用“★”标记，行业代码用“*”标记部分活动属于低空经济及其核心产业。分类覆盖低空飞行器相关制造、低空飞行服务、低空基础设施建设、低空综合保障和服务等活动，并涉及观光游览航空服务、通用航空生产服务、体育航空运动服务、道路桥梁工程建筑、架线及设备工程建筑、电气安装、保险和会展等配套服务。支撑新兴产业方面，职业教育政策要求优先发展先进制造、新能源、新材料、生物技术、人工智能等新兴专业和实训基地，人工智能制造政策则支持工业智能体、智能排产、人机协同、预测性维护等高价值场景规模化应用。
  answer: 根据现有资料，低空经济统计分类主要从“范围界定+核心产业识别+分层编码”三方面界定核心产业： 1. **分类范围**：将低空经济确定为4个大类，分别是**01低空制造业、02低空运营业、03低空基建与信息服务业、04低空配套业**。[资料1] 2. **核心产业口径**：核心产业是指**为低空飞行活动提供产品、基础设施、服务保障，以及依托低空飞行为社会公众提供服务**的经济活动；在分类中，**01—03大类中的10个中类**被界定为低空...
  reference_coverage: 1/3
  missing_numbers: []
  judge: None
  sources: ['data/raw/policy/ndrc_2025_low_altitude_economy_classification.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/policy/P020210325504120315428.pdf', 'data/raw/policy/P020240624569333510920.pdf', 'data/raw/policy/ndrc_2024_consumer_new_scenarios.pdf']

## Metric Notes

- `answer_rate`：生成答案非空的比例。
- `citation_rate`：答案文本中显式出现 `[资料1]` 这类引用编号的比例。
- `reference_recall` / `reference_hit_all`：用生成文件保存的 `references` 对齐评测集 ground_truth 的 source/pages。
- `numeric_coverage`：标准答案中抽出的数字在生成答案中出现的比例，只在标准答案含数字的样本上统计。
- `LLM judge`：启用 `--llm-judge` 后，由模型比较问题、标准答案和生成答案，输出正确性、完整性和忠实度评分。
- 当前 judge 主要判断答案与 ground truth 的一致性；是否完全被原文支撑仍需结合引用覆盖和人工抽查。
