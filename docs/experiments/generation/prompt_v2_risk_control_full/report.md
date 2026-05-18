# Generation Evaluation

- evaluated_at: 2026-05-18T23:48:23
- eval_file: `data/eval/financial_qa_dev.jsonl`
- pred_file: `data/generated/eval_runs/prompt_v2_risk_control_full_answers.jsonl`
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
| numeric_coverage | 81.11% |
| numeric_count | 106 |

## By Question Type

| question_type | count | answer_rate | citation_rate | reference_recall | reference_hit_all | numeric_coverage | numeric_count |
|---|---:|---:|---:|---:|---:|---:|---:|
| compare | 30 | 100.00% | 100.00% | 91.67% | 86.67% | 80.06% | 30 |
| fact | 70 | 100.00% | 100.00% | 97.14% | 97.14% | 86.76% | 68 |
| summary | 20 | 100.00% | 100.00% | 85.83% | 70.00% | 36.99% | 8 |

## Badcases

- `fact_007` fact reasons=number_miss
  query: 林洋能源Q1毛利率是多少？
  expected: 20.72%
  answer: 直接答案：根据现有资料无法确定林洋能源 Q1 毛利率。 依据：资料中只有林洋能源的业绩预测和主营收入信息，没有出现“Q1 毛利率”这一指标的直接数值；Q1 毛利率数值只在资料2中对应的是“新大正”而非林洋能源，不能替代。[资料1][资料2]
  reference_coverage: 1/1
  missing_numbers: ['20.72%']
  judge: None
  sources: ['data/raw/new_energy/LYNY.pdf', 'data/raw/real_estate/XDZ.pdf', 'data/raw/new_energy/LXDQ.pdf']
- `fact_021` fact reasons=number_miss
  query: 爱尔眼科归属母公司净利润是多少
  expected: 11.81 亿元
  answer: 直接答案：32.40 亿元，2025 年[资料1] 依据：2025 年公司实现归母净利润 32.40 亿元；资料中未提供其他与问题更完全匹配的“归属母公司净利润”口径。[资料1]
  reference_coverage: 1/1
  missing_numbers: ['11.81']
  judge: None
  sources: ['data/raw/healthcare/AEYK.pdf']
- `fact_028` fact reasons=number_miss
  query: 皓元医药2025年实现营收多少
  expected: 28.77亿元
  answer: 直接答案：2025年实现营收66.70亿元。 依据：资料中明确写明“2025 年公司实现营收66.70 亿元（+14.91%）”。[资料3]
  reference_coverage: 1/1
  missing_numbers: ['28.77']
  judge: None
  sources: ['data/raw/healthcare/HYYY.pdf', 'data/raw/healthcare/KLY.pdf']
- `fact_035` fact reasons=number_miss
  query: 华发股份2025年营业收入同比增长多少
  expected: 38.8%
  answer: 直接答案：2025年营业收入同比增长**19.4%**。 依据：资料中“营业收入及增速”显示，**2025年**华发股份营业收入对应增速为**19.4%**。[资料3]
  reference_coverage: 1/1
  missing_numbers: ['38.8%']
  judge: None
  sources: ['data/raw/real_estate/HFGF.pdf', 'data/raw/healthcare/SYXY.pdf']
- `fact_036` fact reasons=number_miss
  query: 截至 2025 年末，金地集团有息负债多少
  expected: 672亿元
  answer: 直接答案：根据现有资料无法确定“截至 2025 年末，金地集团有息负债”的具体金额；资料仅明确给出了“截至 2025 年末，金地集团有息负债中短期有息负债占比为 61%，长期有息负债占比为 39%”，但未直接给出有息负债总额。[资料1] 依据：图表12 仅显示“截至2025年末，金地集团有息负债中短期有息负债占比为61%（长期为39%）”，未见有息负债总额数字；资料中出现的“有息负债（亿元）”仅对应 2021-2024 年数值，未显示...
  reference_coverage: 1/1
  missing_numbers: ['672']
  judge: None
  sources: ['data/raw/real_estate/JDJT.pdf', 'data/raw/real_estate/HFGF.pdf']
