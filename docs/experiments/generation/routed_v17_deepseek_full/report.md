# Generation Evaluation

- evaluated_at: 2026-05-19T15:38:21
- eval_file: `data/eval/financial_qa_dev.jsonl`
- pred_file: `data/generated/eval_runs/routed_v17_deepseek_full_answers.jsonl`
- match_level: `page`
- eval_samples: 120 / 120
- skipped_eval_rows: 0
- prediction_rows: 120

## Overall

| metric | value |
|---|---:|
| generated_rate | 100.00% |
| answer_rate | 100.00% |
| citation_rate | 97.50% |
| reference_recall | 95.97% |
| reference_hit_any | 98.33% |
| reference_hit_all | 93.33% |
| numeric_coverage | 86.31% |
| numeric_count | 106 |

## By Question Type

| question_type | count | answer_rate | citation_rate | reference_recall | reference_hit_all | numeric_coverage | numeric_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| compare | 30 | 100.00% | 96.67% | 100.00% | 100.00% | 96.11% | 30 |
| fact | 70 | 100.00% | 97.14% | 97.14% | 97.14% | 86.76% | 68 |
| summary | 20 | 100.00% | 100.00% | 85.83% | 70.00% | 45.74% | 8 |

## Badcases

- `fact_007` fact reasons=number_miss
  query: 林洋能源Q1毛利率是多少？
  expected: 20.72%
  answer: 直接答案：根据现有资料无法确定林洋能源Q1毛利率。 依据：资料中未提供林洋能源Q1毛利率的具体数值。资料1为林洋能源的研报，但仅包含2025A及2026-2028E的预测收入数据，未提及毛利率；资料2和资料3分别涉及新大正和银轮股份等其他公司，与林洋能源无关。[资料1][资料2][资料3]
  reference_coverage: 1/1
  missing_numbers: ['20.72%']
  judge: None
  sources: ['data/raw/new_energy/LYNY.pdf', 'data/raw/real_estate/XDZ.pdf', 'data/raw/new_energy/LXDQ.pdf']
- `fact_021` fact reasons=no_citation,number_miss
  query: 爱尔眼科归属母公司净利润是多少
  expected: 11.81 亿元
  answer: 直接答案：32.40亿元（2025年全年归母净利润） 依据：资料[1]中明确记载：“2025年公司实现营业收入223.53亿元，同比增长6.5%；归母净利润32.40亿元，同比下降8.9%”。
  reference_coverage: 1/1
  missing_numbers: ['11.81']
  judge: None
  sources: ['data/raw/healthcare/AEYK.pdf']
- `fact_024` fact reasons=number_miss
  query: 毕得医药2024A 营业收入同比增速是多少
  expected: 0.9%
  answer: 直接答案：根据现有资料无法确定毕得医药2024A营业收入同比增速。 依据：资料中仅提供了毕得医药2024A营业收入为1,102百万元，以及2025A营业收入为1,324百万元（同比增速20.1%），但未给出2024A营业收入同比增速的具体数值。[资料2]
  reference_coverage: 1/1
  missing_numbers: ['0.9%']
  judge: None
  sources: ['data/raw/real_estate/HFGF.pdf', 'data/raw/healthcare/BDYY.pdf', 'data/raw/healthcare/TGYY.pdf', 'data/raw/consumer/DPYL.pdf', 'data/raw/semiconductor/BDT.pdf']
- `fact_028` fact reasons=number_miss
  query: 皓元医药2025年实现营收多少
  expected: 28.77亿元
  answer: 直接答案：根据现有资料无法确定皓元医药2025年实现的营收。 依据：资料中仅提供了皓元医药的财务预测表，其中“营业总收入”列显示2025A为2,877（百万元）[资料1][资料2]，但该数据为预测值（标注为“2025A”），并非实际实现的营收。资料3中提及的“2025年公司实现营收66.70亿元”对应的是凯莱英（002821.SZ），而非皓元医药[资料3]。因此，无法从现有资料中获取皓元医药2025年实际实现的营收数据。
  reference_coverage: 1/1
  missing_numbers: ['28.77']
  judge: None
  sources: ['data/raw/healthcare/HYYY.pdf', 'data/raw/healthcare/KLY.pdf']
