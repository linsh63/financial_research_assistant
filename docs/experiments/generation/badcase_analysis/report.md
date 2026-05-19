# 生成阶段 Badcase 分析

本文档记录回答生成阶段的主要错误类型、代表案例和后续处理方向。当前正式分析以旧版稳定生成链路为准：

```text
检索：17_routed_compare_raw_entity_slots
生成：默认 prompt 约束，不启用 summary evidence pack 实验线
模型：DeepSeek deepseek-chat
```

相关文件：

- 生成结果：`data/generated/eval_runs/routed_v17_deepseek_full_answers.jsonl`
- 规则评测：`docs/experiments/generation/routed_v17_deepseek_full/report.md`
- LLM judge：`docs/experiments/generation/routed_v17_deepseek_full_judge/report.md`
- 逐样本详情：`docs/experiments/generation/details/routed_v17_deepseek_full_judge/details.json`

注意：`summary_evidence_pack_deepseek` 是一次探索性失败实验，暂不纳入当前正式路线。

## 1. 当前整体结果

| metric | value |
|---|---:|
| eval_samples | 120 |
| answer_rate | 100.00% |
| citation_rate | 97.50% |
| reference_recall | 95.97% |
| reference_hit_any | 98.33% |
| reference_hit_all | 93.33% |
| numeric_coverage | 86.31% |
| judge_correct_rate | 80.00% |
| judge_avg_score | 86.62 |

按问题类型看：

| question_type | count | judge_correct_rate | judge_avg_score | reference_hit_all | numeric_coverage |
|---|---:|---:|---:|---:|---:|
| fact | 70 | 82.86% | 86.07 | 97.14% | 86.76% |
| compare | 30 | 93.33% | 96.17 | 100.00% | 96.11% |
| summary | 20 | 50.00% | 74.25 | 70.00% | 45.74% |

和上一版 GPT-5.4 mini 全量结果相比：

| metric | GPT-5.4 mini | DeepSeek |
|---|---:|---:|
| judge_correct_rate | 67.50% | 80.00% |
| judge_avg_score | 81.17 | 86.62 |
| compare_correct_rate | 73.33% | 93.33% |
| fact_correct_rate | 84.29% | 82.86% |
| summary_correct_rate | 0.00% | 50.00% |

初步判断：

- 对比型已经明显改善，当前主要剩下“证据已命中但生成端说无法确定”的问题。
- 事实型仍有少量“证据命中但取错数字或拒答”的问题。
- 汇总型仍是生成阶段最弱环节，主要是覆盖不完整、关键数字缺失和风格扩写。

## 2. 错误类型汇总

LLM judge 判错 24 条：

| question_type | failed_count | reference_miss | number_miss | no_citation | 主要问题 |
|---|---:|---:|---:|---:|---|
| fact | 12 | 2 | 9 | 2 | 证据多数已命中，但模型取错数字、拒答或选择相近口径。 |
| compare | 2 | 0 | 2 | 0 | 检索证据齐全，但生成端未抽出其中一方关键数字。 |
| summary | 10 | 5 | 5 | 0 | 多政策、多数字、多要点覆盖不完整。 |

失败样本：

- fact：`fact_005`, `fact_007`, `fact_021`, `fact_024`, `fact_028`, `fact_029`, `fact_035`, `fact_036`, `fact_044`, `fact_045`, `fact_047`, `fact_049`
- compare：`compare_007`, `compare_021`
- summary：`summary_001`, `summary_003`, `summary_004`, `summary_009`, `summary_011`, `summary_012`, `summary_014`, `summary_015`, `summary_018`, `summary_020`

## 3. 事实型 Badcase

### 3.1 命中证据但拒答

代表样本：

- `fact_005`
  - 问题：隆基绿能 26Q1 费用率同比提升了多少？
  - 标准答案：8.3pct
  - 生成答案：声称无法确定，但同一段依据中已经出现 `+8.3pct`
  - 根因：生成约束过于谨慎，模型把“期间费用率”与“费用率”口径拆得过细，导致错误拒答。

- `fact_029`
  - 问题：金域医学2026Q1实现归母净利润多少
  - 标准答案：0.43 亿元
  - 生成答案：正文里给出了 0.43 亿元，但结论仍然说无法确定
  - 根因：模型识别到数字，但被来源缩写、公司名映射等信息干扰，结论没有落到直接答案。

