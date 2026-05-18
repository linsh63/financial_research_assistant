# 生成阶段 Badcase 分析初稿

本文档用于记录回答生成阶段的主要错误类型、代表案例、初步原因判断和后续修复计划。当前结论基于以下评测结果：

- 规则评测：`docs/experiments/generation/routed_gpt54mini_full/report.md`
- LLM judge：`docs/experiments/generation/routed_gpt54mini_full_judge/report.md`
- 逐样本详情：`docs/experiments/generation/details/routed_gpt54mini_full_judge/details.json`

注意：本文档是初稿。之后修复 prompt、context formatter、检索策略或评测集后，需要在本文档中追加“修复前后对比”。

## 1. 当前整体结果

| metric | value |
|---|---:|
| eval_samples | 120 |
| answer_rate | 100.00% |
| citation_rate | 100.00% |
| reference_recall | 93.89% |
| reference_hit_all | 90.00% |
| numeric_coverage | 83.69% |
| judge_correct_rate | 67.50% |
| judge_avg_score | 81.17 |

按问题类型看：

| question_type | count | judge_correct_rate | judge_avg_score | reference_hit_all | numeric_coverage |
|---|---:|---:|---:|---:|---:|
| fact | 70 | 84.29% | 86.81 | 97.14% | 85.29% |
| compare | 30 | 73.33% | 80.73 | 86.67% | 90.83% |
| summary | 20 | 0.00% | 62.10 | 70.00% | 43.24% |

初步判断：

- 事实型已经比较接近可用，但仍存在“证据命中后取错数字”的问题。
- 对比型主要问题是召回缺失对比双方之一，或答案中数字和结论不一致。
- 汇总型是当前最弱环节，主要问题是覆盖不完整、风格扩展、没有严格贴合 ground truth 的政策要点。

## 2. 错误类型汇总

| question_type | failed_count | reference_miss | number_miss | 主要问题 |
|---|---:|---:|---:|---|
| fact | 11 | 2 | 10 | 多数不是纯检索失败，而是已命中相关资料后取错数字、自己计算或误判无法确定 |
| compare | 8 | 4 | 8 | 部分缺少一方资料，部分虽然资料齐全但比较结论或数字错位 |
| summary | 20 | 6 | 6 | judge 全部判错，主要是答案覆盖不足、扩写较多、政策目标和关键数字缺失 |

失败样本：

- fact：`fact_002`, `fact_004`, `fact_008`, `fact_013`, `fact_021`, `fact_036`, `fact_043`, `fact_045`, `fact_047`, `fact_049`, `fact_055`
- compare：`compare_002`, `compare_003`, `compare_007`, `compare_008`, `compare_013`, `compare_021`, `compare_028`, `compare_029`
- summary：`summary_001` 到 `summary_020`

## 3. 事实型 Badcase

### 3.1 证据命中但模型取错数字

代表样本：

- `fact_036`：问“截至 2025 年末，金地集团有息负债多少”
  - 标准答案：672 亿元
  - 生成答案：1231 亿元
  - 现象：引用资料命中，但模型选中了错误口径或相邻指标。

- `fact_013`：问“安琪酵母2025A净利润为多少”
  - 标准答案：15.89 亿元
  - 生成答案：15.44 亿元
  - 现象：模型将相近口径数字当成答案，说明 prompt 需要更强约束“公司、年份、指标口径必须完全匹配”。

- `fact_021`：问“爱尔眼科归属母公司净利润是多少”
  - 标准答案：11.81 亿元
  - 生成答案：同时回答了 2025 年和 2026Q1 的归母净利润。
  - 现象：答案包含正确数字，但额外引入无关期间，导致答案焦点不稳定。

初步原因：

- context 中可能包含同一公司多个年份、多个指标，模型没有严格按问题中的时间和指标过滤。
- 表格或预测表进入 prompt 后，模型容易把相邻列、相邻行或不同口径数字混淆。
- prompt 旧版本允许模型进行一定解释和推算，导致事实题出现自算或扩展。