- `fact_035` fact reasons=no_citation,number_miss
  query: 华发股份2025年营业收入同比增长多少
  expected: 38.8%
  answer: 直接答案：根据现有资料无法确定华发股份2025年营业收入同比增长率。 依据：资料中未提供华发股份2025年营业收入的具体数值或同比增速。资料1和资料2主要涉及销售金额、销售回款、现金流等指标，资料3提及营业收入但仅显示历史数据（如2020年等），未包含2025年营业收入同比增速。资料4为另一家公司（昭衍新药）的数据，与华发股份无关。
  reference_coverage: 1/1
  missing_numbers: ['38.8%']
  judge: None
  sources: ['data/raw/real_estate/HFGF.pdf', 'data/raw/healthcare/SYXY.pdf']
- `fact_036` fact reasons=number_miss
  query: 截至 2025 年末，金地集团有息负债多少
  expected: 672亿元
  answer: 直接答案：根据现有资料无法确定截至2025年末金地集团有息负债的具体金额。 依据：资料中仅提供了有息负债的增速（如“有息负债及增速”图表显示2025年同比增速为-20.5%[资料3]）和结构占比（如短期有息负债占比61%[资料1]），但未给出截至2025年末有息负债的绝对数值。
  reference_coverage: 1/1
  missing_numbers: ['672']
  judge: None
  sources: ['data/raw/real_estate/JDJT.pdf', 'data/raw/real_estate/HFGF.pdf']
