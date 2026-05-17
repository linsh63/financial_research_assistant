# 第一周切块实验

## 数据概况

- 输入文件：`data/processed/pages/pages_deepdoc.jsonl`
- 文档数：150
- 页面数：1092
- 解析出的表格数：1014
- 表格来源：pdfplumber_structured: 869，pymupdf_layout_table: 145
- 行业页面分布：consumer: 4，医疗: 131，半导体: 153，房地产: 108，政策: 476，新能源: 125，消费: 95

## 参数对比

| chunk size | overlap | chunk 数 | 平均长度 | 中位长度 | 最大长度 | 表格 chunk | 拆分表格 chunk | 表格保护缺失 | Recall@5 | HitAll@5 | 输出 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 256 | 50 | 10468 | 179.6 | 216.0 | 6954 | 5131 | 4430 | 0 | 77.53% | 67.50% | `data/processed/chunks/chunking_experiment/chunks_256_50.jsonl` |
| 512 | 100 | 6826 | 243.5 | 173.5 | 6954 | 2724 | 1973 | 0 | **78.25%** | **69.17%** | `data/processed/chunks/chunking_experiment/chunks_512_100.jsonl` |
| 1024 | 200 | 5125 | 303.6 | 77 | 6954 | 1594 | 724 | 0 | 76.92% | 67.50% | `data/processed/chunks/chunking_experiment/chunks_1024_200.jsonl` |

## 召回评测设置

- 评测集：`data/eval/financial_qa_dev.jsonl`，共 120 条。
- 评测口径：page-level，召回 chunk 的文档和页码都要命中 ground truth。
- 检索方式：vector-only，FAISS Flat，`bge-large-zh-v1.5`。
- 评测指标：只取指导文档要求的 `Recall@5`，同时补充 `HitAll@5` 观察多证据问题是否完整命中。
- 512/100 与正式索引使用的 `data/processed/chunks/chunks_boundary.jsonl` 内容一致，因此复用 `data/processed/indexes/bge_large_zh_v15`。
- 256/50 与 1024/200 补建临时索引：
  - `data/processed/indexes/chunking_experiment/bge_large_zh_v15_256_50`
  - `data/processed/indexes/chunking_experiment/bge_large_zh_v15_1024_200`

## 备注

- 表格 chunk 使用 `row_boundary` 保护策略，允许按行分成多个 chunk，但不切断单个表格行。
- 三组配置的表格保护缺失均为 0，说明当前切块器能够保证“表格行不被切断”。
- 512/100 在 Recall@5 和 HitAll@5 上都是当前最好结果，因此继续作为默认切块参数。
- 256/50 产生了更多 chunk，但 Recall@5 没有提高，说明过小 chunk 会增加索引规模和编码成本，却没有带来明显召回收益。
- 1024/200 chunk 更少，但 Recall@5 略低，后续若配合 rerank 可以再观察它是否有生成阶段优势。
