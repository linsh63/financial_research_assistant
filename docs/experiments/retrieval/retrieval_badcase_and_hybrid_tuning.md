# Retrieval Badcase And Hybrid Tuning

- 日期：2026-05-17
- 评测集：`data/eval/financial_qa_dev.jsonl`
- 样本数：120 条，全部参与评测
- 索引：`data/processed/indexes/bge_large_zh_v15`
- 向量模型：`models/bge-large-zh-v1.5`
- 向量索引：FAISS Flat
- 评测口径：默认使用 page-level，即召回 chunk 的文档和页码都要命中 ground truth

## 本次输出文件

- 完整三路 baseline：`docs/experiments/retrieval/retrieval_eval_baseline.md`
- baseline 逐样本详情：`docs/experiments/retrieval/details/retrieval_eval_baseline.details.json`
- 调参后 hybrid 结果：`docs/experiments/retrieval/retrieval_eval_hybrid_tuned.md`
- 调参后 hybrid 逐样本详情：`docs/experiments/retrieval/details/retrieval_eval_hybrid_tuned.details.json`
- 调参后 doc-level 对照：`docs/experiments/retrieval/retrieval_eval_hybrid_tuned_doclevel.md`
- 调参后 doc-level 逐样本详情：`docs/experiments/retrieval/details/retrieval_eval_hybrid_tuned_doclevel.details.json`

## Baseline 结果

baseline 使用 `weighted` 融合，`vector_weight=0.5`，`bm25_weight=0.5`。

| scheme | Recall@3 | Recall@5 | Recall@10 | HitAll@3 | HitAll@5 | HitAll@10 |
|---|---:|---:|---:|---:|---:|---:|
| vector | 73.15% | 78.25% | 84.03% | 60.83% | 69.17% | 75.83% |
| bm25 | 63.56% | 70.49% | 80.51% | 50.00% | 58.33% | 70.00% |
| hybrid | 75.50% | 81.47% | 84.07% | 62.50% | 70.83% | 75.83% |

结论：向量召回是主力，BM25 单独效果弱于向量，但可以补足一部分向量漏召。混合召回在 @3 和 @5 上相对更稳，但默认 0.5/0.5 在 @10 上提升很小。

## 混合参数 sweep

本轮只调融合参数，不改变 chunk、索引和评测集。

| config | Recall@3 | Recall@5 | Recall@10 | HitAll@3 | HitAll@5 | HitAll@10 |
|---|---:|---:|---:|---:|---:|---:|
| weighted_v0.5_b0.5_top20 | 75.50% | 81.47% | 84.07% | 62.50% | 70.83% | 75.83% |
| weighted_v0.6_b0.4_top20 | 75.40% | 81.54% | 85.36% | 62.50% | 71.67% | 77.50% |
| weighted_v0.7_b0.3_top20 | 74.06% | 81.44% | 85.32% | 61.67% | 72.50% | 77.50% |
| weighted_v0.4_b0.6_top20 | 73.14% | 78.58% | 85.00% | 60.00% | 68.33% | 75.83% |
| weighted_v0.3_b0.7_top20 | 69.85% | 75.94% | 83.12% | 55.83% | 65.00% | 73.33% |
| rrf_v0.5_b0.5_top20 | 72.90% | 79.11% | 85.97% | 60.00% | 68.33% | 77.50% |
| weighted_v0.5_b0.5_top50 | 75.01% | 80.67% | 84.17% | 63.33% | 70.00% | 75.00% |
| rrf_v0.5_b0.5_top50 | 73.07% | 78.03% | 83.85% | 60.00% | 67.50% | 76.67% |

当前推荐参数：

```bash
--fusion weighted --vector-weight 0.6 --bm25-weight 0.4 --vector-top-k 20 --bm25-top-k 20
```

选择理由：`0.6/0.4` 在 Recall@10 和 HitAll@10 上都高于 baseline，并且没有造成 @3、@5 的明显退化。RRF 的 Recall@10 最高，但 @3 和 @5 下降较多，暂时作为候选方案保留。

## 调参后结果

page-level：