处理方向：

- 对事实型 prompt 保持“不要编造”的约束，但需要增加一句：如果同一资料明确出现与问题匹配的公司、期间、指标和数字，应直接给出数字，不要再以口径谨慎为由拒答。
- 对上下文中的公司简称和文件名缩写，尽量在 references 或 context header 中保留原始 source，帮助模型确认文档归属。

### 3.2 命中证据但取错数字

代表样本：

- `fact_021`
  - 问题：爱尔眼科归属母公司净利润是多少
  - 标准答案：11.81 亿元
  - 生成答案：32.40 亿元
  - 根因：同一页存在多个期间的归母净利润，模型选中了错误时间口径。

- `fact_036`
  - 问题：截至 2025 年末，金地集团有息负债多少
  - 标准答案：672 亿元
  - 生成答案：无法确定
  - 根因：页面中同时有有息负债绝对值、占比、增速等信息，模型没有定位到目标数值。

- `fact_045`
  - 问题：飞荣达公司2025主营收入为多少
  - 标准答案：6527 百万元
  - 生成答案：无法确定
  - 根因：表格字段中存在“主营收入（百万元）”，但模型把营业收入、主营收入和分业务收入区分得过于保守。

处理方向：

- 生成端不要让模型自行换算或推理，优先摘录原始表格行。
- 事实型 context formatter 后续可以做 question-aware 证据压缩：优先保留同时包含公司、年份/季度、指标词、数字的句子或表格行。
- 对 `has_table=true` 的 chunk，生成阶段尽量完整保留相关表格行，避免截断。

### 3.3 真实检索失败

代表样本：

- `fact_047`：海达尔 2025 年研发费用，reference coverage 为 0/1。
- `fact_049`：海光信息 2024A 销售毛利率，reference coverage 为 0/1。

处理方向：

- 这两条优先复核 ground truth 的 source/pages。
- 如果评测集无误，再考虑只针对 fact 的公司 alias 或指标别名补召回；不建议全局扩大 fact TopK。

## 4. 对比型 Badcase

当前 compare 的检索侧已经达到 100% HitAll，剩余问题集中在生成端。

### 4.1 证据齐全但模型漏抽一方数字

代表样本：

- `compare_007`
  - 问题：普蕊斯 vs 普瑞眼科，预计哪家公司在2026年的营收更高
  - 标准答案：普瑞眼科更高；普蕊斯 2026E 营收 931.69 百万元，普瑞眼科 2026E 营收 3136 百万元
  - 当前状态：reference coverage 为 2/2，但生成答案说普瑞眼科 2026 年全年营收预测缺失
  - 根因：模型看到了正确文档，但没有从预测表中抽出 `2026E / 营收`。

- `compare_021`
  - 问题：华源控股 vs 海光信息，哪家公司2026年Q1实现营收更高
  - 标准答案：海光信息更高；华源控股 5.85 亿元，海光信息 40.34 亿元
  - 当前状态：reference coverage 为 2/2，但生成答案说华源控股 2026Q1 营收缺失
  - 根因：同样是表格/季度字段读取失败，而不是召回失败。

处理方向：

- compare 生成 prompt 已经要求先列双方数字再给结论，后续应加强“若 references 中已包含双方文档，不要轻易判定某一方缺失”。
- 对 compare 可以在 context formatter 层按公司分组展示证据，避免模型在混合上下文中漏看一方。
- 保留原始单位，不要求模型换算；判断大小时只在必要时再做单位统一。

## 5. 汇总型 Badcase

summary 的主要问题不是“完全不会答”，而是多文档覆盖不完整，且答案风格容易偏说明文。

### 5.1 多政策证据覆盖不足

代表样本：

- `summary_001`
  - reference coverage：2/4
  - 缺失：2024-2027 年 9 项专项行动、2025-2027 年年均新增 2 亿千瓦以上新能源合理消纳利用、全国新能源利用率不低于 90%、到 2027 年新型储能装机 1.8 亿千瓦以上。

- `summary_004`
  - reference coverage：1/5
  - 缺失：市场化交易电量占全社会用电量 70% 左右、新能源报价政策等。