修复方向：

- 已在 prompt v2 中加入“不得自行计算、不得替换相邻指标、必须精确匹配公司/期间/指标”的约束。
- 后续需要重新跑 fact badcase 子集验证。
- 如果仍然失败，需要改 `context_formatter`：对事实型问题优先保留包含查询关键词、年份、指标词的原始片段，减少无关上下文。

### 3.2 检索命中资料但关键表格内容没有进入答案

代表样本：

- `fact_004`：国轩高科 2024A PB 估值。
- `fact_008`：麦加芯彩 2026E 归母净利润。
- `fact_045`：飞荣达 2025 主营收入。

现象：

- `reference_hit_all = true`，但生成答案说“无法确定”。
- 说明检索返回了正确文档/页码，但传给模型的可读证据可能没有覆盖到关键表格行，或者被截断。

初步原因：

- 召回粒度和生成证据粒度不完全一致。
- 当前 context 截断策略可能把表格中的关键行截掉。
- 对表格型 chunks，答案数字可能在后半段，但 prompt 只看到前部文本。

修复方向：

- 对 `has_table = true` 的 chunk，生成阶段尽量完整保留表格 chunk。
- 对事实型问题，增加 question-aware context selection：优先保留同时包含公司名、年份、指标词、数字的片段。
- 对生成前证据做简短重排：含查询关键词更多的片段排前。

### 3.3 真实检索失败

代表样本：

- `fact_047`：海达尔 2025 年研发费用。
- `fact_049`：海光信息 2024A 销售毛利率。

现象：

- `reference_hit_all = false`。
- 模型没有拿到正确资料，回答错误或无法确定。

修复方向：

- 优先检查 ground truth 的 `source/pages` 是否准确。
- 若数据集无误，进入检索侧优化：同义词扩展、公司简称匹配、BM25 权重、TopK 增大、父页扩展。

## 4. 对比型 Badcase

### 4.1 召回缺少对比双方之一

代表样本：

- `compare_002`：泸州老窖 vs 五粮液，缺少五粮液 2025 年营收。
- `compare_003`：千禾味业 vs 神农集团，缺少神农集团 26Q1 营收。
- `compare_007`：普蕊斯 vs 普瑞眼科，缺少普蕊斯和普瑞眼科关键预测营收。
- `compare_008`：昭衍新药 vs 通策医疗，缺少通策医疗关键营收。

初步原因：

- 对比型问题天然需要“两家公司 + 同一指标 + 同一期间”同时命中。
- 当前路由虽然针对 compare 做了策略调整，但仍可能只召回到其中一方。
- BM25/向量召回对公司简称、行业近义词、指标别名仍不够稳。

修复方向：

- 对 compare 类型做实体拆分：分别用公司 A 和公司 B 形成子查询，各召回一批，再合并 rerank。
- 对最终上下文做覆盖检查：如果缺少任一公司，继续放宽 TopK 或追加 BM25 召回。
- 生成 prompt 要求“如果一方缺证据，不能给出确定比较结论”。

### 4.2 资料齐全但数字或结论错位

代表样本：

- `compare_013`：中集集团 vs 中自科技。
  - 结论正确，但中自科技数字写成了 25 亿元，而标准答案是 2337 百万元。

- `compare_021`：华源控股 vs 海光信息。
  - 结论正确，但遗漏华源控股 5.85 亿元。

- `compare_029`：保利发展 vs 华发股份。
  - 结论表达混乱，前后出现矛盾，并且华发股份数字错误。

初步原因：

- 模型在对比型答案中容易为了完整表达而引入“看起来相关”的其他年份或其他指标。
- 单位转换、百万元/亿元混用时容易产生错误。
- 旧 prompt 没有强制要求“先列双方同口径数字，再给结论”。

修复方向：

- prompt v2 已要求 compare 答案先列双方原始数字和引用，再给结论。
- 尽量避免让模型做单位换算；若必须换算，要保留原始单位。
- 对比型答案格式固定为“公司 A：数字；公司 B：数字；结论：谁更高/更低”。

