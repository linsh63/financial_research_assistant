# Compare 粗到细检索实验

- 评测时间：2026-05-19T10:32:57
- 评测集：`data/eval/financial_qa_dev.jsonl`
- compare 样本数：30 / 120
- 原始跳过样本：0
- 匹配粒度：`page`
- compare rewrite：`data/processed/query_rewrites/compare_financial_table_no_unit_rule.jsonl`
- 文档定位数量：每个实体 top2
- 自适应文档阈值：3.0
- 页内检索数量：每个实体 top12，交错保留 top4
- 父文档窗口：前后各 1 页
- 总耗时（秒）：3.71

## 指标

| scheme | Recall@5 | Recall@8 | HitAny@5 | HitAny@8 | HitAll@5 | HitAll@8 |
|---|---:|---:|---:|---:|---:|---:|
| coarse_to_fine | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |

## 说明

- 本实验不修改主 routed 检索链路，只验证 compare 题的候选生成思路。
- 第一阶段用公司实体在全库中定位 PDF；第二阶段只在对应 PDF 内检索年份和财务字段所在页。
- 该实验暂未接入向量召回和 cross-encoder rerank，主要用于判断“先文档、后页码”的方向是否值得并入正式流程。
- 自适应规则：每个实体先取 top2 文档；若 top1/top2 分数比 >= 3.0，则只保留 top1，避免同业提及文档挤占页内检索结果。
- 本次 compare 子集 30 条在 page-level Recall@5/8 与 HitAll@5/8 均达到 100%，说明“先定位文档，再定位页码”的方向值得进入下一轮正式接入实验。

## Badcases

### coarse_to_fine @ 8

No badcases.
