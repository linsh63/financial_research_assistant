# Rerank 检索 Badcase 分析

本文记录第三周 rerank、父子文档、compare 粗到细召回、summary 子主题召回实验中的 badcase 观察。当前结论基于 `09` 到 `18` 的实验，重点服务后续检索策略调优和生成阶段上下文选择。

## 当前最佳版本

当前检索侧推荐版本是：

```text
17_routed_compare_raw_entity_slots
```

对应策略：

```text
fact    -> hybrid_top5 + parent_window1
compare -> hybrid_top20 + LLM/rule rewrite + coarse_to_fine raw entity slots + rerank + parent_fill
summary -> hybrid_top50 + source_diverse_top8 + parent_window1
```

指标：

| question_type | Recall@8 | HitAny@8 | HitAll@8 | 结论 |
|---|---:|---:|---:|---|
| fact | 97.14% | 97.14% | 97.14% | 仍有少量真实漏召回。 |
| compare | 100.00% | 100.00% | 100.00% | 目前已被 raw coarse-to-fine entity slots 修复到全命中。 |
| summary | 88.08% | 100.00% | 75.00% | 当前主要短板。 |
| overall | 96.35% | 98.33% | 94.17% | 当前整体最稳。 |

参考文件：

- `docs/experiments/rerank/17_routed_compare_raw_entity_slots/report.md`
- `docs/experiments/rerank/17_routed_compare_raw_entity_slots/details.json`

## 实验脉络

| 实验 | 关键策略 | 主要结论 |
|---|---|---|
| `13_financial_table_query_rewrite_no_unit` | compare 财务表述改写，不带单位 | compare 提升到 Recall@8 95.00%、HitAll@8 93.33%，但 `compare_007`、`compare_008` 仍失败。 |
| `14_compare_coarse_to_fine` | compare 独立粗到细实验 | 单独实验中 compare 30 条达到 Recall@5/8 和 HitAll@5/8 100%，证明方向正确。 |
| `15_routed_with_compare_coarse_to_fine` | 把粗到细作为普通 supplement 接入 routed | compare HitAll@8 提升到 96.67%，但 `compare_008` 仍被 rerank 和 parent 逻辑挤掉。 |
| `16_routed_compare_entity_slots` | 每个 compare 实体加保障槽位，但仍先 rerank | HitAny 提升，但 HitAll 回落到 93.33%，说明 reranker 会把正确的实体页挤掉。 |
| `17_routed_compare_raw_entity_slots` | 保障槽位使用 raw coarse-to-fine 排序，不提前 rerank | compare 达到 100%，当前最稳。 |
| `18_routed_summary_subtopic_slots` | summary 子主题分路召回 + 硬保障槽位 | 修复 `summary_004`、`summary_020`，但弄坏 `summary_002`、`summary_003`、`summary_005`，不建议默认启用。 |

## Fact Badcase

当前剩余事实型坏例：

| 样本 | 问题 | 当前表现 | 初步判断 |
|---|---|---|---|
| `fact_047` | 2025 年，海达尔公司研发费用为多少 | 0/1 | 目标公司/指标没有被当前 hybrid_top5 稳定召回。 |
| `fact_049` | 海光信息公司 2024A 销售毛利率为多少 | 0/1 | 可能受公司名、指标口径、相近行业文档干扰。 |

处理建议：

1. 先复核 ground truth 的 source 和 page 是否准确。
2. 若数据集无误，再做事实型局部 query rewrite 或指标别名扩展。
3. 不建议为了这两条直接扩大所有 fact 的 TopK，因为 fact 当前 HitAll@8 已经是 97.14%，全局改动容易引入噪声。

## Compare Badcase

### 已解决的问题

早期 compare 的主要问题是“两家公司中只命中一方”，或目标证据被同业文档、相似年份、相似财务表格挤掉。典型样本包括：

| 样本 | 原问题 | 旧问题 | 当前状态 |
|---|---|---|---|
| `compare_003` | 千禾味业 vs 神农集团，哪家 26Q1 营收更高 | `SNJT.pdf` 解析质量差，神农集团召回不稳 | 单文件修复后进入后续链路。 |
| `compare_007` | 普蕊斯 vs 普瑞眼科，预计 2026 年营收更高 | “预计 2026 年营收”与表格字段 `2026E/营收` 表述不贴近 | no-unit 财务表述改写后改善。 |
| `compare_008` | 昭衍新药 vs 通策医疗，预计 2026 年营收更高 | `TCYL.pdf` 和 `SYXY.pdf` 正确页容易被同业文档挤掉 | raw coarse-to-fine entity slots 修复。 |
| `compare_021` | 华源控股 vs 海光信息，2026Q1 营收更高 | 海光信息被行业月报、弱相关半导体文档干扰 | raw coarse-to-fine entity slots 修复。 |

### 为什么 raw coarse-to-fine 有效

独立粗到细实验 `14` 的流程是：

```text
先用公司实体定位 PDF -> 再在定位出的 PDF 内查年份/指标页 -> 父文档窗口回填
```

它对 compare 很合适，因为 compare 问题天然有两个明确实体。后续接入 routed 时，关键教训是：