### 4.3 数据集自身错误

代表样本：

- `compare_028`：隆基绿能 vs 格林美。
  - 标准答案写“格林美更高”。
  - 但标准答案中的数字是隆基绿能 111.9 亿元、格林美 99.82 亿元。
  - 按数字应为隆基绿能更高。

处理方式：

- 该样本应先修复评测集，再重新导出 `financial_qa_dev.jsonl`。
- 数据集修复后，不能直接拿旧评测结果比较，需要重跑生成评测。

## 5. 汇总型 Badcase

### 5.1 覆盖不完整

代表样本：

- `summary_001`：新能源消纳与新型电力系统建设。
  - 缺失 2024—2027 年 9 项专项行动、2025—2027 年年均新增 2 亿千瓦以上新能源合理消纳利用、全国新能源利用率不低于 90%、到 2027 年新型储能装机 1.8 亿千瓦以上等关键点。

- `summary_003`：可再生能源规划和氢能规划。
  - 缺失 2025 年可再生能源消费总量 10 亿吨标准煤、年发电量 3.3 万亿千瓦时、总量消纳责任权重 33%、非水电消纳责任权重 18% 等关键数字。

初步原因：

- 汇总型问题需要多个政策文件、多页内容共同支撑，当前 TopK 和 context 预算可能不够。
- LLM 看到局部证据后会自然组织答案，但不能保证覆盖 ground truth 的所有要点。

修复方向：

- summary 类型应采用更大的召回预算和更高的文档覆盖目标。
- 根据 `source` 或主题索引做 policy-level expansion：同主题政策文件至少各保留 1 条关键证据。
- prompt 中要求“优先覆盖政策目标、任务、机制、数字，不扩展无关案例”。

### 5.2 风格扩写与原文不贴合

代表样本：

- `summary_002`：新型储能政策。
  - judge score 82，但仍判错。
  - 问题主要不是完全不会答，而是加入了太多标准答案未明确要求的扩写，且市场机制部分不够贴合。

- `summary_005`：设备更新和以旧换新。
  - 检索覆盖较好，但缺失 2027、2023、25% 等能源设备更新目标数字。

初步原因：

- 生成模型倾向把政策材料改写成更完整的说明文。
- 评测集答案更偏“忠于原文、覆盖指定要点”，因此生成答案需要更克制。

修复方向：

- prompt v2 已要求 summary “只回答问题涉及的维度，尽量使用原文表述，不自行扩展分类、案例或措施”。
- 需要重新跑 summary 子集，观察 LLM judge 的 correctness、completeness、faithfulness 是否提升。
- 如果仍不稳定，可把 summary 的上下文组织为“按政策文件分组”的格式，减少模型自行重组造成的偏移。

## 6. 当前修复计划

优先级从高到低：

1. **修复评测集明显错误**
   - 重点：`compare_028`。
   - 修复后重新生成 `financial_qa_dev.jsonl`。

2. **验证 prompt v2**
   - 先跑一小批 badcase：事实型 5 条、对比型 4 条、汇总型 3 条。
   - 观察是否减少“自行计算”“无法确定”“风格扩写”。

3. **改进 context formatter**
   - 事实型：优先保留命中公司名、年份、指标词、数字的原始片段。
   - 表格型：`has_table = true` 的 chunk 不轻易截断。
   - 对比型：保证双方公司都有证据。
   - 汇总型：按政策来源组织证据，提升多文档覆盖。

4. **追加修复后评测**
   - 先跑 badcase subset。
   - 再跑 120 条全量。
   - 在本文档追加“修复后指标”和“仍未解决问题”。

## 7. 后续记录模板

后续每次修复后，可以按下面格式追加：

