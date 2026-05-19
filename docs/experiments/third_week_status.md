# 第三周完成度总结

本文档对照 `docs/project_guide_project2.md` 中“第 3 周：重排 + 生成 + 故障处理”的要求，记录当前完成情况。当前正式路线使用旧版稳定链路：

```text
检索：17_routed_compare_raw_entity_slots
生成：默认 prompt 约束
模型：DeepSeek deepseek-chat
```

探索性 `summary_evidence_pack` 暂不纳入正式路线。

## 1. 指导文档要求

第三周包含三件事：

1. 接入 reranker
   - 使用 `bge-reranker-v2-m3`
   - 对比“向量召回 Top20 + rerank Top5”与“直接 Top5”
   - 记录 Recall 和准确率变化
2. 生成约束
   - 只引用检索到的证据回答
   - 证据不足时明确说明无法确定
   - 通过 prompt 降低幻觉
3. 故障处理
   - 记录空召回、答非所问、幻觉、延迟等 badcase
   - 分析根因并说明修复方式

## 2. 完成情况总览

| 模块 | 完成度 | 说明 |
|---|---:|---|
| Reranker 接入 | 100% | 已接入本地 `bge-reranker-v2-m3`，完成向量/混合召回多组对比。 |
| 两阶段检索实验 | 100% | 已跑 `vector_top20_rerank_top5`、`hybrid_top20_rerank_top5`、阈值、父子文档和路由策略。 |
| QAnything 思路借鉴 | 100% | 已实现两阶段检索、rerank 阈值、父子文档窗口，并记录哪些策略有效。 |
| 生成约束 | 90% | 已实现引用约束、证据不足拒答、按题型 prompt；仍需针对 fact 拒答和 summary 扩写继续小修。 |
| 生成评测 | 100% | 已实现规则评测和 LLM judge，完成 120 条全量生成评测。 |
| Badcase 分析 | 90% | 检索侧和生成侧 badcase 文档已更新；summary 后续放入第四周评测闭环继续优化。 |

总体完成度：**约 90%**。第三周主线已经跑通，可以进入第四周；剩余工作主要是生成端小步调优和最终文档整合。

## 3. Reranker 实验结果

### 3.1 向量召回 Top20 + rerank Top5

相关文档：

- `docs/experiments/rerank/01_vector_top20_rerank_top5/report.md`

结果：

| scheme | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|
| vector_top5 | 78.25% | 88.33% | 69.17% |
| vector_top20_rerank_top5 | 82.29% | 90.00% | 74.17% |

结论：向量 Top20 进入 rerank 后，Recall@5 提升 4.04 个百分点，HitAll@5 提升 5.00 个百分点，是稳定有效的 rerank baseline。

### 3.2 混合召回 Top20 + rerank Top5

相关文档：

- `docs/experiments/rerank/02_hybrid_top20_rerank_top5/report.md`

结果：

| scheme | Recall@5 | HitAny@5 | HitAll@5 |
|---|---:|---:|---:|
| hybrid_top5 | 81.54% | 91.67% | 71.67% |
| hybrid_top20_rerank_top5 | 80.64% | 89.17% | 72.50% |

结论：混合召回加 rerank 对 compare 有帮助，但会引入事实题噪声。由此引出了按题型路由策略。

## 4. 当前最佳检索版本

当前推荐检索版本：

```text
17_routed_compare_raw_entity_slots
```

相关文档：

- `docs/experiments/rerank/17_routed_compare_raw_entity_slots/report.md`
- `docs/experiments/rerank/badcase_analysis.md`

策略：

```text
fact    -> hybrid_top5 + parent_window1
compare -> hybrid_top20 + query rewrite + raw coarse-to-fine entity slots + rerank + parent_fill
summary -> hybrid_top50 + source_diverse_top8 + parent_window1
```

指标：

| scheme | Recall@5 | Recall@8 | HitAny@5 | HitAny@8 | HitAll@5 | HitAll@8 |
|---|---:|---:|---:|---:|---:|---:|
| routed_v17 | 94.90% | 96.35% | 98.33% | 98.33% | 90.83% | 94.17% |

按题型：

