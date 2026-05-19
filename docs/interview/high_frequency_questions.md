# 面试高频追问

本文档用于准备围绕本项目的 RAG 面试追问。回答时尽量带具体实验数字，不只讲概念。

## 1. 这个项目和普通 LangChain Demo 的区别是什么？

普通 Demo 往往只处理纯文本，直接 split 后接向量库。本项目处理的是金融研报和政策 PDF，难点在多栏排版、表格连续、页码证据定位和跨文档汇总。

项目自己实现了：

- PDF 解析和表格保护切块。
- FAISS Dense + BM25 混合召回。
- Cross-Encoder rerank。
- 按 fact / compare / summary 路由检索。
- 120 条自建评测集、规则评测、LLM Judge 和 badcase 闭环。

## 2. 为什么选择金融研报和政策文档？

金融 PDF 比普通网页文本更接近真实复杂文档：

- 多栏排版会打乱阅读顺序。
- 表格多，指标和数值可能跨行、跨列。
- 问题经常要求精确数字和页码证据。
- 对比题需要同时命中两家公司。
- 汇总题需要跨多个政策文件归纳。

这些问题能体现 RAG 系统的工程深度。

## 3. chunk size 怎么选？

做过 256 / 512 / 1024 三组切块实验：

| chunk_size | overlap | Recall@5 | HitAll@5 | 结论 |
|---:|---:|---:|---:|---|
| 256 | 50 | 77.53% | 67.50% | 太碎，表格和上下文更容易分散。 |
| 512 | 100 | 78.25% | 69.17% | 当前默认，召回和上下文平衡最好。 |
| 1024 | 200 | 76.92% | 67.50% | 太长，局部匹配变弱。 |

所以默认使用 `512/100`。

## 4. 表格保护切块解决了什么？

金融表格里经常出现：

```text
2026E / 营收 / 百万元 / 3136
```

如果普通按长度切块，表头、指标名和数值可能被切开，导致召回命中了页面但生成无法读出数字。本项目把表格作为特殊块处理，尽量保证表格行不被切断，并在 metadata 里保留 `has_table`。

## 5. 为什么不只用向量检索？

纯向量检索对语义相近问题有效，但金融问题里有大量关键词、简称、数字和指标口径。BM25 对精确词更敏感。

实验结果：

| scheme | Recall@5 | HitAll@5 |
|---|---:|---:|
| vector | 78.25% | 69.17% |
| bm25 | 70.49% | 58.33% |
| hybrid 0.6/0.4 | 81.54% | 71.67% |

因此使用 `Dense 0.6 + BM25 0.4`。

## 6. FAISS Flat、IVF、HNSW 为什么选 Flat？

当前只有 6826 个 chunk，Flat 的延迟很低，而且召回最高。

| index_type | Recall@10 | HitAll@10 |
|---|---:|---:|
| Flat | 84.03% | 75.83% |
| IVF | 76.94% | 67.50% |
| HNSW | 71.53% | 61.67% |

所以当前阶段优先选 Flat。数据量上来后，可以再调 IVF/HNSW 或接 Milvus。

## 7. Reranker 有多大提升？

向量 Top20 后 rerank Top5 相比直接向量 Top5 有提升：

| scheme | Recall@5 | HitAll@5 |
|---|---:|---:|
| vector_top5 | 78.25% | 69.17% |
| vector_top20_rerank_top5 | 82.29% | 74.17% |

但 rerank 不是所有场景都能直接提升，所以最终不是全局套一个 rerank，而是按问题类型路由。

## 8. 为什么要按问题类型路由？

不同题型需要的候选证据不同：

- fact：只要精确数字，候选太多会干扰生成。
- compare：需要同时保障两个实体的证据。
- summary：需要跨多个来源覆盖，必须扩大候选池并做来源多样性。

最终策略：

| question_type | strategy |
|---|---|
| fact | hybrid Top5 + parent window |
| compare | query rewrite + entity slots + rerank + parent fill |
| summary | hybrid Top50 + source diverse Top8 |

当前 routed_v17 的整体结果：

| Recall@5 | Recall@8 | HitAll@8 |
|---:|---:|---:|
| 94.90% | 96.35% | 94.17% |

