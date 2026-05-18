# 重排实验：混合召回 + 页级父文档 + QAnything 阈值

- 评测时间：2026-05-18T13:02:07
- 评测集：`data/eval/financial_qa_dev.jsonl`
- 索引目录：`data/processed/indexes/bge_large_zh_v15`
- 索引类型：精确向量索引（`flat`）
- 候选来源：混合召回（向量 + BM25）
- 融合方式：加权融合，vector=0.6，bm25=0.4
- 匹配粒度：页码级
- 完成样本：120 / 120
- 跳过样本：0
- 总耗时（秒）：454.64
- 重排模型：`models/bge-reranker-v2-m3`
- 重排后端：本地 `transformers` 加载
- 候选召回数量：20
- 直接召回数量：5
- 重排后保留数量：5
- QAnything 阈值预设：启用
- 分数映射：`sigmoid`
- 绝对分数阈值：0.28
- 相对分差阈值：0.5
- 父文档模式：`page`
- 父文档展开阶段：`before-rerank`
- 邻页窗口：0
- 父文档最大字符数：不截断
- 逐样本详情：`docs/experiments/rerank/hybrid_parent_page_threshold_rerank.details.json`

## 实验设置

本实验参考 QAnything 的两阶段检索和父子文档机制：先用 child chunk 做混合召回，再把命中的 child chunk 回填为页级 parent 文档，随后使用 reranker 对 parent 文档进行重排，并启用 QAnything 风格的两层阈值过滤。

需要注意，本实验中的 `hybrid_top5` 也已经经过页级 parent 回填。因此它不是上一轮“普通混合召回 Top5”的完全同一设置，而是“混合召回 Top5 + page parent 展开”的直接召回基线。

## 总体结果

| scheme | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|
| hybrid_top5 | 82.65% | 91.67% | 74.17% |
| hybrid_top20_rerank_top5 | 81.12% | 91.67% | 71.67% |

结论：页级父文档展开后的直接混合召回表现很好，`HitAll@5` 达到 74.17%。但是在此基础上继续做 rerank 并启用 QAnything 阈值后，整体指标下降：`Recall@5` 下降 1.53 个百分点，`HitAll@5` 下降 2.50 个百分点，`HitAny@5` 持平。

所以这次实验说明两件事：

- `page parent` 展开本身是有效的，它能提升页码级证据覆盖。
- 当前的“parent before-rerank + QAnything 默认阈值”组合过于激进，不适合直接作为最终策略。

## 按问题类型统计

### 混合召回 Top5 + 页级父文档

| question_type | count | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|---:|
| compare | 30 | 78.33% | 96.67% | 60.00% |
| fact | 70 | 88.57% | 88.57% | 88.57% |
| summary | 20 | 68.42% | 95.00% | 45.00% |

### 混合召回 Top20 + 页级父文档 + Rerank + 阈值

| question_type | count | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|---:|
| compare | 30 | 75.00% | 93.33% | 56.67% |
| fact | 70 | 90.00% | 90.00% | 90.00% |
| summary | 20 | 59.25% | 95.00% | 30.00% |

分类型看，rerank + 阈值对事实型问题有小幅帮助：`HitAll@5` 从 88.57% 提升到 90.00%。但是对比型和汇总型都退化，尤其汇总型问题的 `HitAll@5` 从 45.00% 降到 30.00%。

这和任务特征是吻合的：事实型问题通常只需要一个强相关证据页，阈值过滤可以删掉噪声；对比型和汇总型往往需要多个证据页，阈值过滤和相对分差截断会把“第二、第三个必要证据”裁掉。

## 与前序实验对照

| scheme | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|
| vector_top5 | 78.25% | 88.33% | 69.17% |
| vector_top20_rerank_top5 | 82.29% | 90.00% | 74.17% |
| hybrid_top5 | 81.54% | 91.67% | 71.67% |
| hybrid_top20_rerank_top5 | 80.64% | 89.17% | 72.50% |
| hybrid_top5_parent_page | 82.65% | 91.67% | 74.17% |
| hybrid_top20_parent_page_threshold_rerank_top5 | 81.12% | 91.67% | 71.67% |

