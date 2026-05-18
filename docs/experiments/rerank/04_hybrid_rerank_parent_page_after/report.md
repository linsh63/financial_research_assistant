# 调优实验：Rerank 后展开页级父文档

- 评测时间：2026-05-18T13:14:33
- 评测集：`data/eval/financial_qa_dev.jsonl`
- 索引目录：`data/processed/indexes/bge_large_zh_v15`
- 候选来源：混合召回（向量 + BM25）
- 融合方式：加权融合，vector=0.6，bm25=0.4
- 匹配粒度：页码级
- 完成样本：120 / 120
- 总耗时（秒）：349.51
- 重排模型：`models/bge-reranker-v2-m3`
- 候选召回数量：20
- 重排后保留数量：5
- 阈值过滤：未启用
- 父文档模式：`page`
- 父文档展开阶段：`after-rerank`
- 逐样本详情：`docs/experiments/rerank/04_hybrid_rerank_parent_page_after/details.json`

## 实验目的

上一轮 `before-rerank` 的问题是：先把 child chunk 展开成 page parent，再送入 reranker，会让输入文本变长，`max_length=512` 截断可能影响排序；同时 QAnything 默认阈值会把多证据任务裁得过狠。

本实验改成：先对子 chunk 做混合召回 + rerank，再把最终结果展开成页级 parent。这样 reranker 仍然看短文本，最终交给下游问答时再拿完整页上下文。

## 总体结果

| scheme | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|
| hybrid_top5 | 81.54% | 91.67% | 71.67% |
| hybrid_top20_rerank_top5 | 80.64% | 89.17% | 72.50% |

这个结果和普通混合召回 + rerank 基本一致。原因很直接：当前评测是页码级命中，`page parent` 展开并不会改变命中的页码集合，只是把同一页的上下文文本补全。因此它对后续生成回答有价值，但不会在页码级 Recall 指标里体现出额外收益。

## 按问题类型统计

### 混合召回直接前 5

| question_type | count | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|---:|
| compare | 30 | 75.00% | 96.67% | 53.33% |
| fact | 70 | 88.57% | 88.57% | 88.57% |
| summary | 20 | 66.75% | 95.00% | 40.00% |

### 混合召回前 20 + Rerank 前 5 + 页级父文档

| question_type | count | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|---:|
| compare | 30 | 81.67% | 93.33% | 70.00% |
| fact | 70 | 84.29% | 84.29% | 84.29% |
| summary | 20 | 66.33% | 100.00% | 35.00% |

## 结论

`parent-stage after-rerank + parent-mode page` 是合理的上下文组装方式，但它不是解决页码召回问题的关键。它适合在最终问答阶段使用：检索和 rerank 仍然针对短 child chunk，返回给 LLM 时再补全同页上下文。

如果目标是提升页码级评测指标，需要使用 `window` 父文档，把相邻页也带回来。
