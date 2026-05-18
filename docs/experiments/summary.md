# 阶段性实验总览

本文档汇总当前项目已经完成的主要实验，帮助快速判断系统目前处在什么阶段、哪些策略有效、下一步应该做什么。

## 当前结论

目前最强的页码级检索策略是：

```text
混合召回 Top20 -> rerank Top5 -> 展开前后各 1 页父文档
```

它在 120 条评测集上的结果为：

| scheme | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|
| hybrid_top20_rerank_top5_parent_window1 | 87.92% | 94.17% | 81.67% |

但这个策略不是所有问题类型都最优。当前更合理的方向是按问题类型路由：

| question_type | 当前推荐策略 | 原因 |
|---|---|---|
| fact | `hybrid_top5 + parent_window1` | 事实型直接召回已经很强，rerank 可能误排。 |
| compare | `hybrid_top20 + rerank_top5 + parent_window1` | 对比型需要多对象证据，rerank 和邻页展开收益明显。 |
| summary | 待单独设计跨文档聚合 | Top5 rerank 仍不足以覆盖多个政策文件和多页证据。 |

## 数据与评测集

| 项目 | 当前状态 |
|---|---|
| PDF 文档 | 150 份 |
| 解析页面 | 1092 页 |
| 解析表格 | 1014 个 |
| 评测集 | 120 条 |
| 评测类型 | fact 70，compare 30，summary 20 |
| 主要评测口径 | page-level，文档和页码都命中才算证据命中 |

相关文档：

- `docs/experiments/eval_set/eval_set_construction_from_pdfs.md`
- `docs/experiments/chunking/chunking_experiment.md`

## 切块实验

| chunk_size | overlap | chunk 数 | 表格 chunk | Recall@5 | HitAll@5 | 结论 |
|---:|---:|---:|---:|---:|---:|---|
| 256 | 50 | 10468 | 5131 | 77.53% | 67.50% | chunk 太碎，索引规模变大但召回未提升。 |
| 512 | 100 | 6826 | 2724 | 78.25% | 69.17% | 当前默认配置。 |
| 1024 | 200 | 5125 | 1594 | 76.92% | 67.50% | chunk 更长但召回下降。 |

结论：继续使用 `512/100` 作为默认切块参数。表格行保护策略有效，三组实验的表格保护缺失均为 0。

相关文档：`docs/experiments/chunking/chunking_experiment.md`

## 向量索引实验

完整索引使用：

- chunk 文件：`data/processed/chunks/chunks_boundary.jsonl`
- chunk 数：6826
- embedding 模型：`models/bge-large-zh-v1.5`
- 向量维度：1024
- 索引目录：`data/processed/indexes/bge_large_zh_v15`

FAISS 对比结果：

| index_type | Recall@10 | HitAll@10 | avg_latency_ms | file_size_mb | 结论 |
|---|---:|---:|---:|---:|---|
| Flat | 84.03% | 75.83% | 0.3896 | 26.6641 | 当前默认索引。 |
| IVF | 76.94% | 67.50% | 0.0735 | 26.9668 | 更快但召回下降明显。 |
| HNSW | 71.53% | 61.67% | 0.0572 | 28.4328 | 当前参数下不适合默认使用。 |

结论：当前数据规模只有 6826 个 chunk，Flat 延迟已经足够低，继续作为 baseline 和正式实验默认索引。

相关文档：`docs/experiments/vector_index/vector_index_baseline.md`

## 基础召回实验

第一版 baseline：

| scheme | Recall@5 | HitAll@5 | Recall@10 | HitAll@10 |
|---|---:|---:|---:|---:|
| vector | 78.25% | 69.17% | 84.03% | 75.83% |
| bm25 | 70.49% | 58.33% | 80.51% | 70.00% |
| hybrid 0.5/0.5 | 81.47% | 70.83% | 84.07% | 75.83% |

混合召回调参后：

| scheme | Recall@5 | HitAll@5 | Recall@10 | HitAll@10 |
|---|---:|---:|---:|---:|
| hybrid 0.6/0.4 | 81.54% | 71.67% | 85.36% | 77.50% |

结论：混合召回优于单一路召回，当前默认权重为 `vector=0.6, bm25=0.4`。

相关文档：

- `docs/experiments/retrieval/retrieval_eval_baseline.md`
- `docs/experiments/retrieval/retrieval_eval_hybrid_tuned.md`

## Rerank 与父子文档实验

| 实验 | Recall@5 | HitAny@5 | HitAll@5 | 结论 |
|---|---:|---:|---:|---|
| vector_top5 | 78.25% | 88.33% | 69.17% | 纯向量直接召回 baseline。 |
| vector_top20_rerank_top5 | 82.29% | 90.00% | 74.17% | rerank 对纯向量召回有稳定收益。 |
| hybrid_top5 | 81.54% | 91.67% | 71.67% | 混合召回直接 Top5。 |
| hybrid_top20_rerank_top5 | 80.64% | 89.17% | 72.50% | 对比题提升，但整体未超过向量 rerank。 |
| hybrid_top5_parent_page | 82.65% | 91.67% | 74.17% | 页级父文档能提升页码证据覆盖。 |
| hybrid_top20_parent_page_threshold_rerank_top5 | 81.12% | 91.67% | 71.67% | QAnything 默认阈值过激进。 |
| hybrid_top5_parent_window1 | 88.21% | 96.67% | 80.00% | 事实型表现最好。 |
| hybrid_top20_rerank_top5_parent_window1 | 87.92% | 94.17% | 81.67% | 当前整体最佳，尤其适合对比题。 |

按问题类型看当前最佳观察：

| question_type | 最优观察 | 指标 |
|---|---|---|
| fact | `hybrid_top5_parent_window1` | HitAll@5 97.14% |
| compare | `hybrid_top20_rerank_top5_parent_window1` | HitAll@5 83.33% |
| summary | `hybrid_top5_parent_window1` | HitAll@5 50.00%，仍然偏低 |

相关文档：

- `docs/experiments/rerank/01_vector_top20_rerank_top5/report.md`
- `docs/experiments/rerank/02_hybrid_top20_rerank_top5/report.md`
- `docs/experiments/rerank/03_hybrid_parent_page_threshold/report.md`
- `docs/experiments/rerank/04_hybrid_rerank_parent_page_after/report.md`
- `docs/experiments/rerank/05_hybrid_rerank_parent_window1_after/report.md`

## 当前问题

1. 事实型和对比型的最佳策略不同，不能再用单一策略硬套所有问题。
2. 汇总型问题仍然弱，Top5 rerank 很难覆盖多个政策文件和多个非相邻页。
3. `parent_window1` 会显著增加上下文长度，进入回答生成阶段时需要做 token 控制。
4. QAnything 默认阈值不能直接照搬，需要结合金融文档评测集重新调参。

## 下一步行动

1. 实现按问题类型路由：
   - fact：`hybrid_top5 + parent_window1`
   - compare：`hybrid_top20 + rerank_top5 + parent_window1`
   - summary：单独走跨文档聚合策略
2. 为 summary 构造多文档召回策略：
   - 提高候选数量
   - 按 source 去重
   - 保留多个政策文件
   - 再做窗口扩展
3. 进入生成阶段 baseline：
   - 拼接检索上下文
   - 调用 LLM 生成答案
   - 用评测集观察引用覆盖与回答质量
