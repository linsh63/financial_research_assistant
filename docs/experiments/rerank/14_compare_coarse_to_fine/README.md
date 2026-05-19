# Compare 粗到细检索实验结论

本实验只验证 compare 类型问题，不修改现有 routed 主流程，也不影响 fact/summary。

## 实验设置

粗到细策略分两步：

1. 先用对比实体在全库中定位候选 PDF。
2. 再只在候选 PDF 内检索具体年份、指标和页码，并做父文档窗口扩展。

## 结果对比

| experiment | doc_locator | Recall@5 | Recall@8 | HitAny@8 | HitAll@8 | badcase |
|---|---|---:|---:|---:|---:|---|
| 11_snjt_single_pdf_repair | routed baseline | - | 96.67% | 100.00% | 93.33% | compare_007, compare_008 等 |
| 13_financial_table_query_rewrite_no_unit | query rewrite | 93.65% overall | 95.00% compare | 96.67% | 93.33% | compare_007, compare_008 |
| 14_compare_coarse_to_fine | 每实体 top2 PDF | 96.67% | 98.33% | 100.00% | 96.67% | compare_004 |
| 14_compare_coarse_to_fine_doc_top1 | 每实体 top1 PDF | 98.33% | 98.33% | 100.00% | 96.67% | compare_021 |
| 14_compare_coarse_to_fine_adaptive | top2 + 分数比自适应过滤 | 100.00% | 100.00% | 100.00% | 100.00% | 无 |

## 关键观察

- `compare_007` 和 `compare_008` 的正确表格 chunk 本来就存在，失败原因主要是表格 chunk 没有公司中文名，直接 chunk 级召回容易找错页。
- 粗到细策略能绕过这个问题：先用标题页/正文中的实体把 PDF 定位出来，再在 PDF 内找 `2026E`、`营收`、`营业收入`、`主营业务收入` 等字段。
- 每实体 top2 PDF 会保留同业提及文档，可能引入噪声，例如 `compare_004` 中山西汾酒被泸州老窖挤掉。
- 每实体 top1 PDF 又可能错过缩写文档，例如 `compare_021` 中海光信息被半导体行业综述文档挤掉。
- 自适应规则较稳：当 top1 明显高于 top2 时只保留 top1，否则保留 top2。当前阈值为 `top1_score / top2_score >= 3`。

## 后续建议

下一步可以把该策略作为 compare 的一个可选候选生成器接入 routed 检索，但不要直接替换全部 compare 流程。更稳的做法是：

- 只在 compare 题启用。
- 只把粗到细结果作为 candidate supplement。
- 之后仍交给 reranker 和 parent fill 做最终排序。
- 保留现有 query rewrite、entity prefer、parent fill 作为回退链路。
