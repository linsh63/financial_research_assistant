# 实验文档索引

这个目录按实验主题归档，避免所有实验结果堆在同一层。

## 目录结构

- `chunking/`：切块实验记录。
- `eval_set/`：评测集构造说明。
- `generation/`：回答生成阶段的自动评测。
- `rerank/`：第三周 reranker、阈值过滤、父子文档召回实验。
- `retrieval/`：召回评测、混合召回调参和 badcase 分析。
- `retrieval/details/`：逐样本评测详情 JSON。
- `vector_index/`：向量索引构建实验记录。
- `summary.md`：阶段性实验总览和当前最佳策略。
- `third_week_status.md`：第三周“重排 + 生成 + 故障处理”的完成度总结。

## 当前重点

- 检索 baseline：`retrieval/retrieval_eval_baseline.md`
- 混合召回调参：`retrieval/retrieval_eval_hybrid_tuned.md`
- 阶段性总览：`summary.md`
- 第三周完成度：`third_week_status.md`
- 向量召回 + Rerank 对比：`rerank/01_vector_top20_rerank_top5/report.md`
- 混合召回 + Rerank 对比：`rerank/02_hybrid_top20_rerank_top5/report.md`
- 混合召回 + 父文档 + QAnything 阈值：`rerank/03_hybrid_parent_page_threshold/report.md`
- Rerank 后展开页级父文档：`rerank/04_hybrid_rerank_parent_page_after/report.md`
- Rerank 后展开邻页父文档：`rerank/05_hybrid_rerank_parent_window1_after/report.md`
- 当前最佳路由检索：`rerank/17_routed_compare_raw_entity_slots/report.md`
- 生成效果评测：`generation/README.md`
- 检索 badcase 分析：`rerank/badcase_analysis.md`
- 生成 badcase 分析：`generation/badcase_analysis/report.md`

系统架构、Demo 和面试准备已经移到上一级正式文档：

- `../architecture.md`
- `../demo.md`
- `../interview/high_frequency_questions.md`
