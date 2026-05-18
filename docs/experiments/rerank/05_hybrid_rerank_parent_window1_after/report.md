# 调优实验：Rerank 后展开邻页父文档

- 评测时间：2026-05-18T13:20:51
- 评测集：`data/eval/financial_qa_dev.jsonl`
- 索引目录：`data/processed/indexes/bge_large_zh_v15`
- 候选来源：混合召回（向量 + BM25）
- 融合方式：加权融合，vector=0.6，bm25=0.4
- 匹配粒度：页码级
- 完成样本：120 / 120
- 总耗时（秒）：356.34
- 重排模型：`models/bge-reranker-v2-m3`
- 候选召回数量：20
- 重排后保留数量：5
- 阈值过滤：未启用
- 父文档模式：`window`
- 邻页窗口：前后各 1 页
- 父文档展开阶段：`after-rerank`
- 逐样本详情：`docs/experiments/rerank/05_hybrid_rerank_parent_window1_after/details.json`

## 实验目的

上一组 `page after-rerank` 只能补全同页上下文，对页码级指标没有帮助。本实验进一步采用邻页父文档：先对子 chunk 做混合召回 + rerank，然后把最终命中的页扩展为前后各 1 页的窗口。

这个策略对应真实问答里的一个常见需求：研报和政策文件中，标题、表格、解释文字、结论经常跨相邻页分布。只召回命中页可能不够，带上邻页更接近最终会喂给 LLM 的上下文。

## 总体结果

| scheme | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|
| hybrid_top5 | 88.21% | 96.67% | 80.00% |
| hybrid_top20_rerank_top5 | 87.92% | 94.17% | 81.67% |

这是目前所有 rerank 实验里最强的一组。`hybrid_top20_rerank_top5` 的 `HitAll@5` 达到 81.67%，比此前最佳 `vector_top20_rerank_top5` 的 74.17% 高 7.50 个百分点。

需要注意，`window` 展开会扩大最终上下文范围，所以指标提升的一部分来自“相邻页补证据”。这不是作弊，因为最终 RAG 确实会把这些邻页作为上下文提供给模型；但后续进入生成阶段时必须控制上下文长度，避免窗口太大带来噪声。

## 按问题类型统计

### 混合召回直接前 5 + 邻页父文档

| question_type | count | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|---:|
| compare | 30 | 78.33% | 96.67% | 60.00% |
| fact | 70 | 97.14% | 97.14% | 97.14% |
| summary | 20 | 71.75% | 95.00% | 50.00% |

### 混合召回前 20 + Rerank 前 5 + 邻页父文档

| question_type | count | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|---:|
| compare | 30 | 90.00% | 96.67% | 83.33% |
| fact | 70 | 91.43% | 91.43% | 91.43% |
| summary | 20 | 72.50% | 100.00% | 45.00% |

对比型问题收益最明显：`HitAll@5` 从直接混合召回的 60.00% 提升到 83.33%。这说明“Top20 粗召回 + rerank + 邻页展开”很适合多对象比较类问题。

事实型问题则相反：直接混合召回 + 邻页展开已经达到 97.14%，再 rerank 后降到 91.43%。这说明事实型问题不一定需要 rerank，尤其当邻页窗口已经能补足证据时，rerank 可能把原本正确的高排候选换掉。

汇总型问题仍然是短板。邻页展开让 `HitAny@5` 达到 100.00%，但 `HitAll@5` 只有 45.00%。这类问题往往需要跨多个政策文件或多个非相邻页，单纯前后 1 页窗口还不够。

## 与前序实验对照

| scheme | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|
| vector_top5 | 78.25% | 88.33% | 69.17% |
| vector_top20_rerank_top5 | 82.29% | 90.00% | 74.17% |
| hybrid_top5 | 81.54% | 91.67% | 71.67% |
| hybrid_top20_rerank_top5 | 80.64% | 89.17% | 72.50% |
| hybrid_top5_parent_page | 82.65% | 91.67% | 74.17% |
| hybrid_top20_parent_page_threshold_rerank_top5 | 81.12% | 91.67% | 71.67% |
| hybrid_top5_parent_window1 | 88.21% | 96.67% | 80.00% |
| hybrid_top20_rerank_top5_parent_window1 | 87.92% | 94.17% | 81.67% |

当前最佳整体方案是 `hybrid_top20_rerank_top5_parent_window1`，尤其适合对比型问题。当前最佳事实型方案反而是 `hybrid_top5_parent_window1`。

## 变化样本

- 完整命中修复数：8
- 完整命中退化数：6

### 重排后修复的样本

- `fact_049`
- `compare_006`
- `compare_010`
- `compare_012`
- `compare_016`
- `compare_021`
- `compare_025`
- `compare_029`

### 重排后退化的样本

- `fact_004`
- `fact_005`
- `fact_008`
- `fact_035`
- `fact_036`
- `summary_014`

修复样本主要集中在对比型，退化样本主要集中在事实型。这进一步支持“按问题类型路由”的方向。

## 仍然存在的问题

`window` 展开会让多个 child chunk 合并到同一个 parent window，因此最终唯一 parent 数量可能少于 5。当前统计如下：

| scheme | avg_results | samples_with_less_than_5 |
|---|---:|---:|
| hybrid_top5_parent_window1 | 3.82 | 78 |
| hybrid_top20_rerank_top5_parent_window1 | 4.02 | 66 |

虽然指标提升明显，但这个现象提醒我们：后续如果进入回答生成，需要把“结果条数”理解为上下文窗口数，而不是原始 child chunk 数。一个窗口包含多页内容，信息密度更高，但也更长。

## 结论

本轮调优解决了上一轮发现的问题：

- 不再把长 parent 文档送进 reranker，避免 `max_length=512` 截断影响排序。
- 不再使用 QAnything 默认阈值，避免多证据任务被过度过滤。
- 在 rerank 后使用 `window=1` 父文档展开，显著提高页码级完整证据命中。

建议把当前第三周的候选最佳策略定为：

- 事实型：`hybrid_top5 + parent_window1`
- 对比型：`hybrid_top20 + rerank_top5 + parent_window1`
- 汇总型：仍需单独设计跨文档聚合策略，不能只依赖 top5 rerank。

下一步应实现“按问题类型路由”，并为汇总型问题尝试更高 top_k 或按 source 去重后的多文档覆盖策略。
