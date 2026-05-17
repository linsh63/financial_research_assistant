# Retrieval Evaluation

- evaluated_at: 2026-05-17T17:43:07
- eval_file: `data/eval/financial_qa_dev.jsonl`
- index_dir: `data/processed/indexes/bge_large_zh_v15`
- index_type: `flat`
- match_level: `page`
- completed_samples: 120 / 120
- skipped_samples: 0
- elapsed_seconds: 8.91
- fusion: `weighted`
- weights: vector=0.6, bm25=0.4

## Overall

| scheme | Recall@3 | Recall@5 | Recall@10 | HitAll@3 | HitAll@5 | HitAll@10 |
|---|---:|---:|---:|---:|---:|---:|
| hybrid | 75.40% | 81.54% | 85.36% | 62.50% | 71.67% | 77.50% |

## By Question Type

### hybrid @ 10

| question_type | count | Recall | HitAny | HitAll |
|---|---:|---:|---:|---:|
| compare | 30 | 81.67% | 96.67% | 66.67% |
| fact | 70 | 90.00% | 90.00% | 90.00% |
| summary | 20 | 74.67% | 95.00% | 50.00% |

## Badcases

### hybrid @ 10

- `fact_004` fact coverage=0/1
  query: 国轩高科 2024A 的 PB 估值是多少倍
  top_sources: ['data/raw/new_energy/GXGK.pdf', 'data/raw/consumer/WLY.pdf', 'data/raw/new_energy/长安汽车_202601.pdf', 'data/raw/real_estate/XCKG.pdf', 'data/raw/new_energy/XWD.pdf']
- `fact_008` fact coverage=0/1
  query: 麦加芯彩 2026E 归母净利润预计是多少
  top_sources: ['data/raw/new_energy/MJXC.pdf', 'data/raw/semiconductor/HWJ.pdf', 'data/raw/consumer/DPYL.pdf', 'data/raw/consumer/LZLJ.pdf', 'data/raw/semiconductor/LCXX.pdf']
- `fact_013` fact coverage=0/1
  query: 安琪酵母2025A净利润为多少
  top_sources: ['data/raw/consumer/AQJM.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/semiconductor/BDT.pdf', 'data/raw/new_energy/广汽集团_202601.pdf', 'data/raw/healthcare/YMKD.pdf']
- `fact_036` fact coverage=0/1
  query: 截至 2025 年末，金地集团有息负债多少
  top_sources: ['data/raw/real_estate/JDJT.pdf', 'data/raw/real_estate/HFGF.pdf', 'data/raw/real_estate/ZGGM.pdf', 'data/raw/real_estate/BJJT.pdf']
- `fact_045` fact coverage=0/1
  query: 飞荣达公司2025主营收入为多少
  top_sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/FRD.pdf', 'data/raw/healthcare/YKSW.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/semiconductor/HGCY.pdf']
- `fact_047` fact coverage=0/1
  query: 2025 年，海达尔公司研发费用为多少
  top_sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/DLGF.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/real_estate/ZJGF.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `fact_050` fact coverage=0/1
  query: 寒武纪-U公司2023A营业收入为多少
  top_sources: ['data/raw/semiconductor/HWJ.pdf', 'data/raw/consumer/QHWY.pdf', 'data/raw/semiconductor/BDT.pdf', 'data/raw/real_estate/HFGF.pdf', 'data/raw/new_energy/LXDQ.pdf']
- `compare_003` compare coverage=1/2
  query: 千禾味业 vs 神农集团，哪家公司的26Q1营收 更高
  top_sources: ['data/raw/consumer/QHWY.pdf', 'data/raw/semiconductor/TJKJ.pdf', 'data/raw/consumer/HTWY.pdf']
- `compare_006` compare coverage=1/2
  query: 凯莱英 vs 美年健康，哪家公司2025年的归母净利润更高
  top_sources: ['data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/semiconductor/DLGF.pdf', 'data/raw/healthcare/AEYK.pdf', 'data/raw/healthcare/TGYY.pdf']
- `compare_007` compare coverage=1/2
  query: 普蕊斯 vs 普瑞眼科，预计哪家公司在2026年的营收更高
  top_sources: ['data/raw/healthcare/PRYK.pdf', 'data/raw/healthcare/AEYK.pdf', 'data/raw/healthcare/HXYK.pdf']
- `compare_008` compare coverage=0/2
  query: 昭衍新药 vs 通策医疗，预计哪家公司在2026年的营收更高
  top_sources: ['data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YKSW.pdf', 'data/raw/healthcare/GJYX.pdf', 'data/raw/healthcare/BDYY.pdf', 'data/raw/semiconductor/TJKJ.pdf']
- `compare_010` compare coverage=1/2
  query: 药康生物 vs 药明康德，哪家公司2025年的全年营业收入同比增长更多
  top_sources: ['data/raw/healthcare/YMKD.pdf', 'data/raw/healthcare/TGYY.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YKSW.pdf']
- `compare_012` compare coverage=1/2
  query: 亿纬锂能 vs 中国核电，哪家公司2025年的全年营业收入同比增长更多
  top_sources: ['data/raw/new_energy/ZGHD.pdf', 'data/raw/new_energy/XWD.pdf', 'data/raw/real_estate/HFGF.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `compare_013` compare coverage=1/2
  query: 中集集团 vs 中自科技，预计哪家公司2026年营业收入更高
  top_sources: ['data/raw/new_energy/ZZKJ.pdf', 'data/raw/new_energy/ZJJT.pdf', 'data/raw/semiconductor/ZWGS.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `compare_019` compare coverage=1/2
  query: 珠江股份 vs 中新集团，哪家公司2024年实现营收更高
  top_sources: ['data/raw/real_estate/ZJGF.pdf', 'data/raw/new_energy/SGHN.pdf', 'data/raw/real_estate/JDJT.pdf', 'data/raw/real_estate/ZXJT.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `compare_021` compare coverage=1/2
  query: 华源控股 vs 海光信息，哪家公司2026年Q1实现营收更高
  top_sources: ['data/raw/semiconductor/HGXX.pdf', 'data/raw/new_energy/SSGF.pdf', 'data/raw/semiconductor/DLGF.pdf', 'data/raw/new_energy/赛力斯_202601.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `compare_027` compare coverage=1/2
  query: 爱尔眼科 vs 百诚医药，哪家公司2025年实现营收更高
  top_sources: ['data/raw/healthcare/AEYK.pdf', 'data/raw/healthcare/HXYK.pdf', 'data/raw/semiconductor/DLGF.pdf']
- `summary_001` summary coverage=3/4
  query: 结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  top_sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020250106570227369979.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/P020210421528000000606.pdf']
- `summary_002` summary coverage=3/5
  query: 新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？
  top_sources: ['data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/202210114475091.pdf', 'data/raw/policy/P020210421528000000606.pdf']
- `summary_003` summary coverage=2/3
  query: “十四五”可再生能源规划和氢能规划分别怎样服务能源绿色低碳转型？
  top_sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020220323314396580505.pdf']
