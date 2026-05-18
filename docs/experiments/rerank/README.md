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
| `05_hybrid_rerank_parent_window1_after/` | rerank 后展开邻页父文档 | 当前最强整体策略，`HitAll@5=81.67%`。 |

## 当前推荐

- 事实型：优先使用 `hybrid_top5 + parent_window1`。
- 对比型：优先使用 `hybrid_top20 + rerank_top5 + parent_window1`。
- 汇总型：需要额外设计跨文档聚合策略。
