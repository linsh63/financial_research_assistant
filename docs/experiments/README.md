# 实验文档索引

这个目录按实验主题归档，避免所有实验结果堆在同一层。

## 目录结构

- `chunking/`：切块实验记录。
- `eval_set/`：评测集构造说明。
- `rerank/`：第三周 reranker、阈值过滤、父子文档召回实验。
- `retrieval/`：召回评测、混合召回调参和 badcase 分析。
- `retrieval/details/`：逐样本评测详情 JSON。
- `vector_index/`：向量索引构建实验记录。
- `summary.md`：阶段性实验总览和当前最佳策略。

## 当前重点

- 检索 baseline：`retrieval/retrieval_eval_baseline.md`
- 混合召回调参：`retrieval/retrieval_eval_hybrid_tuned.md`
- 阶段性总览：`summary.md`
- 向量召回 + Rerank 对比：`rerank/01_vector_top20_rerank_top5/report.md`
- 混合召回 + Rerank 对比：`rerank/02_hybrid_top20_rerank_top5/report.md`
- 混合召回 + 父文档 + QAnything 阈值：`rerank/03_hybrid_parent_page_threshold/report.md`
- Rerank 后展开页级父文档：`rerank/04_hybrid_rerank_parent_page_after/report.md`
- Rerank 后展开邻页父文档：`rerank/05_hybrid_rerank_parent_window1_after/report.md`
- badcase 分析：`retrieval/retrieval_badcase_and_hybrid_tuning.md`
