# 第一周向量索引构建 baseline

## 实验目标

根据 `docs/project_guide_project2.md` 第一周第 3 步，完成以下内容：

- 使用 `BAAI/bge-large-zh-v1.5` 编码 chunk。
- 使用 FAISS 构建三类索引：`Flat`、`IVF`、`HNSW`。
- 输出索引构建脚本、向量维度、文档记录。

说明：指导文档推荐 `FlagEmbedding`。本地 Mac 环境中 `FlagEmbedding.encode` 会异常退出，因此本次 baseline 使用 `sentence-transformers` 后端加载同一个本地 BGE 模型；脚本仍保留 `--backend flagembedding`，后续在服务器上可以切回 FlagEmbedding。

## 当前实现

代码入口：

```bash
scripts/build_faiss_index.py
scripts/retrieval/build_faiss_index.py
scripts/retrieval/build_faiss_indexes_from_embeddings.py
scripts/search_faiss.py
src/financial_report_rag/retrieval/embeddings.py
src/financial_report_rag/retrieval/vector_store.py
```

设计方式：

- chunk 文本只做一次 embedding，保存为 `embeddings.npy`。
- 三种 FAISS 索引共用同一份 embedding。
- 与向量顺序一致的 chunk 记录保存为 `chunks_meta.jsonl`。
- 构建信息保存为 `index_manifest.json`，记录模型、后端、维度、chunk 数、索引参数和构建耗时。
- 本地使用两阶段构建：父进程负责 BGE 编码，子进程只负责 FAISS 建索引，避免 Mac 上 Torch 与 FAISS IVF 在同一进程中冲突。

## 本次运行命令

```bash
cd /Users/linsh/Documents/Recommendation/project/ProjectSet/financial_research_assistant

.venv-brew/bin/python scripts/build_faiss_index.py \
  --chunks data/processed/chunks/chunks_deepdoc_sample.jsonl \
  --output-dir data/processed/indexes/bge_large_zh_v15_sample \
  --model models/bge-large-zh-v1.5 \
  --backend sentence-transformers \
  --index-types flat ivf hnsw \
  --batch-size 4 \
  --force-embeddings
```

## 小样本 smoke 结果

| 项目 | 结果 |
|---|---|
| 输入 chunk 文件 | `data/processed/chunks/chunks_deepdoc_sample.jsonl` |
| chunk 数 | 47 |
| embedding 模型 | `models/bge-large-zh-v1.5` |
| embedding 后端 | `sentence-transformers` |
| 向量维度 | 1024 |
| embedding 输出 | `data/processed/indexes/bge_large_zh_v15_sample/embeddings.npy` |
| 文档记录输出 | `data/processed/indexes/bge_large_zh_v15_sample/chunks_meta.jsonl` |
| manifest 输出 | `data/processed/indexes/bge_large_zh_v15_sample/index_manifest.json` |
| 本地运行状态 | 已跑通 |

小样本索引构建记录：

| 索引类型 | 向量数 | 维度 | 参数 | 构建时间(s) | 文件大小(MB) |
|---|---:|---:|---|---:|---:|
| Flat | 47 | 1024 | `metric=ip` | 0.0136 | 0.1836 |
| IVF | 47 | 1024 | `nlist=1, nprobe=1`，样本少所以从请求的 64 自动下调 | 0.0016 | 0.1880 |
| HNSW | 47 | 1024 | `m=32, ef_construction=200, ef_search=64` | 0.0002 | 0.1958 |

## 检索验证

查询：

```text
比亚迪海外销量为什么保持高增长？
```

Flat Top5 结果摘要：

| rank | score | chunk_id | 说明 |
|---:|---:|---|---|
| 1 | 0.5971 | `byd_202601-p001-s006-c001` | 相关报告列表 |
| 2 | 0.5606 | `byd_202601-p001-s001-c001` | 标题命中“海外销量保持高增” |
| 3 | 0.5534 | `byd_202601-p001-s002-c002` | 正文解释海外销量高增、全球化战略和区域布局 |
| 4 | 0.5197 | `byd_202601-p001-s002-c003` | 闪充和产品矩阵升级、投资建议 |
| 5 | 0.4333 | `byd_202601-p001-s002-c001` | 一季度业绩和销量背景 |