| question_type | Recall@8 | HitAny@8 | HitAll@8 |
|---|---:|---:|---:|
| fact | 97.14% | 97.14% | 97.14% |
| compare | 100.00% | 100.00% | 100.00% |
| summary | 88.08% | 100.00% | 75.00% |

## 5. 生成约束与全量评测

相关文档：

- `docs/experiments/generation/routed_v17_deepseek_full/report.md`
- `docs/experiments/generation/routed_v17_deepseek_full_judge/report.md`
- `docs/experiments/generation/badcase_analysis/report.md`

生成约束已包含：

- 只根据给定资料回答。
- 必须保留关键数字、口径和时间。
- 必须使用 `[资料1]` 形式引用。
- 证据不足时说明“根据现有资料无法确定”。
- fact / compare / summary 分别使用不同输出要求。

DeepSeek 全量结果：

| metric | value |
|---|---:|
| answer_rate | 100.00% |
| citation_rate | 97.50% |
| reference_recall | 95.97% |
| reference_hit_all | 93.33% |
| numeric_coverage | 86.31% |
| judge_correct_rate | 80.00% |
| judge_avg_score | 86.62 |

按题型：

| question_type | judge_correct_rate | judge_avg_score | reference_hit_all | numeric_coverage |
|---|---:|---:|---:|---:|
| fact | 82.86% | 86.07 | 97.14% | 86.76% |
| compare | 93.33% | 96.17 | 100.00% | 96.11% |
| summary | 50.00% | 74.25 | 70.00% | 45.74% |

结论：

- compare 已经是当前最强模块。
- fact 可用，但需要修“证据已出现但模型拒答/取错数字”。
- summary 仍是第四周重点。

## 6. 故障处理记录

### 6.1 已处理或已定位的问题

| 故障类型 | 代表样本 | 根因 | 当前处理 |
|---|---|---|---|
| compare 单边召回 | `compare_002`, `compare_008`, `compare_021` | 一条 query 很难同时召回两个公司同口径证据 | 引入 query rewrite、粗到细召回、实体保障槽位。 |
| 表格字段表述不贴近 | `compare_007` | “预计 2026 年营收”与 `2026E/营收` 字段不一致 | 规则化财务表述改写，不带单位。 |
| PDF 解析问题 | `compare_003` 神农集团 | 单文件 PDF 文本抽取质量影响召回 | 做了 SNJT 单文件修复，不影响其他 PDF。 |
| rerank 挤掉正确候选 | `compare_008` | 正确页进入候选后被 reranker 排低 | 使用 raw coarse-to-fine entity slots 保证实体证据。 |
| summary 多主题覆盖不足 | `summary_004`, `summary_020` | 单 query 被强主题主导，弱主题被挤掉 | 实验过 summary 子主题槽位，但不稳定，暂不默认启用。 |
| 生成端拒答 | `fact_005`, `fact_029`, `compare_021` | prompt 过于谨慎或表格读取不稳定 | 已记录到生成 badcase，后续小修。 |

### 6.2 当前不纳入默认的实验

| 实验 | 结论 |
|---|---|
| `18_routed_summary_subtopic_slots` | 修复部分 summary 多主题样本，但使其他 summary 回退，不默认启用。 |
| `summary_evidence_pack_deepseek` | 回答更规整，但小批 reference recall 下降，暂不接入主流程。 |

## 7. 是否可以进入第四周

可以进入。

第三周的核心要求已经满足：

- reranker 已接入并完成对比实验。
- 生成链路已跑通，具备引用约束。
- 已有全量规则评测和 LLM judge。
- 已有可讲清楚的 badcase 和修复脉络。

进入第四周前建议保留的正式版本：

```text
retrieval: 17_routed_compare_raw_entity_slots
generation: default prompt
model: DeepSeek deepseek-chat 或可切回 GPT-5.4 mini 对比
```

## 8. 下一步

第四周重点应转向：

1. 做最终评测闭环：
   - 固定正式配置。
   - 跑一次全量生成。
   - 跑规则评测和 LLM judge。
   - 汇总最终指标。
2. 做 Demo：
   - 输入问题。
   - 展示召回证据。
   - 展示生成答案。
   - 展示引用来源和页码。
3. 补最终文档：
   - 系统架构图。
   - 实验对比表。
   - badcase 修复记录。
   - 项目 README 的复现实验命令。