- `fact_044` fact reasons=number_miss
  query: 鼎智科技的子公司东莞赛仑特2025年主营业务收入多少
  expected: 7367 万元
  answer: 直接答案：根据现有资料无法确定鼎智科技的子公司东莞赛仑特2025年主营业务收入。 依据：资料中仅提及“我们看好公司收购赛仑特实现覆盖全产业链能力”[资料1]，但未提供东莞赛仑特2025年主营业务收入的具体数字。
  reference_coverage: 1/1
  missing_numbers: ['7367']
  judge: None
  sources: ['data/raw/semiconductor/DZKJ.pdf', 'data/raw/healthcare/YKSW.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/consumer/GLDQ.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `fact_047` fact reasons=reference_not_hit_all,number_miss
  query: 2025 年，海达尔公司研发费用为多少
  expected: 1401万元
  answer: 直接答案：4,410.76 万元（2025年） 依据：根据资料1，2023-2025年，公司研发费用分别达3,548.04万元、4,139.42万元和4,410.76万元。[资料1]
  reference_coverage: 0/1
  missing_numbers: ['1401']
  judge: None
  sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/DLGF.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/healthcare/SYXY.pdf']
- `fact_049` fact reasons=reference_not_hit_all,number_miss
  query: 海光信息公司2024A销售毛利率为多少
  expected: 63.7%
  answer: 直接答案：根据现有资料无法确定海光信息公司2024A销售毛利率。 依据：所有资料中均未提及“海光信息”公司，也未出现“2024A”或“2024年”的销售毛利率数据。资料1和资料2分别涉及其他公司2025年的销售毛利率（20.71%和47.6%），资料3和资料4涉及其他公司2023-2025年的综合毛利率或毛利率，但与海光信息无关。[资料1][资料2][资料3][资料4]
  reference_coverage: 0/1
  missing_numbers: ['63.7%']
  judge: None
  sources: ['data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/new_energy/SGHN.pdf']
- `compare_005` compare reasons=number_miss
  query: 珀莱雅 vs 伊利股份，哪家公司2025年的毛利率更高
  expected: 珀莱雅。25 年珀莱雅毛利率为 73.26%，2025/2026Q1 伊利股份毛利率为 34.58%/38.37%
  answer: - 对象A（珀莱雅）：2025年毛利率为73.26%，口径为2025年全年毛利率。[资料1][资料3] - 对象B（伊利股份）：2025年毛利率为34.58%，口径为2025年全年毛利率。[资料2] 结论：珀莱雅2025年的毛利率（73.26%）高于伊利股份（34.58%）。
  reference_coverage: 2/2
  missing_numbers: ['38.37%']
  judge: None
  sources: ['data/raw/consumer/BLY.pdf', 'data/raw/consumer/YLGF.pdf', 'data/raw/healthcare/KLY.pdf']
- `compare_007` compare reasons=number_miss
  query: 普蕊斯 vs 普瑞眼科，预计哪家公司在2026年的营收更高
  expected: 普瑞眼科。普蕊斯2026E营收为931.69百万元，普瑞眼科2026E营收为3136百万元
  answer: - 对象A（普蕊斯）：2026年预计营收为931.69百万元（即9.3169亿元），口径为2026E营收预测，来源为[资料1]第3页及[资料4]第3页。 - 对象B（普瑞眼科）：根据现有资料，未提供2026年全年的营收预测数据。资料中仅提供了2025年全年营收27.97亿元（[资料2]第1页）和2026年第一季度营收8.20亿元（[资料2]第1页），但无2026年全年营收预测值。 结论：根据现有资料，普蕊斯2026年预计营收为9.316...
  reference_coverage: 2/2
  missing_numbers: ['3136']
  judge: None
  sources: ['data/raw/healthcare/PRS.pdf', 'data/raw/healthcare/PRYK.pdf']
- `compare_012` compare reasons=no_citation
  query: 亿纬锂能 vs 中国核电，哪家公司2025年的全年营业收入同比增长更多
  expected: 亿纬锂能。亿纬锂能2025年的全年营业收入同比增长26%，中国核电2025年的全年营业收入同比增长6.22%
  answer: - 亿纬锂能：2025年全年营业收入同比增长26%（资料1显示“2025年公司收入615亿元，同比+26%”） - 中国核电：2025年全年营业收入同比增长6.22%（资料2显示“2025年公司实现营业收入820.75亿元，同比增加6.22%”） 结论：亿纬锂能2025年全年营业收入同比增长26%，高于中国核电的6.22%，因此亿纬锂能同比增长更多。
  reference_coverage: 2/2
  missing_numbers: []
  judge: None
  sources: ['data/raw/new_energy/YWLN_202601.pdf', 'data/raw/new_energy/ZGHD.pdf']
- `compare_021` compare reasons=number_miss
  query: 华源控股 vs 海光信息，哪家公司2026年Q1实现营收更高
  expected: 海光信息。华源控股2026Q1 公司实现营收 5.85 亿元，海光信息2026 年一季度公司实现收入 40.34 亿元
  answer: - 华源控股：根据现有资料，无法确定华源控股2026年Q1的营收数据。资料中仅提供了华源控股2025年全年营收（23.11亿元）[资料1]以及2026-2028年全年营收预测（分别为27.21/31.10/35.37亿元）[资料4]，但未披露2026年Q1的季度营收数据。 - 海光信息：2026年Q1实现收入40.34亿元（口径：2026年一季度公司实现收入）[资料2]。 结论：根据现有资料，海光信息2026年Q1营收为40.34亿元，...
  reference_coverage: 2/2
  missing_numbers: ['5.85']
  judge: None
  sources: ['data/raw/semiconductor/HYKG.pdf', 'data/raw/semiconductor/HGXX.pdf']
- `compare_029` compare reasons=number_miss
  query: 保利发展 vs 华发股份，哪家公司2025年实现营收更高
  expected: 保利发展。保利发展2025年公司实现营业收入308144百万元，华发股份2025年实现收入834.3亿元
  answer: - 保利发展：2025年营业总收入为308,144百万元（即3081.44亿元），口径为“营业总收入（百万元）”，来自[资料1]盈利预测与估值表。 - 华发股份：2025年营业收入为83,426百万元（即834.26亿元），口径为“营业收入（百万元）”，来自[资料3]损益表。 结论：保利发展2025年营业总收入（3081.44亿元）高于华发股份2025年营业收入（834.26亿元）。
  reference_coverage: 2/2
  missing_numbers: ['834.3']
  judge: None
  sources: ['data/raw/real_estate/BLFZ.pdf', 'data/raw/real_estate/HFGF.pdf', 'data/raw/new_energy/LXDQ.pdf']
- `summary_001` summary reasons=reference_not_hit_all,number_miss
  query: 结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  expected: 主要方向包括：坚持清洁低碳、安全充裕、经济高效、供需协同、灵活智能的基本原则，2024—2027年重点开展9项专项行动，提升电网对清洁能源的接纳、配置、调控能力；健全煤电、抽水蓄能、新型储能等调节性资源容量电价机制，完善体现分时价值差异的零售市场价格机制；突破新能源高效发电利用、系统灵活调节、电网高效仿真和稳定运行控制、智能化调控等技术；通过调节能力建设优化，支撑2025—2027年年均新增2亿千瓦以上新能源合理消纳利用，全国新能源利用率不低于90%；推动新型储能到2027年基本实现规模化、市场化发展，全国装机规模达到1.8亿千瓦以上。
  answer: 1. **大规模、高比例、市场化、高质量发展**：以“大规模发展、高比例发展、市场化发展、高质量发展”为特征，实施可再生能源替代行动，提高可再生能源消纳和存储能力，加快构建新型电力系统。[资料1] 2. **电力系统调节能力优化**：建设共享储能电站，探索应用液流电池、飞轮、压缩空气储能等多种新型储能技术，提升系统层面的电力保供和新能源消纳能力。[资料2][资料4] 3. **电动汽车充电设施网络拓展**：完善充电基础设施网络布局，加强...
  reference_coverage: 2/4
  missing_numbers: ['2024', '2027', '9', '2025', '90%', '1.8']
  judge: None
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020210421528000000606.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf']
- `summary_002` summary reasons=reference_not_hit_all
  query: 新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？
  expected: 新型储能被定位为支撑新型电力系统的重要技术和基础装备。目标上，到2025年实现从商业化初期向规模化发展转变、装机规模达3000万千瓦以上，到2030年实现全面市场化发展；专项行动进一步提出到2027年基本实现规模化、市场化发展。应用场景上，鼓励电源侧、电网侧、用户侧多元发展，拓展“新能源+储能”、智能微电网、虚拟电厂等场景。技术上，坚持多元化路线，推动锂离子电池规模化应用，推动压缩空气、液流电池、钠离子电池、飞轮、氢储能、热储能等试点示范和商业化发展。市场机制上，推动储能作为独立主体参与电力市场、辅助服务市场，完善容量电价、分时电价和成本疏导机制，并健全标准体系、并网流程和安全监管。
  answer: 1. **发展目标**：到2025年，新型储能由商业化初期步入规模化发展阶段，具备大规模商业化应用条件，装机规模达3000万千瓦以上 [资料1][资料2]；到2027年，基本实现规模化、市场化发展，全国装机规模达1.8亿千瓦以上 [资料4]；到2030年，实现新型储能全面市场化发展 [资料2]。 2. **应用场景**：推进电源侧储能应用（如新能源基地、煤电机组联合运行）[资料4]；拓展电网侧储能应用（如关键电网节点独立储能电站、构网型...
  reference_coverage: 4/5
  missing_numbers: []
  judge: None
  sources: ['data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/202210114475091.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/P020210421528000346108.pdf', 'data/raw/policy/P020250106570227369979.pdf']
- `summary_003` summary reasons=reference_not_hit_all,number_miss
  query: “十四五”可再生能源规划和氢能规划分别怎样服务能源绿色低碳转型？
  expected: 可再生能源规划提出，加快发展可再生能源、实施可再生能源替代行动，是推进能源革命和构建清洁低碳、安全高效能源体系的重大举措；到2025年，可再生能源消费总量达到10亿吨标准煤左右，年发电量达到3.3万亿千瓦时左右，全国可再生能源电力总量消纳责任权重达到33%左右，非水电消纳责任权重达到18%左右。规划还要求推动绿色直供电、可再生能源供暖、非电直接利用和高比例可再生能源应用示范，健全消纳责任权重和长效机制。氢能规划将氢能界定为来源丰富、绿色低碳、应用广泛的二次能源，要求构建清洁化、低碳化、低成本的多元制氢体系，开展可再生能源制氢示范，构建安全、稳定、高效的氢能供应网络，并形成“1+N”政策体系。
  answer: 1. **“十四五”可再生能源规划**：该规划提出“实施可再生能源替代行动”，目标是“推动能源绿色低碳转型”，通过“大规模开发可再生能源”（如风电、光伏发电基地化开发）、“促进存储消纳，高比例利用可再生能源”等措施，构建“清洁低碳、安全高效能源体系”。[资料1][资料2] 2. **氢能规划**：该规划将氢能定位为“用能终端实现绿色低碳转型的重要载体”，强调“以绿色低碳为方针，加强氢能的绿色供应”，通过“推动交通、工业等用能终端的能源消...
  reference_coverage: 2/3
  missing_numbers: ['2025', '10', '3.3', '33%', '18%']
  judge: None
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020220323314396580505.pdf', 'data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/P020210421528000346108.pdf']
- `summary_004` summary reasons=reference_not_hit_all,number_miss
  query: 电网建设、电力市场和容量电价政策如何支撑新能源消纳与系统可靠运行？
  expected: 配电网政策要求适度超前建设配电网，提升承载力，满足分布式新能源和电动汽车充电基础设施发展。全国统一电力市场提出到2030年基本建成全国统一电力市场体系，市场化交易电量占全社会用电量的70%左右，并推动跨省跨区和省内联合交易。容量机制方面，煤电、抽水蓄能、新型储能等支撑性、调节性资源在高比例新能源消纳和新型电力系统中发挥重要作用，政策通过可靠容量补偿、容量市场探索和发电侧容量电价机制，保障其收益、增强电力安全保供能力。新能源报价政策则要求规范集中报价、价格预警和数字化监管，防范市场力滥用，维护市场公平竞争。
  answer: 1. **电网建设支撑新能源消纳与系统可靠运行**：通过配电网高质量发展行动，提升供电能力、抗灾能力和承载能力，针对性提升新能源、电动汽车充电设施接网能力，并建立配电网可开放容量定期发布和预警机制 [资料5]。同时，加强智慧化调度体系建设，适应大规模高比例新能源，创新新型有源配电网调度模式，提升配电网层面就地平衡能力和对主网的主动支撑能力 [资料5]。 2. **电力市场促进新能源消纳**：到2030年，电力市场促进新能源消纳的机制更加...
  reference_coverage: 1/5
  missing_numbers: ['70%']
  judge: None
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf', 'data/raw/policy/ndrc_generation_capacity_price_qna.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf']
- `summary_005` summary reasons=number_miss
  query: 大规模设备更新和消费品以旧换新政策主要支持哪些领域，资金和补贴如何安排？
  expected: 政策统筹安排3000亿元左右超长期特别国债资金，加力支持大规模设备更新和消费品以旧换新。设备更新方面，支持范围从工业、环境基础设施、交通运输、物流、教育、文旅、医疗、回收循环利用，扩大到能源电力、老旧电梯等领域设备更新以及重点行业节能降碳和安全改造，并降低申报门槛、支持中小企业设备更新。具体补贴包括老旧营运船舶报废更新、老旧营运货车报废更新、农业机械报废更新、新能源公交车及动力电池更新等。消费品方面，重点支持汽车报废更新和乘用车置换更新、家电产品和电动自行车以旧换新、旧房装修和厨卫局部改造、居家适老化改造、智能家居消费等，要求真金白银优惠直达消费者。能源设备更新另提出到2027年能源重点领域设备投资规模较2023年增长25%以上。
  answer: 1. **设备更新支持领域**：政策支持工业、环境基础设施、交通运输、物流、教育、文旅、医疗等领域设备更新及回收循环利用，并将范围扩大到能源电力、老旧电梯等领域设备更新以及重点行业节能降碳和安全改造。[资料1] 具体包括老旧营运船舶报废更新、老旧营运货车报废更新、农业机械报废更新、新能源公交车及动力电池更新。[资料1][资料2] 2. **消费品以旧换新支持领域**：支持汽车报废更新和个人消费者乘用车置换更新，以及家电产品以旧换新（冰箱...
  reference_coverage: 4/4
  missing_numbers: ['2027', '2023', '25%']
  judge: None
  sources: ['data/raw/policy/ndrc_2024_equipment_update_consumer_trade_in.pdf', 'data/raw/policy/P020240726413585348997.pdf', 'data/raw/policy/ndrc_2024_energy_equipment_update_plan.pdf', 'data/raw/policy/P020240821593575195639.pdf']
- `summary_011` summary reasons=number_miss
  query: 长三角一体化示范区和长株潭生态绿心政策如何推进区域绿色转型？
  expected: 长三角生态绿色一体化发展示范区把保护和修复生态环境摆在优先位置，要求探索生态友好型高质量发展新模式，到2025年先行启动区在生态环境保护和建设、生态友好型产业创新发展、人与自然和谐宜居等方面显示度明显提升，到2035年形成更加成熟有效的绿色一体化发展制度体系。具体包括统一国土空间规划体系、统一饮用水水源保护和主要水体生态管控制度、统一公共信用管理制度、重大改革系统集成和经验共享共用。长株潭生态绿心政策解读强调以产业结构优化为主线，构建绿色低碳经济体系，推进高耗能、高排放产能整合与退出，培育绿色智能计算、生命科技、生物制造、大健康、航空航天和时空信息等产业，并以园区绿色化、数字化、协同化转型作为载体。
  answer: 1. **长三角生态绿色一体化发展示范区**：以“生态筑底、绿色发展”为原则，锚固生态基底、厚植生态优势、发展生态经济，率先将生态优势转化为经济社会发展优势，探索生态友好型发展模式，实现绿色经济、高品质生活、可持续发展有机统一。[资料1] 2. **长株潭生态绿心**：通过《长株潭生态绿心加快绿色转型发展实施方案》，构建“源头减碳、过程控碳、生态固碳”全链条管控体系，以绿色智能交通为牵引构建低碳高效运输体系，以绿色基础设施为支撑夯实城市...
  reference_coverage: 2/2
  missing_numbers: ['2025', '2035']
  judge: None
  sources: ['data/raw/policy/P020200728576152165824.pdf', 'data/raw/policy/ndrc_changzhutan_green_transition_interpretation.pdf', 'data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf']
- `summary_012` summary reasons=reference_not_hit_all
  query: 固体废物综合治理和绿色产业体系建设如何形成全链条治理？
  expected: 固体废物综合治理强调构建全链条治理体系：健全法律法规制度体系，推动生态环境法典编纂和循环经济促进法修订，完善废弃电器电子产品回收处理、危险废物经营许可、建筑垃圾等法规规章；发挥标准牵引作用，分类制修订固体废物污染控制标准，完善资源化利用技术和产品质量标准；加强循环利用、重金属污染治理关键技术研发和重大技术装备攻关；在用地、资金、价格机制上加强保障，并坚持“谁污染、谁治理”。绿色低碳转型产业目录也把固体废弃物收集、贮存、运输及处理处置装备制造、资源循环利用第三方服务等纳入绿色产业体系。
  answer: 1. **源头减量**：通过推行绿色设计、强化工业生产精细化管控、推广尾矿就近充填回填、发展装配式建筑和绿色施工、加强农业投入品包装管理等措施，从源头减少固体废物产生。[资料1] 2. **过程管控**：完善工业固体废物管理台账制度，强化全链条跟踪管控；规范危险废物收集管理；深化生活垃圾分类网点与废旧物资回收网点“两网融合”；加强建筑工地和运输车辆信息化监管。[资料1] 3. **末端利用与无害化处置**：提升冶炼渣、建筑垃圾等综合利用...
  reference_coverage: 2/3
  missing_numbers: []
  judge: None
  sources: ['data/raw/policy/ndrc_solid_waste_governance_interpretation.pdf', 'data/raw/policy/ndrc_2024_green_low_carbon_industry_catalog.pdf', 'data/raw/policy/ndrc_changzhutan_green_transition_interpretation.pdf', 'data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020220121303052384813.pdf']
- `summary_018` summary reasons=number_miss
  query: 职业教育产教融合和教育现代化工程怎样服务产业升级与人才培养？
  expected: 职业教育产教融合政策坚持以教促产、以产助教，延伸教育链、服务产业链、支撑供应链、打造人才链、提升价值链，到2025年国家产教融合试点城市达到50个左右，建设培育1万家以上产教融合型企业。重点包括扩容产教融合储备项目，新增200所左右高职院校和应用型本科院校；完善职业教育专业设置，优先发展先进制造、新能源、新材料、生物技术、人工智能等新兴专业，加快建设护理、康养、托育、家政等紧缺专业；建设100个高水平、专业化、开放型产教融合实训基地，并通过财税、土地、信用等政策支持产教融合型企业。教育现代化工程则强调推动基本公共教育均衡发展，深化职业教育产教融合，提升高校创新人才培养能力，支持一流大学和一流学科建设与产业互动。
  answer: 1. **深化职业教育产教融合，增强产业升级的人才支撑**：通过实施职业教育产教融合工程，以实习实验实训设施建设为重点，支持职业院校和本科高校深化产教融合、校企合作，改善人才培养条件，加强实践育人，提升学生创新精神、实践水平和就业创业能力，更好服务实体经济发展。[资料3] 2. **推动产教融合赋能提升，形成良性互动格局**：到2025年，国家产教融合试点城市达到50个左右，培育1万家以上产教融合型企业，完善组合式激励政策体系，使产业需...
  reference_coverage: 2/2
  missing_numbers: ['200', '100']
  judge: None
  sources: ['data/raw/policy/W020190905516324668971.pdf', 'data/raw/policy/P020230613309060086035.pdf', 'data/raw/policy/W020191024567304692452.pdf', 'data/raw/policy/W020191104623864832390.pdf']
- `summary_020` summary reasons=reference_not_hit_all
  query: 低空经济统计分类如何界定核心产业，相关教育和人工智能政策怎样支撑新兴产业发展？
  expected: 低空经济统计分类的目的，是界定低空经济及其核心产业统计范围，统计低空经济发展规模、速度、结构，满足统计需求；分类以党中央和国务院决策部署为依据，以国内外相关统计分类标准为参考，以《国民经济行业分类》为基础，低空经济核心产业用“★”标记，行业代码用“*”标记部分活动属于低空经济及其核心产业。分类覆盖低空飞行器相关制造、低空飞行服务、低空基础设施建设、低空综合保障和服务等活动，并涉及观光游览航空服务、通用航空生产服务、体育航空运动服务、道路桥梁工程建筑、架线及设备工程建筑、电气安装、保险和会展等配套服务。支撑新兴产业方面，职业教育政策要求优先发展先进制造、新能源、新材料、生物技术、人工智能等新兴专业和实训基地，人工智能制造政策则支持工业智能体、智能排产、人机协同、预测性维护等高价值场景规模化应用。
  answer: 1. **低空经济核心产业界定**：低空经济核心产业是指“为低空飞行活动提供产品、基础设施、服务保障，以及依托低空飞行为社会公众提供服务的各类经济活动”。在统计分类中，低空经济范围包括“01 低空制造业、02 低空运营业、03 低空基建与信息服务业、04 低空配套业等4 个大类”，其中“01—03 大类中的10 个中类为低空经济核心产业”，核心产业包含“10 个中类，36 个小类”。[资料1] 2. **相关教育政策支撑**：资料中提及...
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