```text
## yyyy-mm-dd 修复记录

### 改动

- prompt/context/retrieval/eval_set 哪些部分发生变化。

### 复测范围

- badcase subset / full 120。

### 指标变化

| metric | before | after |
|---|---:|---:|
| judge_correct_rate |  |  |
| fact_correct_rate |  |  |
| compare_correct_rate |  |  |
| summary_correct_rate |  |  |
| reference_hit_all |  |  |
| numeric_coverage |  |  |

### 仍然失败的代表样本

- question_id：
- 现象：
- 下一步：
```

## 8. 2026-05-18 Prompt v2 小批复测

### 8.1 复测范围

本次从旧评测失败样本中抽取 12 条：

- fact：`fact_002`, `fact_004`, `fact_008`, `fact_036`, `fact_043`
- compare：`compare_002`, `compare_003`, `compare_013`, `compare_029`
- summary：`summary_001`, `summary_002`, `summary_005`

相关文件：

- 小批评测集：`data/eval/badcase_prompt_v2_subset.jsonl`
- 生成结果：`data/generated/eval_runs/prompt_v2_badcase_subset_answers.jsonl`
- 评测报告：`docs/experiments/generation/prompt_v2_badcase_subset/report.md`
- 评测详情：`docs/experiments/generation/details/prompt_v2_badcase_subset/details.json`

### 8.2 指标变化

| metric | old subset | prompt v2 subset |
|---|---:|---:|
| judge_correct | 0/12 | 2/12 |
| judge_correct_rate | 0.00% | 16.67% |
| judge_avg_score | 36.75 | 38.58 |
| fact_avg_score | 17.20 | 12.40 |
| compare_avg_score | 37.25 | 44.00 |
| summary_avg_score | 68.67 | 75.00 |

按样本看：

| question_id | type | old_correct | old_score | prompt_v2_correct | prompt_v2_score | 备注 |
|---|---|---:|---:|---:|---:|---|
| `fact_002` | fact | false | 38 | false | 12 | 不再自行计算 492 倍，但改答 33x，关键 2025A P/E 仍未进入有效上下文 |
| `fact_004` | fact | false | 18 | false | 12 | 仍回答无法确定，说明 PB 数字可能没有进入 prompt 可见片段 |
| `fact_008` | fact | false | 12 | false | 25 | 稍有改善，但仍没有命中 272.43 百万元 |
| `fact_036` | fact | false | 8 | false | 5 | 仍取错为 1231 亿元，属于同文档/同页中的错误口径 |
| `fact_043` | fact | false | 10 | false | 8 | 仍判断无法确定，检索虽命中但关键公司/指标没有进入可用证据 |
| `compare_002` | compare | false | 18 | false | 32 | 表达更保守，但仍缺五粮液 405.29 亿元 |
| `compare_003` | compare | false | 18 | false | 28 | 表达更保守，但仍缺神农集团 13.22 亿元 |
| `compare_013` | compare | false | 68 | true | 88 | 结论修正为正确，但中自科技数字仍不完全匹配 |
| `compare_029` | compare | false | 45 | false | 28 | 结论更保守但未给出正确结论，华发股份数字仍错 |
| `summary_001` | summary | false | 48 | false | 56 | 风格更克制，但关键政策数字仍缺失 |
| `summary_002` | summary | false | 82 | true | 91 | 明显改善，覆盖目标、场景、技术路线、市场机制 |
| `summary_005` | summary | false | 76 | false | 78 | 略有改善，但仍缺 2027/2023/25% 等目标数字 |

### 8.3 结论

Prompt v2 对“回答风格”和“对比题格式”有帮助，尤其是：

- summary 答案更克制，`summary_002` 从错误变为正确。
- compare 答案开始按对象分别列证据，`compare_013` 从错误变为正确。
- 部分缺证据的问题不再强行下结论，而是更明确地说明缺少哪一方证据。

但 prompt v2 没有解决事实型问题，甚至在本批 fact 上平均分下降。原因不是 prompt 规则不够，而是：

- 关键表格行或关键数字没有稳定进入 prompt。
- 事实题经常在同一页/同一文档里出现多个相似口径，模型仍会选错。
- 现有上下文截断策略对表格和预测表不够友好。

