# 按问题类型路由检索实验

- 评测时间：2026-05-18T16:41:25
- 评测集：`data/eval/financial_qa_dev.jsonl`
- 索引目录：`data/processed/indexes/bge_large_zh_v15`
- 索引类型：`flat`
- 匹配粒度：`page`
- 完成样本：120 / 120
- 跳过样本：0
- 总耗时（秒）：102.52
- 融合方式：`weighted`，vector=0.6, bm25=0.4
- 父文档窗口：前后各 1 页
- fact 策略：hybrid_top5 + parent_window
- compare 策略：hybrid_top20 + rerank_top5 + parent_window
- summary 策略：hybrid_top50 + source_diverse_top8 + parent_window

## Overall

| scheme | Recall@5 | Recall@8 | HitAny@5 | HitAny@8 | HitAll@5 | HitAll@8 |
|---|---:|---:|---:|---:|---:|---:|
| routed | 92.82% | 94.26% | 97.50% | 97.50% | 87.50% | 90.83% |

## 结果分析

这次实验验证了“按问题类型路由”的路线是有效的。和上一轮整体最佳的
`hybrid_top20_rerank_top5_parent_window1` 相比，`routed` 在 `Recall@5`
从 87.92% 提升到 92.82%，`HitAll@5` 从 81.67% 提升到 87.50%。提升来自三类问题不再共用同一套策略：

- fact：使用 `hybrid_top5 + parent_window1`，保持了事实型题目的强表现，`HitAll@5=97.14%`。
- compare：使用 `hybrid_top20 + rerank_top5 + parent_window1`，`HitAll@5=86.67%`，比单一路线更适合多对象对比。
- summary：使用 `hybrid_top50 + source_diverse_top8 + parent_window1`，`HitAll@5=55.00%`，`HitAll@8=75.00%`，说明汇总型题目确实需要保留更多来源文档。

按题型拆开看：

| question_type | Recall@5 | HitAll@5 | Recall@8 | HitAll@8 |
|---|---:|---:|---:|---:|
| fact | 97.14% | 97.14% | 97.14% | 97.14% |
| compare | 91.67% | 86.67% | 91.67% | 86.67% |
| summary | 79.42% | 55.00% | 88.08% | 75.00% |

因此，当前检索阶段的默认推荐策略应改为 `routed`。后续进入生成阶段时，fact 和 compare 可以直接使用路由结果；summary 还需要继续控制多文档覆盖与上下文长度。

## By Question Type

### routed @ 8

| question_type | count | Recall | HitAny | HitAll |
|---|---:|---:|---:|---:|
| compare | 30 | 91.67% | 96.67% | 86.67% |
| fact | 70 | 97.14% | 97.14% | 97.14% |
| summary | 20 | 88.08% | 100.00% | 75.00% |

## Notes

- 本实验的 `routed` 结果会按问题类型使用不同策略，因此 summary 的候选数量可能大于 5。
- `Recall@5` 便于和前序实验横向对比，`Recall@8` 用于观察 summary 多文档聚合是否带来额外覆盖。
- 本实验仍使用 page-level 评测口径，命中文档但页码不对仍算未完全命中。
- summary 的 `HitAll@8` 明显高于 `HitAll@5`，后续回答生成时应允许 summary 使用更多证据块，并在 prompt 侧要求按政策来源归纳。

## Badcase 分析

主要 badcase 分为三类：

1. 事实型漏召回：`fact_047`、`fact_049` 没有命中目标页，说明部分公司名称或财务指标仍容易被相近行业文档干扰。
2. 对比型单边命中：`compare_002`、`compare_003`、`compare_007` 等只命中两家公司中的一家公司，需要考虑对 query 中的公司名做显式实体拆分。
3. 汇总型覆盖不足：`summary_004`、`summary_020` 等问题需要 3-5 个政策来源，虽然 `source_diverse_top8` 有改善，但还没有稳定覆盖全部证据。

下一步优先级：先把 `routed` 作为默认检索入口接入生成 baseline；同时为 compare 增加实体感知召回，为 summary 增加主题或来源约束召回。

## Badcases

### routed @ 8

- `fact_047` fact coverage=0/1
  query: 2025 年，海达尔公司研发费用为多少
  top_sources: ['data/raw/new_energy/LXDQ.pdf', 'data/raw/semiconductor/DLGF.pdf', 'data/raw/healthcare/KLY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/healthcare/SYXY.pdf']
- `fact_049` fact coverage=0/1
  query: 海光信息公司2024A销售毛利率为多少
  top_sources: ['data/raw/healthcare/SYXY.pdf', 'data/raw/healthcare/YMKD.pdf', 'data/raw/new_energy/LXDQ.pdf', 'data/raw/new_energy/SGHN.pdf']
- `compare_002` compare coverage=1/2
  query: 泸州老窖 vs 五粮液，哪家公司的2025年营业总收入更高？
  top_sources: ['data/raw/consumer/SXFJ.pdf', 'data/raw/consumer/LZLJ.pdf']
- `compare_003` compare coverage=1/2
  query: 千禾味业 vs 神农集团，哪家公司的26Q1营收 更高
  top_sources: ['data/raw/consumer/QHWY.pdf', 'data/raw/consumer/HTWY.pdf']
- `compare_007` compare coverage=1/2
  query: 普蕊斯 vs 普瑞眼科，预计哪家公司在2026年的营收更高
  top_sources: ['data/raw/healthcare/PRYK.pdf', 'data/raw/healthcare/HXYK.pdf', 'data/raw/healthcare/AEYK.pdf']
- `compare_008` compare coverage=0/2
  query: 昭衍新药 vs 通策医疗，预计哪家公司在2026年的营收更高
  top_sources: ['data/raw/healthcare/YKSW.pdf', 'data/raw/healthcare/SYXY.pdf']
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