| scheme | Recall@3 | Recall@5 | Recall@10 | HitAll@3 | HitAll@5 | HitAll@10 |
|---|---:|---:|---:|---:|---:|---:|
| hybrid | 75.40% | 81.54% | 85.36% | 62.50% | 71.67% | 77.50% |

doc-level 对照：

| scheme | Recall@3 | Recall@5 | Recall@10 | HitAll@3 | HitAll@5 | HitAll@10 |
|---|---:|---:|---:|---:|---:|---:|
| hybrid | 86.31% | 89.25% | 93.72% | 75.00% | 80.83% | 87.50% |

page-level 与 doc-level 的差距说明：当前很多样本已经召回了正确文档，但没有召回到标注页码对应的 chunk。也就是说，下一步不只是继续调 BM25/向量权重，还要处理页内定位、邻页扩展、父子文档召回和表格页召回。

## Badcase 结构

调参后 page-level @10 仍有 27 个未完全命中：

| 类型 | 数量 |
|---|---:|
| fact | 7 |
| compare | 10 |
| summary | 10 |

其中有 12 个属于“doc-level 已全命中，但 page-level 未全命中”，主要是页码或 chunk 定位问题：

- `fact_004`
- `fact_008`
- `fact_013`
- `fact_036`
- `fact_045`
- `fact_050`
- `compare_010`
- `compare_013`
- `compare_019`
- `compare_021`
- `summary_014`
- `summary_019`

还有 15 个属于真正的文档级漏召：

- `fact_047`
- `compare_003`
- `compare_006`
- `compare_007`
- `compare_008`
- `compare_012`
- `compare_027`
- `summary_001`
- `summary_002`
- `summary_003`
- `summary_004`
- `summary_005`
- `summary_006`
- `summary_012`
- `summary_020`

## 主要问题判断

1. 事实型题目主要卡在页内定位。很多问题的目标文档进入 top10，但具体页码没有命中，尤其是估值表、财务预测表、费用率和收入利润表这类内容。

2. 对比型题目经常只召回两家公司中的一家。当前 query 一次性输入“公司 A vs 公司 B”，融合排序容易被其中一个公司或一个指标主导，导致第二家公司漏召。

3. 汇总型题目天然需要多篇政策文件共同命中。page-level HitAll@10 对这类问题很严格，当前 summary 的 doc-level Recall@10 为 82.33%，说明主要问题是多文档覆盖不足，而不是单篇定位。

4. 单纯把 BM25 权重继续调高不是好方向。`0.4/0.6` 和 `0.3/0.7` 都降低了 @3/@5，说明 BM25 适合作为补充召回，不适合作为主导排序。

5. 内部候选从 top20 提到 top50 没有改善，说明当前瓶颈不只是候选池大小，而是融合策略和查询拆解策略。

## 下一步调优方向

优先级 1：增加父子文档召回或邻页扩展。

- 命中某个 chunk 后，额外带上同文档相邻页或同 section 的 chunk。
- 对事实型表格问题尤其重要，因为目标页附近经常存在标题页、估值表、盈利预测表等强相关内容。

优先级 2：对 compare 问题做实体拆分召回。

- 从 query 中识别两个公司名。
- 对每个公司分别发起一次子查询召回。
- 最终再与原始 query 的召回结果融合。
- 目标是保证两家公司至少各有若干候选 chunk 进入重排阶段。

优先级 3：对 summary 问题做 source-level 覆盖控制。

- 对政策汇总题，不只按 chunk 分数排序，还要控制来源文档多样性。
- 可以先按 source 聚合，每个 source 保留最高分 chunk，再做多文档覆盖排序。

优先级 4：引入 rerank 阶段。

- 当前只是 embedding + BM25 融合，还没有精排。
- 后续可按指导文档继续接入 bge-reranker，形成 2-stage retrieval：先多路召回，再 rerank 精排。

## 当前阶段结论

第一版混合召回已经跑通，并且 `weighted 0.6/0.4` 比默认 `0.5/0.5` 更适合作为当前默认实验参数。下一轮不建议继续只扫权重，应该开始做“查询拆解 + 父子文档/邻页扩展 + source 覆盖控制”，这些比继续微调融合权重更可能提升 badcase。