### 8.4 下一步

接下来优先改 `context_formatter`，而不是继续加 prompt 规则：

1. 对 fact 类型做 question-aware 证据筛选，优先保留同时包含公司名、年份/季度、指标词、数字的片段。
2. 对 `has_table = true` 的 chunk 尽量完整保留，避免表格后半部分被截断。
3. 对 compare 类型做双方覆盖检查，缺公司 B 时追加以公司 B 为核心的召回。
4. 对 summary 类型提高政策文件覆盖率，按政策来源组织上下文。

复测顺序：

1. 先复测本 12 条小批。
2. 若 fact 明显改善，再跑完整 120 条。
3. 将修复后的指标继续追加到本文档。

## 9. 2026-05-18 上下文组织修复记录

### 9.1 问题定位

对 `prompt_v2_badcase_subset` 中 5 条事实型失败样本检查中间检索链路后，发现问题不是“PDF 没解析”，也不是简单的“完全没检索到”，而是：

- 检索阶段经常能命中正确文档和正确页码。
- 关键答案 chunk 在 `chunks_meta.jsonl` 中存在。
- 但生成阶段把 child chunk 扩展成 parent window 后，`context_formatter` 只截取父页文本前部，导致真正命中的表格行或正文句子被截断。

典型样本：

| question_id | 现象 | 判断 |
|---|---|---|
| `fact_002` | `514.94` 存在于 `EJGF.pdf` 的估值表，但目标 chunk 在混合召回中排第 46 | 父页包含答案，但前部截断导致答案不可见 |
| `fact_008` | `272.43` 存在于 `MJXC.pdf` 第 2 页预测表 | “归母净利润”和“归属母公司净利润”未做同义匹配，相关片段未抽中 |
| `fact_043` | 第一名就是 `DLGF.pdf` 中“深圳皓飞新材2026年Q1实现产品销售收入1.57亿元” | child 命中准确，但父页从第 1 页开头截断，答案在第 2 页后部被吞掉 |
| `fact_036` | 资料正文确有“截至2025年末，公司有息负债672亿元” | 不是评测集错误，而是图表、正文和相邻数字混在一起后模型选错 |

### 9.2 代码改动

本次改动不重建索引，只改变生成阶段的上下文组织：

- `src/financial_report_rag/retrieval/parent_document.py`
  - 在 `child_hits` 中保留原始命中 child chunk 的文本、类型和表格标记。

- `src/financial_report_rag/generation/context_formatter.py`
  - 每条证据先展示“命中片段”，再展示围绕 query 词抽取的“相关片段”，最后才展示父页上下文。
  - 增加 query-aware 片段抽取，优先保留公司名、年份/季度、指标词、数字附近文本。
  - 增加指标同义词扩展，例如“归母净利润”与“归属母公司净利润/归属于母公司净利润”，“PB”与“P/B/市净率”，“PE”与“P/E/市盈率”。

- `scripts/generation/generate_answers.py`
  - 调用 `format_contexts` 时传入 `query` 和 `question_type`。

### 9.3 Dry-run 验证

验证文件：

- `data/generated/dry_runs/prompt_v2_context_fix_v2_badcase_subset.jsonl`

验证结果：

| question_id | 关键证据是否进入 prompt |
|---|---|
| `fact_002` | `514.94`, `P/E`, `2025A` 均已进入 |
| `fact_004` | `2.7`, `PB`, `2024A` 均已进入 |
| `fact_008` | `272.43`, `2026E`, `归属母公司净利润` 均已进入 |
| `fact_036` | `672`, `有息负债`, `截至2025` 均已进入 |
| `fact_043` | `1.57`, `深圳皓飞新材`, `产品销售收入` 均已进入 |

这说明本次修复已经解决“关键答案存在但没有进入 prompt”的主要问题。下一步需要调用 API 重新生成 12 条 badcase，并用 LLM judge 复测实际回答是否改善。
