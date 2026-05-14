# 第一周切块实验

## 数据概况

- 输入文件：`data/processed/pages_deepdoc.jsonl`
- 文档数：150
- 页面数：1092
- 解析出的表格数：1014
- 表格来源：pdfplumber_structured: 869，pymupdf_layout_table: 145
- 行业页面分布：医疗: 131，半导体: 153，房地产: 108，政策: 476，新能源: 125，消费: 99

## 参数对比

| chunk size | overlap | chunk 数 | 平均长度 | 中位长度 | 最大长度 | 表格 chunk | 拆分表格 chunk | 表格保护缺失 | Recall@5 | 输出 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 256 | 50 | 10620 | 186.9 | 221.0 | 6954 | 5131 | 4430 | 0 | 待召回评测 | `data/processed/chunking_experiment/chunks_256_50.jsonl` |
| 512 | 100 | 6885 | 252.2 | 206 | 6954 | 2724 | 1973 | 0 | 待召回评测 | `data/processed/chunking_experiment/chunks_512_100.jsonl` |
| 1024 | 200 | 5124 | 307.9 | 79.0 | 6954 | 1594 | 724 | 0 | 待召回评测 | `data/processed/chunking_experiment/chunks_1024_200.jsonl` |

## 备注

- 本阶段只做切块对比，不提前伪造 Recall@5；召回指标需要等 FAISS + FlagEmbedding 索引和评测集接入后再补。
- 表格 chunk 使用 `row_boundary` 保护策略，允许按行分成多个 chunk，但不切断单个表格行。