- `summary_020`
  - 低空经济、教育、人工智能制造多个子主题需要同时覆盖，默认 summary 路由仍容易偏向其中一个主题。

处理方向：

- 当前不采用 `summary_subtopic_slots` 作为默认策略，因为实验 18 虽修复 `summary_004` 和 `summary_020`，但使 `summary_002`、`summary_003`、`summary_005` 回退。
- 后续更稳的路线是 summary 子主题 fallback：默认结果先保留，只在多主题缺口明显时补新 source，不强行插队。

### 5.2 风格扩写与答案不贴合

代表样本：

- `summary_009`
  - 问题：绿色低碳转型产业指导目录覆盖哪些主要产业方向
  - 现象：只覆盖节能降碳产业和绿色服务，遗漏环境保护、资源循环利用、能源绿色低碳转型、生态保护修复、基础设施绿色升级等方向，还加入了标准答案未提及的先进交通装备制造。

- `summary_014`
  - 问题：国家区域医疗中心建设和健康产业高质量发展政策怎样扩大优质服务供给
  - 现象：遗漏补齐短板、中医药服务贸易等要点，加入了标准答案未提及的社会办医等内容。

- `summary_015`
  - 问题：生物经济规划和高端医疗器械药品产业化政策如何推动生命健康产业发展
  - 现象：核心方向正确，但遗漏基础研究、合成生物学、干细胞治疗、生物环保、生物能源等关键点。

处理方向：

- prompt 已经要求 summary 尽量使用原文，但仍需配合更好的上下文组织。
- 后续可以把 summary 上下文按政策文件分组，并在每组前提示“只总结该文件命中的目标/任务/机制/数字”，减少模型自由重组。

## 6. 已尝试但暂不纳入默认的实验

### 6.1 summary evidence pack

实验文件：

- `data/generated/eval_runs/summary_evidence_pack_deepseek_subset_answers.jsonl`
- `docs/experiments/generation/summary_evidence_pack_deepseek/subset_report.md`

初步结论：

- 小批量前 5 条 summary 中，证据包让回答更长、更规整，但 reference recall 从旧版前 5 条的 63.33% 降到 47.67%。
- 这次实验同时启用了 `summary_subtopic_slots`，导致检索上下文也变了，不适合作为正式对比。
- 当前不接入默认生成路线。

### 6.2 DeepSeek 与 GPT-5.4 mini 的差异

- DeepSeek 在 compare 和 summary 上明显优于 GPT-5.4 mini。
- fact 略低于 GPT-5.4 mini，主要表现为更容易谨慎拒答。
- 因此当前修 fact 时要避免过度强化“无法确定”，而应该强调“证据明确时直接回答”。

## 7. 下一步计划

短期优先级：

1. **先固定旧版正式路线**
   - 继续使用 `routed_v17` 检索 + 默认生成 prompt。
   - 不把 summary evidence pack 接入主流程。

2. **小步修事实型拒答**
   - 针对 `fact_005`, `fact_029`, `fact_045` 这类“证据已出现但模型说无法确定”的样本做 prompt/context 小修。
   - 要求只影响 fact，不动 compare 和 summary。

3. **compare 只做生成端表格读取优化**
   - compare 检索侧已经 100% HitAll，不能再大改召回。
   - 重点是让模型从双方 evidence 中稳定抽取 `2026E / 营收`、`2026Q1 / 营收` 等字段。

4. **summary 放到第四周评测闭环继续做**
   - 第三周已经完成故障定位。
   - 后续更适合结合人工抽查、RAGAS/LLM judge、上下文组织做闭环优化。

## 8. 后续记录模板

```text
## yyyy-mm-dd 修复记录

### 改动

- 改动范围：
- 是否影响其他题型：

### 复测范围

- subset / full：
- 模型：

### 指标变化

| metric | before | after |
|---|---:|---:|
| judge_correct_rate |  |  |
| fact_correct_rate |  |  |
| compare_correct_rate |  |  |
| summary_correct_rate |  |  |
| reference_hit_all |  |  |
| numeric_coverage |  |  |

### 仍失败样本

- question_id：
- 现象：
- 下一步：
```
