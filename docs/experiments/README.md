# Experiments

这个目录按实验主题归档，避免所有实验结果堆在同一层。

## 目录结构

- `chunking/`：切块实验记录。
- `eval_set/`：评测集构造说明。
- `rerank/`：第三周 reranker 对比实验。
- `retrieval/`：召回评测、混合召回调参和 badcase 分析。
- `retrieval/details/`：逐样本评测详情 JSON。
- `vector_index/`：向量索引构建实验记录。

## 当前重点

- 检索 baseline：`retrieval/retrieval_eval_baseline.md`
- 混合召回调参：`retrieval/retrieval_eval_hybrid_tuned.md`
- 向量召回 + Rerank 对比：`rerank/vector_top20_rerank_top5.md`
- 混合召回 + Rerank 对比：`rerank/hybrid_top20_rerank_top5.md`
- 混合召回 + 父文档 + QAnything 阈值：`rerank/hybrid_parent_page_threshold_rerank.md`
- badcase 分析：`retrieval/retrieval_badcase_and_hybrid_tuning.md`