目前最值得保留的不是“阈值 rerank 结果”，而是 `hybrid_top5_parent_page` 这个发现：只做页级父文档展开，就已经把 `HitAll@5` 从普通混合召回的 71.67% 提升到 74.17%，并且 `HitAny@5` 仍保持 91.67%。

相比之下，`hybrid_top20_parent_page_threshold_rerank_top5` 没有超过前序最佳结果，也没有超过自己的直接召回基线。

## 阈值过滤影响

启用 QAnything 阈值后，rerank 输出结果并不总能保留满 5 个候选：

| scheme | avg_results | samples_with_less_than_5 |
|---|---:|---:|
| hybrid_top5 | 4.99 | 1 |
| hybrid_top20_rerank_top5 | 3.81 | 58 |

按问题类型看，rerank 后结果不足 5 个的分布如下：

| question_type | avg_results | samples_with_less_than_5 | count |
|---|---:|---:|---:|
| compare | 3.40 | 21 | 30 |
| fact | 3.79 | 32 | 70 |
| summary | 4.50 | 5 | 20 |

这说明当前阈值策略会显著缩短最终候选列表。对事实型问题来说，这有时能减少噪声；但对对比型和汇总型来说，少于 5 个候选会降低多证据覆盖概率。

## 变化样本

- 完整命中修复数：5
- 完整命中退化数：8
- `hybrid_top5` 未完整命中：31 / 120
- `hybrid_top20_rerank_top5` 未完整命中：34 / 120

### 重排后修复的样本

- `fact_036`
- `fact_049`
- `compare_010`
- `compare_012`
- `summary_018`

### 重排后退化的样本

- `fact_033`
- `compare_011`
- `compare_017`
- `compare_028`
- `summary_007`
- `summary_008`
- `summary_016`
- `summary_017`

退化样本中汇总型占 4 个，对比型占 3 个，说明“阈值截断 + 页级 parent rerank”对多证据任务不稳定。

## Badcase 观察

这次 badcase 的核心不是模型完全找不到相关文档，而是“找到部分相关文档后，无法同时保住多个必要证据”。例如：

- 对比题需要两个公司的证据页，阈值过滤后经常只留下其中一个公司的 parent。
- 汇总题需要多个政策文件或多个页码，reranker 会优先保留语义最贴近 query 的 parent，但不保证覆盖全部来源。
- 页级 parent 在 `before-rerank` 阶段会把候选文本变长，reranker 的 `max_length=512` 可能截断后半部分内容，使部分真正有用的证据没有进入 cross-encoder 的有效输入。

## 结论

这次实验的最佳结论是：**父子文档机制值得保留，但 QAnything 默认阈值不能照搬。**

更具体地说：

- `parent page` 能提高页码级证据覆盖，应继续作为后续上下文组装策略的一部分。
- `before-rerank` 展开 parent 后再 rerank，可能因为输入过长而影响排序稳定性。
- `score_threshold=0.28` 和 `relative_drop_threshold=0.5` 对当前金融研报评测集偏激进，尤其伤害对比型和汇总型任务。
- 当前阶段不应把 `hybrid_top20_parent_page_threshold_rerank_top5` 作为最终策略。

## 后续方向

下一轮建议做三个更小的对照实验：

1. `parent-stage after-rerank`：先对子 chunk rerank，再把 Top5 展开成页级 parent，观察是否保留 rerank 收益同时提高上下文完整度。
2. 关闭相对分差阈值，只保留绝对阈值，或把 `relative_drop_threshold` 调宽到 0.8，减少多证据任务被截断的问题。
3. 按问题类型路由：事实型可以尝试阈值过滤；对比型和汇总型优先保留固定 Top5，再做 parent page 或 window 展开。