IVF 和 HNSW 的 Top3 与 Flat 一致，说明三类索引在 sample 上均可用。

验证命令：

```bash
.venv-brew/bin/python scripts/search_faiss.py \
  --index-dir data/processed/indexes/bge_large_zh_v15_sample \
  --index-type flat \
  --query "比亚迪海外销量为什么保持高增长？" \
  --top-k 5 \
  --batch-size 1
```

## 完整索引构建结果

第二周正式评测使用完整 chunk 文件：

```text
data/processed/chunks/chunks_boundary.jsonl
```

完整索引输出目录：

```text
data/processed/indexes/bge_large_zh_v15
```

| 项目 | 结果 |
|---|---|
| chunk 数 | 6826 |
| embedding 模型 | `models/bge-large-zh-v1.5` |
| embedding 后端 | `sentence-transformers` |
| 向量维度 | 1024 |
| embedding 耗时 | 441.582s |
| embedding 输出 | `data/processed/indexes/bge_large_zh_v15/embeddings.npy` |
| 文档记录输出 | `data/processed/indexes/bge_large_zh_v15/chunks_meta.jsonl` |
| manifest 输出 | `data/processed/indexes/bge_large_zh_v15/index_manifest.json` |

完整索引构建记录：

| 索引类型 | 向量数 | 维度 | 参数 | 构建时间(s) | 文件大小(MB) |
|---|---:|---:|---|---:|---:|
| Flat | 6826 | 1024 | `metric=ip` | 0.0406 | 26.6641 |
| IVF | 6826 | 1024 | `nlist=64, nprobe=8` | 0.0293 | 26.9668 |
| HNSW | 6826 | 1024 | `m=32, ef_construction=200, ef_search=64` | 0.1774 | 28.4328 |

## 第二周 FAISS 索引对比

评测设置：

- 评测集：`data/eval/financial_qa_dev.jsonl`，共 120 条。
- 评测口径：page-level，召回 chunk 的文档和页码都要命中 ground truth。
- 检索方式：vector-only。
- 指标：`Recall@10`、`HitAll@10`、FAISS search 延迟。
- 延迟统计只包含 FAISS search，不包含 query embedding；120 条 query 编码总耗时为 2.8450s。
- 文件大小作为当前规模下的索引内存占用近似。

| 索引类型 | Recall@10 | HitAll@10 | 平均查询延迟(ms) | P50(ms) | P95(ms) | 构建时间(s) | 文件大小/近似内存(MB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Flat | **84.03%** | **75.83%** | 0.3896 | 0.3885 | 0.4033 | 0.0406 | 26.6641 |
| IVF | 76.94% | 67.50% | 0.0735 | 0.0735 | 0.1034 | 0.0293 | 26.9668 |
| HNSW | 71.53% | 61.67% | **0.0572** | **0.0542** | **0.0845** | 0.1774 | 28.4328 |

逐样本详情：

```text
docs/experiments/vector_index/faiss_index_comparison.details.json
```

结论：

- 当前数据规模只有 6826 个 chunk，Flat 的延迟已经低于 0.5ms，且 Recall@10 最高，因此正式 baseline 继续使用 Flat。
- IVF 和 HNSW 查询更快，但在当前参数下 Recall@10 分别下降到 76.94% 和 71.53%，不适合作为当前默认索引。
- 当数据量扩大到几十万或百万级 chunk 后，再重新调 IVF 的 `nlist/nprobe` 或 HNSW 的 `ef_search`，届时速度收益会更有意义。

## 注意事项

- 当前 sample 只有 47 个 chunk，IVF 的 `nlist` 会自动调成 1；这不是最终实验参数，只是为了小样本 baseline 不失败。
- 完整评测已经使用 `data/processed/chunks/chunks_boundary.jsonl` 跑通，Flat / IVF / HNSW 对比见上表。

服务器上如果使用 GPU 或 Linux 环境，可以尝试：

```bash
python scripts/build_faiss_index.py \
  --chunks data/processed/chunks/chunks_deepdoc_sample.jsonl \
  --output-dir data/processed/indexes/bge_large_zh_v15_sample \
  --model models/bge-large-zh-v1.5 \
  --backend flagembedding \
  --index-types flat ivf hnsw \
  --batch-size 16 \
  --use-fp16 \
  --force-embeddings
```