- `fact_044` fact reasons=number_miss
  query: 鼎智科技的子公司东莞赛仑特2025年主营业务收入多少
  expected: 7367 万元
  answer: 直接答案：根据现有资料无法确定“东莞赛仑特”2025年主营业务收入的具体数字，资料中未披露该子公司该口径的收入。 依据：资料中仅披露了鼎智科技2025年整体营收、海外营收和机器人项目收入等信息，未找到“东莞赛仑特”2025年主营业务收入的明确数值。[资料1]
  reference_coverage: 1/1
  missing_numbers: ['7367']
  judge: None
  sources: ['data/raw/semiconductor/DZKJ.pdf', 'data/raw/healthcare/YKSW.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/consumer/GLDQ.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `fact_045` fact reasons=number_miss
  query: 飞荣达公司2025主营收入为多少
  expected: 6527百万元
  answer: 直接答案：2025年主营收入为14.11亿元。 依据：资料中写明“2025 年实现营收14.11 亿元”，对应飞荣达公司2025年营收口径。[资料1]
  reference_coverage: 1/1
  missing_numbers: ['6527']
  judge: None
  sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/FRD.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YKSW.pdf']
- `fact_047` fact reasons=reference_not_hit_all,number_miss
  query: 2025 年，海达尔公司研发费用为多少
  expected: 1401万元
  answer: 直接答案：4,410.76 万元 依据：资料中明确写明“2023-2025 年，公司研发费用分别达3,548.04 万元、4,139.42 万元和4,410.76 万元”，因此 2025 年海达尔公司研发费用为 4,410.76 万元。[资料1]
  reference_coverage: 0/1
  missing_numbers: ['1401']
  judge: None
  sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/DLGF.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/healthcare/SYXY.pdf']
- `fact_049` fact reasons=reference_not_hit_all,number_miss
  query: 海光信息公司2024A销售毛利率为多少
  expected: 63.7%
  answer: 直接答案：根据现有资料无法确定海光信息公司 **2024A 销售毛利率**。 依据：可用资料中仅找到 **2025 年** 的公司整体销售毛利率 **20.71%**，以及其他公司/其他年份的毛利率信息，未见海光信息公司 **2024A** 销售毛利率的直接对应数值。[资料1][资料2][资料3][资料4]
  reference_coverage: 0/1
  missing_numbers: ['63.7%']
  judge: None
  sources: ['data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/new_energy/SGHN.pdf']
- `compare_001` compare reasons=number_miss
  query: 劲仔食品 vs 青岛啤酒，2026Q1营业总收入哪个高
  expected: 青岛啤酒营业总收入更高。劲仔食品26Q1实现收入7.39 亿元，青岛啤酒2026Q1 营业总收入 102.9 亿元。
  answer: - 对象A（劲仔食品）：根据现有资料，**未检索到劲仔食品 2026Q1 营业总收入**的直接数字；资料中仅有**2025A 营业收入 24.43 亿元**、**2026E 营业收入 30.09 亿元**等预测/年度数据，不能替代 2026Q1 实际值。[资料3] - 对象B（青岛啤酒）：**2026Q1 营业总收入 102.9 亿元**，口径为“营业总收入”，时间为 2026Q1。[资料1][资料2] 结论：**根据现有资料无法直接比...
  reference_coverage: 2/2
  missing_numbers: ['7.39']
  judge: None
  sources: ['data/raw/consumer/QDPJ.pdf', 'data/raw/consumer/JZSP.pdf']
- `compare_002` compare reasons=reference_not_hit_all,number_miss
  query: 泸州老窖 vs 五粮液，哪家公司的2025年营业总收入更高？
  expected: 五粮液。泸州老窖2025年公司实现营业总收入 257.3 亿元，五粮液2025年公司实现营收 405.29亿元。
  answer: - 对象A：泸州老窖，2025A 营业总收入为 **25,731 百万元**（即资料原文口径的“营业总收入（百万元）”），引用见 **[资料2]**。 - 对象B：五粮液，**根据现有资料无法确定其 2025 年“营业总收入”**。现有资料仅给出了五粮液在可比公司估值表中的数值，但未明确对应“营业总收入（2025A）”这一指标口径，因此不能直接用于与泸州老窖比较，引用见 **[资料1]、[资料2]**。 结论：**根据现有资料无法确定哪...
  reference_coverage: 1/2
  missing_numbers: ['257.3', '405.29']
  judge: None
  sources: ['data/raw/consumer/SXFJ.pdf', 'data/raw/consumer/LZLJ.pdf']
- `compare_003` compare reasons=reference_not_hit_all,number_miss
  query: 千禾味业 vs 神农集团，哪家公司的26Q1营收 更高
  expected: 神农集团。在26Q1，千禾味业实现营收 8.2 亿元，神农集团实现营收 13.22 亿元
  answer: - 对象A：千禾味业 26Q1 营收 **8.2 亿元**，口径为“26Q1公司实现营收”，引用：[资料1] - 对象B：神农集团 **根据现有资料无法确定** 26Q1 营收。当前提供的资料中未出现神农集团26Q1营收的直接数据，且可用资料主要为千禾味业与海天味业相关内容，没有神农集团对应口径的营收数字引用。 结论：**根据现有资料无法比较千禾味业与神农集团哪家26Q1营收更高**，因为缺少神农集团26Q1营收这一同口径数据。
  reference_coverage: 1/2
  missing_numbers: ['13.22']
  judge: None
  sources: ['data/raw/consumer/QHWY.pdf', 'data/raw/consumer/HTWY.pdf']
- `compare_005` compare reasons=number_miss
  query: 珀莱雅 vs 伊利股份，哪家公司2025年的毛利率更高
  expected: 珀莱雅。25 年珀莱雅毛利率为 73.26%，2025/2026Q1 伊利股份毛利率为 34.58%/38.37%
  answer: - 对象A：珀莱雅，2025 年毛利率为 **73.26%**；口径为“2025 年公司毛利率”；引用：[资料2] - 对象B：伊利股份，2025 年毛利率为 **34.58%**；口径为“2025/2026Q1 公司毛利率”中的 2025 年值；引用：[资料1] 结论：**珀莱雅 2025 年的毛利率更高**，因为 **73.26% > 34.58%**。[资料2][资料1]
  reference_coverage: 2/2
  missing_numbers: ['38.37%']
  judge: None
  sources: ['data/raw/consumer/YLGF.pdf', 'data/raw/consumer/BLY.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/SYXY.pdf']
- `compare_006` compare reasons=number_miss
  query: 凯莱英 vs 美年健康，哪家公司2025年的归母净利润更高
  expected: 凯莱英。凯莱英2025年归母净利润 11.33 亿元，美年健康2025年归母净利润2.85 亿元。
  answer: - 对象A（凯莱英）：2025 年归母净利润 **11.33 亿元**，口径为“归母净利润”，时间为 2025 年；依据资料中“2025 年公司实现营收66.70 亿元（+14.91%），归母净利润11.33 亿元（+19.35%）”以及预测表“归母净利润亿元 | 25A: 11.33” [资料2] - 对象B（美年健康）：2025 年归母净利润 **285.33 百万元**，口径为“归母净利润”，时间为 2025A；依据资料中“盈利预...
  reference_coverage: 2/2
  missing_numbers: ['2.85']
  judge: None
  sources: ['data/raw/healthcare/KLY.pdf', 'data/raw/real_estate/ZGGM.pdf', 'data/raw/healthcare/MNJK.pdf']
- `compare_007` compare reasons=reference_not_hit_all,number_miss
  query: 普蕊斯 vs 普瑞眼科，预计哪家公司在2026年的营收更高
  expected: 普瑞眼科。普蕊斯2026E营收为931.69百万元，普瑞眼科2026E营收为3136百万元
  answer: - 对象A：**普蕊斯**，根据现有资料**无法确定其2026年营收预测**。资料2中仅给出了“2026-2028年EPS分别为0.66元、0.76元、0.89元”，以及“营业收入（百万元）: PB; 4139.16: 2.80; 4451.57: 2.64; 4856.68: 2.48; 5351.50: 2.32”，但未明确对应公司为“普蕊斯”，且没有直接给出普蕊斯2026年营业收入数字。[资料2] - 对象B：**普瑞眼科**，2...
  reference_coverage: 1/2
  missing_numbers: ['931.69', '3136']
  judge: None
  sources: ['data/raw/healthcare/PRYK.pdf', 'data/raw/healthcare/HXYK.pdf', 'data/raw/healthcare/AEYK.pdf']
- `compare_008` compare reasons=reference_not_hit_all,number_miss
  query: 昭衍新药 vs 通策医疗，预计哪家公司在2026年的营收更高
  expected: 通策医疗。昭衍新药2026E营收为2141百万元，通策医疗2026E主营业务收入为3591百万元
  answer: - 对象A（昭衍新药）：资料中可直接匹配到的是 **2026E 营业收入 1,943 百万元**，口径为“营业收入(百万元)”；但该数值只出现在 [资料5] 中，而且对应的是昭衍新药的预测表述。**引用**：[资料5] - 对象B（通策医疗）：**根据现有资料无法确定**通策医疗 **2026 年营业收入** 的同口径数字；提供的资料中未出现通策医疗的 2026E 营业收入预测。**引用**：无 结论：**根据现有资料无法判断昭衍新药...
  reference_coverage: 0/2
  missing_numbers: ['2141', '3591']
  judge: None
  sources: ['data/raw/healthcare/YKSW.pdf', 'data/raw/healthcare/SYXY.pdf']
- `compare_010` compare reasons=number_miss
  query: 药康生物 vs 药明康德，哪家公司2025年的全年营业收入同比增长更多
  expected: 药明康德。药康生物2025年的全年营业收入同比增长15.51%，药明康德2025年的全年营业收入同比增长15.8%
  answer: - 对象A：药康生物 2025年全年营业收入同比增长率为 **10.39%**，口径为“营业收入同比增长率（%）/2025”；引用：[资料5] - 对象B：药明康德 2025年全年营业收入同比增长率为 **15.8%**，口径为“营业收入(+/-%)/2025”；引用：[资料1] 结论：**药明康德**2025年的全年营业收入同比增长更多，因为 **15.8% > 10.39%**。[资料1][资料5]
  reference_coverage: 2/2
  missing_numbers: ['15.51%']
  judge: None
  sources: ['data/raw/healthcare/YMKD.pdf', 'data/raw/healthcare/TGYY.pdf', 'data/raw/healthcare/BTGF.pdf', 'data/raw/healthcare/YKSW.pdf']
- `compare_011` compare reasons=number_miss
  query: 威贸电子 vs 欣旺达，哪家公司2025 年营收更高
  expected: 欣旺达。威贸电子2025 年公司实现营业收入 2.88 亿元，欣旺达公司 25 年营收 632 亿元
  answer: - 对象A：威贸电子 2025 年营收 **2.88 亿元**，口径为“2025 年实现营业收入/营收”，引用：[资料1] - 对象B：欣旺达 2025 年营收 **根据现有资料无法确定**。资料2仅给出的是 2025A/2026E/2027E/2028E 的“营业总收入”预测表项，但命中片段未直接清晰给出 2025 年实际营收数值；现有摘录中可确认的只是预测口径信息，不能替代 2025 年实际营收引用。[资料2] 结论：根据现有资料，...
  reference_coverage: 2/2
  missing_numbers: ['632']
  judge: None
  sources: ['data/raw/new_energy/WMDZ.pdf', 'data/raw/new_energy/XWD.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/consumer/WLY.pdf']
- `compare_016` compare reasons=number_miss
  query: 上海临港 vs 苏州高新，哪家公司2025年实现营收更高
  expected: 上海临港。上海临港公司 2025 年实现总营业收入 79.4 亿元，苏州高新2025 年实现营业收入 54.69亿元
  answer: - 对象A：上海临港，2025年实现**总营业收入79.4亿元**，口径为“总营业收入”，引用：[资料2] - 对象B：苏州高新，2025年实现**营业总收入5,469**，口径为“营业总收入”，引用：[资料1] 结论：**上海临港2025年实现营收更高**。 补充说明：两家公司资料中的营收口径分别为“总营业收入”和“营业总收入”，但均为2025年营收指标；按列示数字比较，上海临港高于苏州高新。[资料2][资料1]
  reference_coverage: 2/2
  missing_numbers: ['54.69']
  judge: None
  sources: ['data/raw/real_estate/SZGX.pdf', 'data/raw/real_estate/SHLG.pdf', 'data/raw/healthcare/TGYY.pdf']
- `compare_017` compare reasons=number_miss
  query: 我爱我家 vs 新城控股，哪家公司2025年实现营收更高
  expected: 新城控股。我爱我家2025年实现营业收入 105 亿元，新城控股2025年实现营业收入53012百万元。
  answer: - 对象A：我爱我家 2025年实现营业收入105亿元，口径为“营业收入”，时间为2025年 [资料1] - 对象B：新城控股 2025A 营业收入12,536百万元，口径为“营业收入(百万元)”，时间为2025A [资料3] 结论：按资料中的同口径“营业收入”比较，**我爱我家2025年实现营收更高**。 说明：我爱我家的105亿元对应的量级高于新城控股的12,536百万元；两者均为2025年营业收入口径 [资料1][资料3]
  reference_coverage: 2/2
  missing_numbers: ['53012']
  judge: None
  sources: ['data/raw/real_estate/WAWJ.pdf', 'data/raw/real_estate/XCKG.pdf']
- `compare_019` compare reasons=number_miss
  query: 珠江股份 vs 中新集团，哪家公司2024年实现营收更高
  expected: 中新集团。珠江股份2024年实现营业收入1558百万元，中新集团2024年实现营业收入2685百万元。
  answer: - 对象A（珠江股份）：2024A 营业收入 **1,558 百万元**，即 **15.58 亿元**；口径为“营业收入（百万元）/2024A” [资料2] - 对象B（中新集团）：公司 **2024 年实现营收的直接数值在现有资料中未列出**；资料中只给出了 **2025 年营收 32.14 亿元**，并未提供 2024 年营收原始数字 [资料1] 结论：**根据现有资料无法确定珠江股份 vs 中新集团哪家公司2024年实现营收更高*...
  reference_coverage: 2/2
  missing_numbers: ['2685']
  judge: None
  sources: ['data/raw/real_estate/ZXJT.pdf', 'data/raw/real_estate/ZJGF.pdf', 'data/raw/healthcare/BTGF.pdf', 'data/raw/new_energy/SGHN.pdf', 'data/raw/healthcare/SYXY.pdf']
- `compare_021` compare reasons=number_miss
  query: 华源控股 vs 海光信息，哪家公司2026年Q1实现营收更高
  expected: 海光信息。华源控股2026Q1 公司实现营收 5.85 亿元，海光信息2026 年一季度公司实现收入 40.34 亿元
  answer: - 对象A：华源控股 2026年Q1营收根据现有资料**无法确定**。资料中仅看到其**2025年**营业收入为**23.11亿元**，以及**2026年全年/预测**收入为**27.21亿元**等信息，未提供“2026年Q1”营收数据。引用：[资料2]、[资料4] - 对象B：海光信息 2026年Q1实现收入**40.34亿元**，口径为**2026年一季度公司实现收入**。引用：[资料1] 结论：根据现有资料，**无法直接比较两家公...
  reference_coverage: 2/2
  missing_numbers: ['5.85']
  judge: None
  sources: ['data/raw/semiconductor/HGXX.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `compare_024` compare reasons=number_miss
  query: 拓荆科技 vs 中科曙光，哪家公司2026年Q1实现营收更高
  expected: 中科曙光。拓荆科技2026年Q1实现营收11.12 亿元，中科曙光2026年Q1实现营收30.72 亿元
  answer: - 对象A（拓荆科技）：2026年Q1实现营收 **51.42亿元**，口径为“2026Q1营收”，引用见[资料3]：**“26Q1，公司实现营收51.42亿元，同比增加75.27%”**。 - 对象B（中科曙光）：2026年Q1实现营收 **30.72亿元**，口径为“2026Q1公司营业收入”，引用见[资料1]：**“2026Q1 公司营业收入30.72 亿元，同比+18.80%”**。 结论：在**2026年Q1营收**这一同口径...
  reference_coverage: 2/2
  missing_numbers: ['11.12']
  judge: None
  sources: ['data/raw/semiconductor/ZKSG.pdf', 'data/raw/new_energy/宁德时代_202601.pdf', 'data/raw/semiconductor/TJKJ.pdf']
- `compare_027` compare reasons=number_miss
  query: 爱尔眼科 vs 百诚医药，哪家公司2025年实现营收更高
  expected: 爱尔眼科。爱尔眼科2025 年公司实现营业收入 223.53 亿元，百诚医药2025 年实现收入 6.78亿元
  answer: - 对象A（爱尔眼科）：**2025 年实现营业收入 223.53 亿元**，口径为“营业收入”，引用：**“2025 年公司实现营业收入223.53 亿元”** [资料3] - 对象B（百诚医药）：**根据现有资料无法确定 2025 年实现营收的直接数值**。资料中仅看到 2025A/2026E 等预测/指标表述，以及“营业总收入”相关表格片段，但未明确给出“2025 年实现营业收入”的完整可核对数值；可见片段为“营业总收入 | 67...
  reference_coverage: 2/2
  missing_numbers: ['6.78']
  judge: None
  sources: ['data/raw/healthcare/BCYY.pdf', 'data/raw/healthcare/AEYK.pdf']
- `compare_028` compare reasons=number_miss
  query: 隆基绿能 vs 格林美，哪家公司2026年Q1实现营收更高
  expected: 隆基绿能。隆基绿能26Q1 营收 111.9 亿，格林美2026年Q1实现营收99.82 亿元
  answer: - 对象A：隆基绿能，2026年Q1实现**营业总收入 104,390 百万元**，口径为“营业总收入”，时间为2026E对应季度/期内披露口径；依据见[资料2]。 - 对象B：格林美，2026年Q1实现**营业收入 99.82 亿元**，口径为“营业收入”，时间为2026年第一季度；依据见[资料1]。 结论：**隆基绿能2026年Q1实现营收更高**。按资料中披露的同口径收入数据，隆基绿能的“营业总收入 104,390 百万元”高于格...
  reference_coverage: 2/2
  missing_numbers: ['111.9']
  judge: None
  sources: ['data/raw/new_energy/GLM.pdf', 'data/raw/new_energy/LJLN.pdf', 'data/raw/new_energy/宁德时代_202601.pdf']
- `compare_030` compare reasons=number_miss
  query: 鼎龙股份 vs 鼎智科技，哪家公司2025年实现营收更高
  expected: 鼎龙股份。鼎龙股份2025年营业总收入为36.60亿元，鼎智科技2025 年公司实现营收 2.68 亿元
  answer: - 对象A：鼎龙股份，**2025年营收 38.?? 亿元**？——根据现有资料，资料1仅明确给出其**2025年分业务营收**，如半导体板块业务营收**20.86亿元**、CMP抛光垫**10.91亿元**、CMP抛光液及清洗液**2.94亿元**、半导体显示材料**5.44亿元**、先进封装材料**1176万元**；但**未直接给出鼎龙股份2025年公司整体营收总额**。引用：[资料1] - 对象B：鼎智科技，**2025年营收 2...
  reference_coverage: 2/2
  missing_numbers: ['36.60']
  judge: None
  sources: ['data/raw/semiconductor/DLGF.pdf', 'data/raw/semiconductor/DZKJ.pdf']
- `summary_001` summary reasons=reference_not_hit_all,number_miss
  query: 结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  expected: 主要方向包括：坚持清洁低碳、安全充裕、经济高效、供需协同、灵活智能的基本原则，2024—2027年重点开展9项专项行动，提升电网对清洁能源的接纳、配置、调控能力；健全煤电、抽水蓄能、新型储能等调节性资源容量电价机制，完善体现分时价值差异的零售市场价格机制；突破新能源高效发电利用、系统灵活调节、电网高效仿真和稳定运行控制、智能化调控等技术；通过调节能力建设优化，支撑2025—2027年年均新增2亿千瓦以上新能源合理消纳利用，全国新能源利用率不低于90%；推动新型储能到2027年基本实现规模化、市场化发展，全国装机规模达到1.8亿千瓦以上。
  answer: 结合相关政策，新能源消纳与新型电力系统建设主要从以下方向推进： 1. 要点：坚持系统观念，统筹“电源与电网、可再生能源与传统化石能源、可再生能源开发与消纳”的关系，加快构建新型电力系统，提升可再生能源消纳和存储能力，实现能源绿色低碳转型与安全可靠供应相统一。[资料1] 2. 要点：以提高消纳和存储能力为重点，实施可再生能源替代行动，促进可再生能源大规模、高比例、市场化、高质量发展，并“以区域布局优化发展、以重大基地支撑发展、以示范工程引...
  reference_coverage: 2/4
  missing_numbers: ['2024', '2027', '9', '2025', '90%', '1.8']
  judge: None
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020210421528000000606.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf']
- `summary_002` summary reasons=reference_not_hit_all,number_miss
  query: 新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？
  expected: 新型储能被定位为支撑新型电力系统的重要技术和基础装备。目标上，到2025年实现从商业化初期向规模化发展转变、装机规模达3000万千瓦以上，到2030年实现全面市场化发展；专项行动进一步提出到2027年基本实现规模化、市场化发展。应用场景上，鼓励电源侧、电网侧、用户侧多元发展，拓展“新能源+储能”、智能微电网、虚拟电厂等场景。技术上，坚持多元化路线，推动锂离子电池规模化应用，推动压缩空气、液流电池、钠离子电池、飞轮、氢储能、热储能等试点示范和商业化发展。市场机制上，推动储能作为独立主体参与电力市场、辅助服务市场，完善容量电价、分时电价和成本疏导机制，并健全标准体系、并网流程和安全监管。
  answer: 1. 要点：以“碳达峰碳中和”为目标，推动新型储能由“商业化初期”步入“规模化发展”，到2025年“具备大规模商业化应用条件”；到2030年“实现新型储能全面市场化发展”，标准体系、市场机制、商业模式成熟健全，装机规模基本满足新型电力系统相应需求。[资料1][资料2] 2. 要点：应用场景上，重点围绕电源侧、电网侧、用户侧以及工业园区、算力设施、商业综合体、光储充放一体化充电站、分布式光伏、通信基站等多场景拓展，推进电源协同运行、电网稳...
  reference_coverage: 4/5
  missing_numbers: ['3000', '2027']
  judge: None
  sources: ['data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/202210114475091.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/P020210421528000346108.pdf', 'data/raw/policy/P020250106570227369979.pdf']
- `summary_003` summary reasons=reference_not_hit_all,number_miss
  query: “十四五”可再生能源规划和氢能规划分别怎样服务能源绿色低碳转型？
  expected: 可再生能源规划提出，加快发展可再生能源、实施可再生能源替代行动，是推进能源革命和构建清洁低碳、安全高效能源体系的重大举措；到2025年，可再生能源消费总量达到10亿吨标准煤左右，年发电量达到3.3万亿千瓦时左右，全国可再生能源电力总量消纳责任权重达到33%左右，非水电消纳责任权重达到18%左右。规划还要求推动绿色直供电、可再生能源供暖、非电直接利用和高比例可再生能源应用示范，健全消纳责任权重和长效机制。氢能规划将氢能界定为来源丰富、绿色低碳、应用广泛的二次能源，要求构建清洁化、低碳化、低成本的多元制氢体系，开展可再生能源制氢示范，构建安全、稳定、高效的氢能供应网络，并形成“1+N”政策体系。
  answer: 1. 要点：“十四五”可再生能源发展规划把“加快发展可再生能源、实施可再生能源替代行动”作为“推进能源革命和构建清洁低碳、安全高效能源体系”的重大举措，并明确在“十四五”时期“推动能源绿色低碳转型、落实应对气候变化国家自主贡献目标”；具体通过“大规模开发可再生能源”和“高比例利用可再生能源”，包括风电和光伏基地化开发、分布式开发、水风光综合基地一体化开发，以及提升存储能力、促进就地就近消纳和外送消纳来服务转型。[资料2][资料1] 2....
  reference_coverage: 2/3
  missing_numbers: ['2025', '10', '3.3', '33%', '18%']
  judge: None
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020220323314396580505.pdf', 'data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/P020210421528000346108.pdf']
- `summary_004` summary reasons=reference_not_hit_all,number_miss
  query: 电网建设、电力市场和容量电价政策如何支撑新能源消纳与系统可靠运行？
  expected: 配电网政策要求适度超前建设配电网，提升承载力，满足分布式新能源和电动汽车充电基础设施发展。全国统一电力市场提出到2030年基本建成全国统一电力市场体系，市场化交易电量占全社会用电量的70%左右，并推动跨省跨区和省内联合交易。容量机制方面，煤电、抽水蓄能、新型储能等支撑性、调节性资源在高比例新能源消纳和新型电力系统中发挥重要作用，政策通过可靠容量补偿、容量市场探索和发电侧容量电价机制，保障其收益、增强电力安全保供能力。新能源报价政策则要求规范集中报价、价格预警和数字化监管，防范市场力滥用，维护市场公平竞争。
  answer: 1. 要点：通过“坚持系统观念”统筹电源与电网、可再生能源与传统化石能源、可再生能源开发与消纳，加快构建新型电力系统，提升可再生能源消纳和存储能力，实现能源绿色低碳转型与安全可靠供应相统一。[资料1] 2. 要点：通过“坚持市场主导”，健全市场机制、破除市场壁垒、营造公平开放充分竞争的市场环境，落实“放管服”改革，提升可再生能源自我发展、自主发展能力；并提出到2030年“电力市场促进新能源消纳的机制更加健全，跨省跨区新能源交易更加顺畅”...
  reference_coverage: 1/5
  missing_numbers: ['70%']
  judge: None
  sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf', 'data/raw/policy/ndrc_generation_capacity_price_qna.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf']

## Metric Notes

- `answer_rate`：生成答案非空的比例。
- `citation_rate`：答案文本中显式出现 `[资料1]` 这类引用编号的比例。
- `reference_recall` / `reference_hit_all`：用生成文件保存的 `references` 对齐评测集 ground_truth 的 source/pages。
- `numeric_coverage`：标准答案中抽出的数字在生成答案中出现的比例，只在标准答案含数字的样本上统计。
- `LLM judge`：启用 `--llm-judge` 后，由模型比较问题、标准答案和生成答案，输出正确性、完整性和忠实度评分。
- 当前 judge 主要判断答案与 ground truth 的一致性；是否完全被原文支撑仍需结合引用覆盖和人工抽查。
