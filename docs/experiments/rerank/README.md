# Rerank 实验索引

本目录按实验顺序归档第三周的 reranker、阈值过滤和父子文档召回实验。每个子目录包含：

- `report.md`：中文实验记录和结论。
- `details.json`：逐样本评测详情。

## 实验目录

| 目录 | 实验内容 | 关键结论 |
|---|---|---|
| `01_vector_top20_rerank_top5/` | 向量召回 Top20 + rerank Top5 | 纯向量 rerank 是稳定 baseline，`HitAll@5=74.17%`。 |
| `02_hybrid_top20_rerank_top5/` | 混合召回 Top20 + rerank Top5 | 对比题提升，但事实题退化，整体未超过向量 rerank。 |
| `03_hybrid_parent_page_threshold/` | 混合召回 + 页级父文档 + QAnything 阈值 | 页级父文档有用，但默认阈值过于激进。 |
| `04_hybrid_rerank_parent_page_after/` | rerank 后展开页级父文档 | 适合补全同页上下文，但不改变页码级指标。 |
| `05_hybrid_rerank_parent_window1_after/` | rerank 后展开邻页父文档 | 单一策略中最强，`HitAll@5=81.67%`。 |
| `06_routed_retrieval/` | 按问题类型路由检索 | 当前整体最佳，`Recall@5=92.82%`，`HitAll@5=87.50%`。 |
| `07_compare_entity_recall/` | compare 规则实体补召回 | 提升 HitAny，但 HitAll 下降，不能作为默认策略。 |
| `08_compare_llm_query_rewrite/` | LLM 改写 compare 子查询并独立召回 | 修复部分单边召回，`Compare Recall@8=93.33%`，但 HitAll 仍与 06 打平。 |
| `09_compare_llm_entity_prefer/` | compare 子查询召回后实体优先保留 | 修复 `compare_024`，但引入 `compare_010` 回退，整体指标与 08 持平。 |

## 当前推荐

- 默认检索入口：优先使用 `06_routed_retrieval` 的路由策略。
- 事实型：`hybrid_top5 + parent_window1`。
- 对比型：`hybrid_top20 + rerank_top5 + parent_window1`。
- 汇总型：`hybrid_top50 + source_diverse_top8 + parent_window1`，后续仍需优化多文档覆盖和上下文长度。

## Compare 专项实验观察

`08` 和 `09` 说明 LLM query rewrite 的方向是有效的，但当前还没有形成稳定默认策略：

- `08` 通过“每个子查询独立召回”修复了 `compare_002` 和 `compare_010`，但 `compare_024` 回退。
- `09` 通过“实体优先”修复了 `compare_024`，但 `compare_010` 回退。
- 下一步应把实体优先改为轻量 boost，而不是直接整体提前实体命中的候选。
- `compare_003`、`compare_008` 暴露的是 PDF 解析/表格/公司 alias 问题，不能只靠查询改写解决。
