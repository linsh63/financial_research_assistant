# 按问题类型路由检索实验

- 评测时间：2026-05-19T11:04:09
- 评测集：`data/eval/financial_qa_dev.jsonl`
- 索引目录：`data/processed/indexes/bge_large_zh_v15`
- 索引类型：`flat`
- 匹配粒度：`page`
- 完成样本：120 / 120
- 跳过样本：0
- 总耗时（秒）：162.38
- 融合方式：`weighted`，vector=0.6, bm25=0.4
- compare rewrite：`data/processed/query_rewrites/compare_financial_table_no_unit_rule.jsonl`
- 父文档窗口：前后各 1 页
- fact 策略：hybrid_top5 + parent_window
- compare 策略：hybrid_top20 + llm_rewrite_separate_subquery_top8 + per_query_keep2 + coarse_to_fine_doc_top2_adaptive3_page_top12_keep4 + raw_entity_slot4 + entity_prefer + rerank_top5 + parent_fill_pool12 + parent_window
- summary 策略：hybrid_top50 + source_diverse_top8 + parent_window

## Overall

| scheme | Recall@5 | Recall@8 | HitAny@5 | HitAny@8 | HitAll@5 | HitAll@8 |
|---|---:|---:|---:|---:|---:|---:|
| routed | 94.90% | 96.35% | 98.33% | 98.33% | 90.83% | 94.17% |

## By Question Type

### routed @ 8

| question_type | count | Recall | HitAny | HitAll |
|---|---:|---:|---:|---:|
| compare | 30 | 100.00% | 100.00% | 100.00% |
| fact | 70 | 97.14% | 97.14% | 97.14% |
| summary | 20 | 88.08% | 100.00% | 75.00% |

## Notes

- 本实验的 `routed` 结果会按问题类型使用不同策略，因此 summary 的候选数量可能大于 5。
- `Recall@5` 便于和前序实验横向对比，`Recall@8` 用于观察 summary 多文档聚合是否带来额外覆盖。

## Badcases

### routed @ 8

- `fact_047` fact coverage=0/1
  query: 2025 年，海达尔公司研发费用为多少
  top_sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/DLGF.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/healthcare/SYXY.pdf']
- `fact_049` fact coverage=0/1
  query: 海光信息公司2024A销售毛利率为多少
  top_sources: ['data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/new_energy/SGHN.pdf']
- `summary_001` summary coverage=3/4
  query: 结合相关政策，新能源消纳与新型电力系统建设主要从哪些方向推进？
  top_sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020210421528000000606.pdf', 'data/raw/policy/P020240806534738672970.pdf', 'data/raw/policy/P020250912338143145278.pdf']
- `summary_003` summary coverage=2/3
  query: “十四五”可再生能源规划和氢能规划分别怎样服务能源绿色低碳转型？
  top_sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020220323314396580505.pdf', 'data/raw/policy/P020220321550104020921.pdf', 'data/raw/policy/P020210421528000346108.pdf']
- `summary_004` summary coverage=1/5
  query: 电网建设、电力市场和容量电价政策如何支撑新能源消纳与系统可靠运行？
  top_sources: ['data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/ndrc_2025_new_energy_consumption_guidance_qna.pdf', 'data/raw/policy/ndrc_generation_capacity_price_qna.pdf', 'data/raw/policy/ndrc_2024_new_power_system_action_plan.pdf', 'data/raw/policy/P020240806534738672970.pdf']
- `summary_012` summary coverage=2/3
  query: 固体废物综合治理和绿色产业体系建设如何形成全链条治理？
  top_sources: ['data/raw/policy/ndrc_solid_waste_governance_interpretation.pdf', 'data/raw/policy/ndrc_2024_green_low_carbon_industry_catalog.pdf', 'data/raw/policy/ndrc_changzhutan_green_transition_interpretation.pdf', 'data/raw/policy/P020220602315650388122.pdf', 'data/raw/policy/P020220121303052384813.pdf']
- `summary_020` summary coverage=1/3
  query: 低空经济统计分类如何界定核心产业，相关教育和人工智能政策怎样支撑新兴产业发展？
  top_sources: ['data/raw/policy/ndrc_2025_low_altitude_economy_classification.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/policy/P020210325504120315428.pdf', 'data/raw/policy/P020240624569333510920.pdf', 'data/raw/policy/ndrc_2024_consumer_new_scenarios.pdf']