- 只作为普通 supplement 不够，正确候选仍可能被 reranker 挤掉。
- “实体保障槽位 + rerank”也不够，reranker 会偏向包含大量年份/指标词的同业文档。
- 最终有效做法是：**保障槽位使用 raw coarse-to-fine 排序，不提前 rerank**。

当前 compare 可以暂时视为检索侧已跑通，下一步重点转向生成阶段的数字提取和单位一致性。

## Summary Badcase

summary 是当前检索侧主要短板。`17` 下 summary 仍有 5 条 page-level 未完全命中：

| 样本 | 覆盖 | 主要原因 |
|---|---:|---|
| `summary_001` | 3/4 | hybrid_top50 中已命中 4/4，但 final top8 没保住 `ndrc_2024_new_power_system_action_plan.pdf` 的正确页。属于页内定位/最终保留问题。 |
| `summary_003` | 2/3 | 缺 `P020240806534738672970.pdf`，原 query 对该目标文档召回信号不足。 |
| `summary_004` | 1/5 | 多主题问题，涉及配电网、电力市场、容量电价、新能源报价。部分目标文档没进 top50，部分进了但 final top8 没保住。 |
| `summary_012` | 2/3 | `P020200728576152165824.pdf` 文档可进 hybrid top50，但目标页没命中。属于页内定位问题。 |
| `summary_020` | 1/3 | 低空经济命中，但职业教育和人工智能制造两个子主题没有被原 query 召回；还混入公司研报。 |

### 根因拆分

summary 低召回不是单一问题，而是三类问题叠加：

1. **多主题问题没有分路召回**

   例如 `summary_004` 一题同时包含：

   ```text
   配电网建设
   全国统一电力市场
   发电侧容量电价
   新能源市场报价
   ```

   当前默认 summary 是一条大 query 做一次 hybrid_top50，因此强语义主题会挤掉弱语义政策。

2. **source_diverse 只懂来源去重，不懂主题配额**

   `source_diverse_top8` 能避免单个 PDF 占满结果，但不知道“每个政策子主题至少保留一个证据位”。所以 `summary_004` 中一些文档即使在 hybrid_top50 中出现，也可能没有进入最终 Top8。

3. **页内定位不稳定**

   `summary_001` 和 `summary_012` 属于已经找到目标文档，但选错页或没保住目标页。这类问题不需要更多文档，而需要在已定位文档内做页级二次定位。

### `18` 子主题实验的教训

`18_routed_summary_subtopic_slots` 尝试了：

```text
summary query -> 子主题拆分 -> 每个子主题独立 hybrid -> 每路硬保障槽位 -> source_diverse
```

它修复了两个最典型的多主题问题：

| 样本 | 17 | 18 | 说明 |
|---|---:|---:|---|
| `summary_004` | 1/5 | 3/5 | 子主题召回找回容量电价和新能源市场报价相关政策。 |
| `summary_020` | 1/3 | 3/3 | 子主题召回找回职业教育和人工智能制造政策。 |

但整体不升反降：

| 指标 | 17 | 18 | 变化 |
|---|---:|---:|---:|
| Summary Recall@8 | 88.08% | 87.50% | -0.58 |
| Summary HitAll@8 | 75.00% | 70.00% | -5.00 |
| Overall HitAll@8 | 94.17% | 93.33% | -0.84 |

负向样本：

| 样本 | 17 | 18 | 问题 |
|---|---:|---:|---|
| `summary_002` | 5/5 | 2/5 | 子主题硬槽位混入 `LXDQ.pdf`、`TCL.pdf` 等无关候选，挤掉原本正确政策。 |
| `summary_003` | 2/3 | 1/3 | 子主题排序改变后，可再生能源/氢能原本命中的证据被挤掉。 |
| `summary_005` | 4/4 | 3/4 | 设备更新题被房地产研报等噪声影响。 |

结论：summary 子主题方向有效，但不能作为全量硬插队策略。

## 当前推荐路线

### 默认检索策略

继续使用 `17_routed_compare_raw_entity_slots` 作为当前最佳检索版本：

```text
fact    -> hybrid_top5 + parent_window1
compare -> compare rewrite + raw coarse-to-fine entity slots + rerank + parent_fill
summary -> hybrid_top50 + source_diverse_top8 + parent_window1
```

### 下一轮 summary 实验

不要继续全量强制 `summary_subtopic_slots`。更稳的路线是：

1. 先跑默认 summary 路线。
2. 只在疑似多主题或默认结果覆盖不足时启用子主题补召回。
3. 子主题候选不要排在 base 前面，而是作为 fallback 或 supplement。
4. 子主题结果只补入新的 source，避免挤掉已经命中的目标 source。
5. 对已命中文档但页码不对的 case，做文档内页级二次定位，而不是召回更多文档。

可命名为：

```text
19_routed_summary_subtopic_fallback
```

预期目标：

- 保留 `summary_002`、`summary_003`、`summary_005` 原本的命中。
- 修复或部分修复 `summary_004`、`summary_020`。
- 避免非政策研报噪声进入最终 Top8。这里暂不做 filter，而是通过“只补新 source + 不强插队”控制风险。

## 后续记录模板

每次新增 badcase 修复实验后，在本节追加：

```markdown
### 实验编号

- 目标：
- 改动：
- 指标变化：
- 修复样本：
- 回退样本：
- 是否进入默认策略：
- 下一步：
```
