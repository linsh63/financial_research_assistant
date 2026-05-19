# 阶段性实验总览

本文档汇总当前项目已经完成的主要实验，帮助快速判断系统目前处在什么阶段、哪些策略有效、下一步应该做什么。

## 当前结论

当前正式路线分为检索和生成两部分：

```text
检索：17_routed_compare_raw_entity_slots
生成：默认 prompt 约束 + DeepSeek deepseek-chat
```

其中，当前最强的页码级检索策略是按问题类型路由：

```text
fact    -> 混合召回 Top5 -> 展开前后各 1 页父文档
compare -> 混合召回 Top20 -> query rewrite -> raw coarse-to-fine entity slots -> rerank -> parent fill -> 展开前后各 1 页父文档
summary -> 混合召回 Top50 -> 按来源多样性保留 Top8 -> 展开前后各 1 页父文档
```

它在 120 条评测集上的结果为：

| scheme | Recall@5 | Recall@8 | HitAny@5 | HitAny@8 | HitAll@5 | HitAll@8 |
|---|---:|---:|---:|---:|---:|---:|
| routed_v17 | 94.90% | 96.35% | 98.33% | 98.33% | 90.83% | 94.17% |

按问题类型看，路由策略的结果为：

| question_type | 当前推荐策略 | Recall@8 | HitAll@8 | 说明 |
|---|---|---:|---:|---|
| fact | `hybrid_top5 + parent_window1` | 97.14% | 97.14% | 事实型直接混合召回已经足够强。 |
| compare | `query rewrite + raw coarse-to-fine entity slots + rerank + parent_fill` | 100.00% | 100.00% | 对比型检索侧已经基本跑通。 |
| summary | `hybrid_top50 + source_diverse_top8 + parent_window1` | 88.08% | 75.00% | 汇总型需要更多来源文档，仍是后续重点。 |

生成阶段当前正式结果为：

| metric | value |
|---|---:|
| answer_rate | 100.00% |
| citation_rate | 97.50% |
| reference_hit_all | 93.33% |
| numeric_coverage | 86.31% |
| judge_correct_rate | 80.00% |
| judge_avg_score | 86.62 |

按问题类型看：

| question_type | judge_correct_rate | judge_avg_score | reference_hit_all |
|---|---:|---:|---:|
| fact | 82.86% | 86.07 | 97.14% |
| compare | 93.33% | 96.17 | 100.00% |
| summary | 50.00% | 74.25 | 70.00% |

结论：第三周主线已经跑通，可以进入第四周。下一阶段重点是固定正式配置、做最终评测闭环、Demo 和最终文档。

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
| hybrid_top20_rerank_top5_parent_window1 | 87.92% | 94.17% | 81.67% | 单一策略中的整体最佳，尤其适合对比题。 |
| routed | 92.82% | 97.50% | 87.50% | 早期路由策略，按问题类型分别选择策略。 |
| routed + compare LLM rewrite | 93.24% | 98.33% | 87.50% | 子查询独立召回提升 compare Recall，但 HitAll 未超过 routed。 |
| routed + compare entity prefer | 93.24% | 98.33% | 87.50% | 修复 `compare_024`，但 `compare_010` 回退，整体与 LLM rewrite 持平。 |
| routed_v17_compare_raw_entity_slots | 94.90% | 98.33% | 90.83% | 当前最佳检索版本，compare 检索侧达到 100% HitAll@8。 |

按问题类型看当前最佳观察：

| question_type | 最优观察 | 指标 |
|---|---|---|
| fact | routed 中的 `hybrid_top5_parent_window1` | HitAll@5 97.14% |
| compare | `query rewrite + raw coarse-to-fine entity slots + rerank + parent_fill` | HitAll@8 100.00% |
| summary | routed 中的 `hybrid_top50_source_diverse_top8_parent_window1` | HitAll@5 55.00%，HitAll@8 75.00% |
| all | `routed_v17_compare_raw_entity_slots` | HitAll@5 90.83%，HitAll@8 94.17% |

相关文档：

- `docs/experiments/rerank/01_vector_top20_rerank_top5/report.md`
- `docs/experiments/rerank/02_hybrid_top20_rerank_top5/report.md`
- `docs/experiments/rerank/03_hybrid_parent_page_threshold/report.md`
- `docs/experiments/rerank/04_hybrid_rerank_parent_page_after/report.md`
- `docs/experiments/rerank/05_hybrid_rerank_parent_window1_after/report.md`
- `docs/experiments/rerank/06_routed_retrieval/report.md`
- `docs/experiments/rerank/08_compare_llm_query_rewrite/report.md`
- `docs/experiments/rerank/17_routed_compare_raw_entity_slots/report.md`
- `docs/experiments/rerank/badcase_analysis.md`

## 当前问题

1. 检索侧 compare 已经基本跑通，剩余 compare 问题主要在生成端读取表格字段。
2. fact 仍有两条真实漏召回和若干“证据已命中但模型拒答/取错数字”的生成问题。
3. summary 的 `HitAll@8` 仍然偏低，生成 correct rate 只有 50.00%，是第四周主要优化对象。
4. `parent_window1` 会显著增加上下文长度，生成阶段需要继续控制 token 和证据组织方式。

## 下一步行动

1. 固定正式路线：`routed_v17` 检索 + 默认生成 prompt。
2. 进入第四周评测闭环：
   - 跑最终全量生成。
   - 跑规则评测和 LLM judge。
   - 产出最终指标表。
3. 小步修生成端：
   - fact：减少证据已命中时的错误拒答。
   - compare：增强双方表格字段抽取，不再改检索主流程。
   - summary：继续做多文档覆盖和风格约束，但先不接入 `summary_evidence_pack`。
4. 补 Demo 和最终文档：
   - 展示问题、召回证据、答案、引用文档和页码。
   - 汇总系统架构图和实验对比表。
