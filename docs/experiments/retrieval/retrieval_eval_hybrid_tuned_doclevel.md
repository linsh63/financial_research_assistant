# Retrieval Evaluation

- evaluated_at: 2026-05-17T17:44:07
- eval_file: `data/eval/financial_qa_dev.jsonl`
- index_dir: `data/processed/indexes/bge_large_zh_v15`
- index_type: `flat`
- match_level: `doc`
- completed_samples: 120 / 120
- skipped_samples: 0
- elapsed_seconds: 9.04
- fusion: `weighted`
- weights: vector=0.6, bm25=0.4

## Overall

| scheme | Recall@3 | Recall@5 | Recall@10 | HitAll@3 | HitAll@5 | HitAll@10 |
|---|---:|---:|---:|---:|---:|---:|
| hybrid | 86.31% | 89.25% | 93.72% | 75.00% | 80.83% | 87.50% |

## By Question Type

### hybrid @ 10

| question_type | count | Recall | HitAny | HitAll |
|---|---:|---:|---:|---:|
| compare | 30 | 90.00% | 100.00% | 80.00% |
| fact | 70 | 98.57% | 98.57% | 98.57% |
| summary | 20 | 82.33% | 95.00% | 60.00% |

## Badcases

### hybrid @ 10

- `fact_047` fact coverage=0/1
  query: 2025 年，海达尔公司研发费用为多少
  top_sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/DLGF.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/real_estate/ZJGF.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `compare_003` compare coverage=1/2
  query: 千禾味业 vs 神农集团，哪家公司的26Q1营收 更高
  top_sources: ['data/raw/consumer/QHWY.pdf', 'data/raw/semiconductor/TJKJ.pdf', 'data/raw/consumer/HTWY.pdf']
- `compare_006` compare coverage=1/2
  query: 凯莱英 vs 美年健康，哪家公司2025年的归母净利润更高
  top_sources: ['data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/semiconductor/DLGF.pdf', 'data/raw/healthcare/AEYK.pdf', 'data/raw/healthcare/TGYY.pdf']
- `compare_007` compare coverage=1/2
  query: 普蕊斯 vs 普瑞眼科，预计哪家公司在2026年的营收更高
  top_sources: ['data/raw/healthcare/PRYK.pdf', 'data/raw/healthcare/AEYK.pdf', 'data/raw/healthcare/HXYK.pdf']
- `compare_008` compare coverage=1/2
  query: 昭衍新药 vs 通策医疗，预计哪家公司在2026年的营收更高
  top_sources: ['data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YKSW.pdf', 'data/raw/healthcare/GJYX.pdf', 'data/raw/healthcare/BDYY.pdf', 'data/raw/semiconductor/TJKJ.pdf']
- `compare_012` compare coverage=1/2
  query: 亿纬锂能 vs 中国核电，哪家公司2025年的全年营业收入同比增长更多
  top_sources: ['data/raw/new_energy/ZGHD.pdf', 'data/raw/new_energy/XWD.pdf', 'data/raw/real_estate/HFGF.pdf', 'data/raw/healthcare/SYXY.pdf', 'data/raw/semiconductor/HYKG.pdf']
- `compare_027` compare coverage=1/2
  query: 爱尔眼科 vs 百诚医药，哪家公司2025年实现营收更高
  top_sources: ['data/raw/healthcare/AEYK.pdf', 'data/raw/healthcare/HXYK.pdf', 'data/raw/semiconductor/DLGF.pdf']
- `summary_001` summary coverage=3/4
  query: 结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  top_sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020250106570227369979.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/P020210421528000000606.pdf']
- `summary_002` summary coverage=4/5
  query: 新型储能政策对发展目标、应用场景、技术路线和市场机制是如何安排的？
  top_sources: ['data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/P020250912338143145278.pdf', 'data/raw/policy/202210114475091.pdf', 'data/raw/policy/P020210421528000000606.pdf']
- `summary_003` summary coverage=2/3
  query: “十四五”可再生能源规划和氢能规划分别怎样服务能源绿色低碳转型？
  top_sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020220323314396580505.pdf']