## 9. compare 类型为什么要单独优化？

对比题经常问：

```text
A vs B，哪家公司 2025 年营收更高？
```

如果只用原问题召回，系统可能只命中 A 或只命中 B。项目引入了：

- query rewrite：拆成 A 的指标查询和 B 的指标查询。
- raw entity slots：给每个实体保留候选槽位。
- coarse-to-fine：先定位文档，再定位具体页码。
- parent fill：避免 rerank 后只剩一个实体。

最终 compare 检索侧达到 `Recall@8=100%`、`HitAll@8=100%`。

## 10. summary 类型为什么最难？

summary 题要求跨多个政策文件覆盖多个方面。难点是：

- 标准答案可能来自 3 到 5 个文件。
- 单个 query 很容易只召回主题最强的前几个文件。
- 生成时还要控制不要扩展资料外内容。

当前 summary 的 `HitAll@8=75.00%`，生成 judge correct rate 为 `50.00%`。这是后续最值得继续优化的模块。

## 11. 如何缓解幻觉？

项目做了三层约束：

1. 检索侧保留 source、pages、chunk_id。
2. Prompt 明确要求只依据资料回答，并用 `[资料X]` 标注依据。
3. 评测侧检查引用命中、数字覆盖，并用 LLM Judge 判断 correctness / completeness / faithfulness。

当前生成结果：

| metric | value |
|---|---:|
| answer_rate | 100.00% |
| citation_rate | 97.50% |
| reference_hit_all | 93.33% |
| judge_correct_rate | 80.00% |

## 12. 空召回或证据不足怎么处理？

当前策略是：

- fact：优先精准回答，证据不足时拒答。
- compare：如果一方缺失，明确说明缺失哪一方的哪个指标。
- summary：只覆盖检索资料中出现的方向，不自行补充政策背景。

后续可以加入低置信度阈值和拒答模板，但现阶段更关注检索证据覆盖。

## 13. 父子文档机制是什么？

child chunk 负责精确召回，parent page 负责给 LLM 更完整上下文。命中 child 后，系统把对应页和邻页上下文带给生成模型。

这个机制对财务表格和长段落有帮助，因为命中的短片段可能没有完整表头、单位或上下文。

## 14. 为什么引入 LLM Judge？

规则评测能检查引用和数字，但不能充分判断回答是否等价、是否完整。LLM Judge 用 ground truth、生成答案和证据进行对比，输出：

- `is_correct`
- `score`
- `correctness`
- `completeness`
- `faithfulness`
- reason

最终可以得到回答正确率，并辅助 badcase 分类。

## 15. 项目最大的 badcase 是什么？

当前主要有三类：

1. 检索没命中：例如极少数 fact 文档或页码没有进入 TopK。
2. 证据命中但生成拒答：模型看到直接数字却判断“无法确定”。
3. summary 覆盖不足：跨政策文件的关键方向或数字没有全部进入上下文。

对应文档：

- `docs/experiments/rerank/badcase_analysis.md`
- `docs/experiments/generation/badcase_analysis/report.md`

## 16. 如果数据量扩大 10 倍怎么办？

可以按顺序做：

- 把 FAISS Flat 切换为 IVF/HNSW 并重新调参。
- 接入 Milvus，做服务化向量库。
- 对 BM25 和 Dense 候选做分片或缓存。
- rerank 只处理 TopN，控制 Cross-Encoder 延迟。
- 对高频 query 和热门文档做缓存。

## 17. 系统瓶颈在哪里？

本地检索阶段主要瓶颈：

- embedding 模型加载。
- reranker 推理。

线上生成阶段主要瓶颈：

- LLM API 延迟和网络稳定性。
- summary 题上下文长，生成耗时更高。

Demo 支持 dry-run，就是为了在 API 不稳定时也能展示检索链路。

## 18. 下一步怎么改进？

优先级从高到低：

1. summary 多文档覆盖和答案组织。
2. 表格字段结构化抽取，减少“证据命中但读错数”。
3. 引入低置信度拒答和引用校验。
4. 接入 Milvus 或服务化检索。
5. 做端到端延迟统计和缓存策略。
