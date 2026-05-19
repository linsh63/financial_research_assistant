# Compare 粗到细检索实验

- 评测时间：2026-05-19T10:31:04
- 评测集：`data/eval/financial_qa_dev.jsonl`
- compare 样本数：30 / 120
- 原始跳过样本：0
- 匹配粒度：`page`
- compare rewrite：`data/processed/query_rewrites/compare_financial_table_no_unit_rule.jsonl`
- 文档定位数量：每个实体 top2
- 页内检索数量：每个实体 top12，交错保留 top4
- 父文档窗口：前后各 1 页
- 总耗时（秒）：3.88

## 指标

| scheme | Recall@5 | Recall@8 | HitAny@5 | HitAny@8 | HitAll@5 | HitAll@8 |
|---|---:|---:|---:|---:|---:|---:|
| coarse_to_fine | 96.67% | 98.33% | 100.00% | 100.00% | 93.33% | 96.67% |

## 说明

- 本实验不修改主 routed 检索链路，只验证 compare 题的候选生成思路。
- 第一阶段用公司实体在全库中定位 PDF；第二阶段只在对应 PDF 内检索年份和财务字段所在页。
- 该实验暂未接入向量召回和 cross-encoder rerank，主要用于判断“先文档、后页码”的方向是否值得并入正式流程。

## Badcases

### coarse_to_fine @ 8

- `compare_004` compare coverage=1/2
  query: 山西汾酒 vs TCL 智家，哪家公司的26Q1营收 更高
  top_sources: ['data/raw/consumer/LZLJ.pdf', 'data/raw/consumer/TCL.pdf']
