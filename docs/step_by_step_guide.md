# 金融研报助手逐步实践指南

本文档是项目执行手册，配合 `docs/todo.md` 使用：

- `todo.md` 负责记录“要做什么”。
- 本文档负责指导“怎么学、怎么做、执行哪些命令、每个阶段怎么验收”。

项目主线：先读优秀开源项目的关键设计，再自己实现一条可评测的金融研报 RAG 链路。

```text
数据收集 -> PDF 解析 -> 切块 -> 索引 -> 多路召回 -> 重排 -> 生成 -> 引用 -> 评测 -> badcase 复盘 -> Demo
```

## 0. 数据收集阶段

目标：先把项目语料准备好，再进入代码开发。这个项目的数据质量很重要，后续所有解析、切块、召回、评测和 badcase 都依赖这批 PDF。

### 0.1 数据收集目标

先分两批收集：

- 第一批开发数据：3-5 份 PDF，用来验证 PDF 解析、页码、表格和引用链路。
- 第二批实验数据：10-20 份 PDF，用来跑通 baseline 和初版评测。
- 完整项目数据：200-300 份 PDF，用来做正式实验和简历展示。

建议覆盖 3 个行业：

- 新能源：车企、动力电池、光伏、储能。
- 半导体：设备、材料、芯片设计、先进封装。
- 消费：食品饮料、医美、家电、零售。

文档类型建议混合：

- 券商行业研报。
- 公司年报、季报、公告。
- 政策文件。
- 行业白皮书或研究报告。

### 0.2 推荐数据来源

优先使用公开、可追溯的数据源：

- 巨潮资讯网：上市公司年报、季报、公告。
- 东方财富 / Choice：公司报告和行业研报。
- 发改委、工信部、人民银行、证监会等官网：政策文件。
- 卷心菜研究、墨宝研报等公开研报站点：行业报告。
- GitHub / Hugging Face：FinanceIQ、FinQA 等评测数据参考。

收集时保留来源链接。后续写项目文档时，不要只说“下载了一批 PDF”，而要能说清楚：

> 语料库包含金融研报、上市公司公告和政策文件，覆盖新能源、半导体、消费三个行业，文档以 PDF 为主，包含多栏排版、表格、图表和超过 80 页的长文档。

### 0.3 建立数据目录

```bash
cd /Users/linsh/Documents/Recommendation/project/ProjectSet/financial_research_assistant
mkdir -p data/raw data/processed docs/data_collection
```

建议按行业建立子目录：

```bash
mkdir -p data/raw/new_energy data/raw/semiconductor data/raw/consumer
```

目录示例：

```text
data/raw/
  new_energy/
    byd_2024_q3_report.pdf
    catl_2024_annual_report.pdf
  semiconductor/
    semiconductor_equipment_2025_industry_report.pdf
  consumer/
    baijiu_industry_2024_report.pdf
```

### 0.4 文件命名规范

建议使用英文小写、下划线分隔，避免中文路径和空格影响脚本处理：

```text
公司或主题_年份_报告类型.pdf
```

示例：

```text
byd_2024_q3_report.pdf
catl_2024_annual_report.pdf
semiconductor_equipment_2025_industry_report.pdf
new_energy_vehicle_2025_policy.pdf
```

如果原始文件名很长，可以保留原始文件名到数据清单里。

### 0.5 记录数据清单

创建数据清单文件：

```bash
touch docs/data_collection/pdf_manifest.csv
```

建议字段：

```csv
doc_id,file_path,title,industry,doc_type,year,source_url,notes
```

示例：

```csv
byd_2024_q3_report,data/raw/new_energy/byd_2024_q3_report.pdf,比亚迪2024年三季度报告,新能源,公司季报,2024,https://example.com,用于事实型问题
```

每下载一份 PDF，就补一行。这个习惯会让后续评测、引用和项目讲解省很多力气。

### 0.6 初步质量检查

如果想先复现当前种子数据集，可以直接运行：

```bash
scripts/download_seed_dataset.sh
```

先确认 PDF 数量：

```bash
find data/raw -name "*.pdf" | wc -l
```

检查文件大小，排除空文件：

```bash
find data/raw -name "*.pdf" -size -50k -print
```

随机查看文件名：

```bash
find data/raw -name "*.pdf" | head -n 20
```

阶段性验收：

- [x] 第一批至少收集 3-5 份 PDF。
- [ ] 每份 PDF 都在 `docs/data_collection/pdf_manifest.csv` 中有记录。
- [ ] 文件名不包含空格，尽量不包含中文。
- [ ] 每份 PDF 都能打开，不是空文件或下载失败页面。
- [ ] 至少包含 1 份带表格的 PDF 和 1 份长 PDF。

## 1. 环境准备

### 1.1 进入项目目录

```bash
cd /Users/linsh/Documents/Recommendation/project/ProjectSet/financial_research_assistant
```

### 1.2 创建 Python 虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

如果后续运行脚本时找不到 `financial_report_rag` 包，可以先设置：

```bash
export PYTHONPATH="$PWD/src:$PYTHONPATH"
```

### 1.3 约定数据和产物位置

```text
data/raw/                 原始 PDF，不提交 Git
data/processed/           解析后的 JSONL、评测集、中间结果，不提交 Git
indexes/                  FAISS / BM25 索引，不提交 Git
outputs/                  实验表、临时输出，不提交 Git
docs/                     文档、报告、badcase、面试材料
src/financial_report_rag/ 核心代码
scripts/                  可执行脚本
```

### 1.4 每次开始开发前检查状态

```bash
git status
git pull
```

如果你还没有提交当前文档：

```bash
git add docs/todo.md docs/project_guide_project2.md docs/step_by_step_guide.md
git commit -m "Add project planning docs"
git push
```

## 2. 开源项目学习路线

学习目标不是复制代码，而是带着问题读：它们怎么处理 PDF、怎么切块、怎么召回、怎么 rerank、怎么评测。

建议把参考项目放在本项目外部，避免把大仓库误提交：

```bash
mkdir -p ~/Documents/rag_open_source_refs
cd ~/Documents/rag_open_source_refs
```

### 2.1 RAGFlow：重点学习 PDF 解析和切块

仓库：<https://github.com/infiniflow/ragflow>

```bash
git clone --depth 1 https://github.com/infiniflow/ragflow.git
cd ragflow
rg -n "DeepDoc|pdf|table|chunk|parser|layout|retrieval|rerank" .
```

重点看：

- PDF 解析如何保留版面信息。
- 多栏、页眉页脚、表格、图表如何处理。
- 切块时如何避免把表格和标题上下文切散。
- 检索融合和评测链路如何组织。

阶段性实践：

- [ ] 在 `docs/notes_ragflow.md` 记录 5 条你能借鉴的设计。
- [ ] 把其中 1-2 条转化成本项目的实现要求，例如“chunk 必须保留页码”和“表格 chunk 单独标记”。

### 2.2 Langchain-Chatchat：重点学习中文 RAG 工程链路

仓库：<https://github.com/chatchat-space/Langchain-Chatchat>

```bash
cd ~/Documents/rag_open_source_refs
git clone --depth 1 https://github.com/chatchat-space/Langchain-Chatchat.git
cd Langchain-Chatchat
rg -n "FAISS|Milvus|BM25|retriever|embedding|rerank|knowledge|split" .
```

重点看：

- 中文文档如何切分。
- 向量库和检索器如何封装。
- FAISS / Milvus / BM25 等组件如何被组织成可替换模块。

阶段性实践：

- [ ] 在 `docs/notes_langchain_chatchat.md` 记录它的检索模块设计。
- [ ] 明确本项目的 `retriever` 接口：输入 query，输出带分数、文档名、页码的 chunks。

### 2.3 QAnything：重点学习两阶段召回和 rerank

仓库：<https://github.com/netease-youdao/QAnything>

```bash
cd ~/Documents/rag_open_source_refs
git clone --depth 1 https://github.com/netease-youdao/QAnything.git
cd QAnything
rg -n "rerank|retrieval|threshold|parent|child|score|top" .
```

重点看：

- embedding 粗召回后如何做 rerank。
- TopK、阈值、父子文档召回策略如何影响结果。
- 如何处理低置信度结果。

阶段性实践：

- [ ] 在 `docs/notes_qanything.md` 记录两阶段召回的设计。
- [ ] 为本项目设计 `Top20 -> rerank -> Top5` 的实验方案。

## 3. 阶段 1：PDF 解析与最小数据闭环

目标：让项目能读 PDF，输出结构化 JSONL。

### 3.1 确认测试 PDF 已就绪

先不要追求 200-300 份。使用数据收集阶段准备的第一批 3-5 份 PDF，便于 debug。

```bash
cd /Users/linsh/Documents/Recommendation/project/ProjectSet/financial_research_assistant
mkdir -p data/raw data/processed
```

把 PDF 手动放入：

```text
data/raw/
```

建议文件名包含公司、行业、年份，例如：

```text
data/raw/byd_2024_q3_report.pdf
data/raw/semiconductor_industry_2025_policy.pdf
```

### 3.2 新增解析模块

建议新增文件：

```text
src/financial_report_rag/pdf_parser.py
scripts/parse_pdfs.py
```

解析输出建议为 `data/processed/pages.jsonl`，每行一个页面：

```json
{
  "doc_id": "byd_2024_q3_report",
  "source": "data/raw/byd_2024_q3_report.pdf",
  "page": 3,
  "text": "页面文本...",
  "tables": [],
  "metadata": {
    "title": "比亚迪 2024 Q3 研报",
    "industry": "新能源"
  }
}
```

完成后运行：

```bash
python scripts/parse_pdfs.py \
  --input data/raw \
  --output data/processed/pages.jsonl
```

### 3.3 验证解析质量

```bash
wc -l data/processed/pages.jsonl
python -m json.tool < data/processed/pages.jsonl | head -n 60
```

如果 `python -m json.tool` 不适合 JSONL，就用：

```bash
python - <<'PY'
import json
from pathlib import Path

path = Path("data/processed/pages.jsonl")
for i, line in enumerate(path.open()):
    print(json.dumps(json.loads(line), ensure_ascii=False, indent=2)[:1200])
    if i >= 2:
        break
PY
```

阶段性验收：

- [ ] 能解析至少 3 份 PDF。
- [ ] 每页文本能保留 `doc_id`、`source`、`page`。
- [ ] 页眉、页脚、空白行没有明显污染检索。
- [ ] 记录 2-3 个 PDF 解析问题到 `docs/badcases.md`。

## 4. 阶段 2：切块与表格保护

目标：把页面级文本变成可检索 chunks，并保留来源。

### 4.1 新增切块模块

建议新增文件：

```text
src/financial_report_rag/chunker.py
scripts/build_chunks.py
```

chunk 输出建议为 `data/processed/chunks.jsonl`：

```json
{
  "chunk_id": "byd_2024_q3_report-p003-c002",
  "doc_id": "byd_2024_q3_report",
  "source": "data/raw/byd_2024_q3_report.pdf",
  "pages": [3],
  "text": "chunk 文本...",
  "chunk_type": "text",
  "has_table": false
}
```

完成后运行：

```bash
python scripts/build_chunks.py \
  --input data/processed/pages.jsonl \
  --output data/processed/chunks.jsonl \
  --chunk-size 512 \
  --overlap 100
```

### 4.2 跑三组切块实验

```bash
python scripts/build_chunks.py --input data/processed/pages.jsonl --output data/processed/chunks_256.jsonl --chunk-size 256 --overlap 50
python scripts/build_chunks.py --input data/processed/pages.jsonl --output data/processed/chunks_512.jsonl --chunk-size 512 --overlap 100
python scripts/build_chunks.py --input data/processed/pages.jsonl --output data/processed/chunks_1024.jsonl --chunk-size 1024 --overlap 200
```

统计每组 chunk 数量：

```bash
wc -l data/processed/chunks_*.jsonl
```

阶段性实践：

- [ ] 在 `docs/experiments_chunking.md` 建立切块实验表。
- [ ] 手动检查每组各 5 个 chunk，看是否切断表格、标题和数字上下文。
- [ ] 选择默认切块参数，先写入 `configs/rag.yaml`。

阶段性验收：

- [ ] 三组切块文件都能生成。
- [ ] 每个 chunk 都能追溯来源 PDF 和页码。
- [ ] 表格相关 chunk 有标记或保护策略。

## 5. 阶段 3：FAISS 向量检索 Baseline

目标：先跑通最小检索，不急着做复杂融合。

### 5.1 新增 embedding 与索引模块

建议新增文件：

```text
src/financial_report_rag/embeddings.py
src/financial_report_rag/vector_store.py
scripts/build_faiss_index.py
scripts/search_faiss.py
```

### 5.2 构建索引

先用 `configs/rag.yaml` 里的 embedding 模型。如果 MacBook Air 跑 `bge-large-zh-v1.5` 太慢，可以临时换成小模型。

```bash
mkdir -p indexes

python scripts/build_faiss_index.py \
  --chunks data/processed/chunks.jsonl \
  --index-path indexes/faiss_flat.index \
  --meta-path indexes/faiss_meta.jsonl \
  --model BAAI/bge-large-zh-v1.5
```

### 5.3 查询验证

```bash
python scripts/search_faiss.py \
  --index-path indexes/faiss_flat.index \
  --meta-path indexes/faiss_meta.jsonl \
  --query "比亚迪 Q3 毛利率是多少？" \
  --top-k 5
```

阶段性实践：

- [ ] 保存 5 个查询及其 Top5 结果到 `docs/experiments_retrieval.md`。
- [ ] 标注哪些结果相关、哪些不相关。
- [ ] 总结纯向量检索的第一个问题，例如“数字问答召回不稳定”或“行业简称召回弱”。

阶段性验收：

- [ ] 查询能返回 Top5 chunks。
- [ ] 每条结果包含分数、来源文档、页码。
- [ ] 至少 3 个问题能召回明显相关证据。

## 6. 阶段 4：BM25 与混合召回

目标：回答“为什么不只用向量检索”。

### 6.1 新增 BM25 检索模块

建议新增文件：

```text
src/financial_report_rag/bm25_store.py
src/financial_report_rag/hybrid_retriever.py
scripts/build_bm25_index.py
scripts/search_hybrid.py
```

### 6.2 构建 BM25 索引

```bash
python scripts/build_bm25_index.py \
  --chunks data/processed/chunks.jsonl \
  --output indexes/bm25.pkl
```

### 6.3 对比三路召回

```bash
python scripts/search_hybrid.py \
  --query "宁德时代装机量是多少？" \
  --faiss-index indexes/faiss_flat.index \
  --faiss-meta indexes/faiss_meta.jsonl \
  --bm25-index indexes/bm25.pkl \
  --top-k 10 \
  --dense-weight 0.6 \
  --bm25-weight 0.4
```

阶段性实践：

- [ ] 找 5 个纯向量召回不好的 query。
- [ ] 对比 BM25 是否更容易命中关键词。
- [ ] 在 `docs/experiments_retrieval.md` 记录“向量、BM25、混合召回”的样例。

阶段性验收：

- [ ] 支持纯向量、纯 BM25、混合召回三种模式。
- [ ] 能解释至少一个混合召回优于纯向量的金融问答例子。

## 7. 阶段 5：离线评测集与 Recall 指标

目标：让每个优化都能用数字说明，而不是靠感觉。

### 7.1 构造评测集

建议文件：

```text
data/processed/eval_qa.jsonl
```

格式：

```json
{
  "query": "比亚迪 Q3 毛利率是多少？",
  "ground_truth_doc_id": "byd_2024_q3_report",
  "answer": "具体答案",
  "question_type": "fact"
}
```

先写 20 条开发集，再扩展到 80-120 条。

### 7.2 新增评测脚本

建议新增文件：

```text
src/financial_report_rag/evaluator.py
scripts/evaluate_retrieval.py
```

运行：

```bash
python scripts/evaluate_retrieval.py \
  --eval-file data/processed/eval_qa.jsonl \
  --chunks data/processed/chunks.jsonl \
  --faiss-index indexes/faiss_flat.index \
  --faiss-meta indexes/faiss_meta.jsonl \
  --bm25-index indexes/bm25.pkl \
  --mode hybrid \
  --top-k 10 \
  --output outputs/retrieval_eval_hybrid.json
```

阶段性实践：

- [ ] 在 `docs/experiments_retrieval.md` 填写 Recall@3 / Recall@5 / Recall@10。
- [ ] 至少比较纯向量、纯 BM25、混合召回三组结果。
- [ ] 记录每组的平均延迟。

阶段性验收：

- [ ] 能得到 Recall@3、Recall@5、Recall@10。
- [ ] 能用一个表说明混合召回是否有效。
- [ ] 能解释不同类型问题下的召回差异。

## 8. 阶段 6：FAISS 索引实验

目标：形成工程深度，知道 Flat、IVF、HNSW 的取舍。

### 8.1 构建不同索引

```bash
python scripts/build_faiss_index.py --chunks data/processed/chunks.jsonl --index-path indexes/faiss_flat.index --meta-path indexes/faiss_meta.jsonl --index-type flat
python scripts/build_faiss_index.py --chunks data/processed/chunks.jsonl --index-path indexes/faiss_ivf.index --meta-path indexes/faiss_meta.jsonl --index-type ivf
python scripts/build_faiss_index.py --chunks data/processed/chunks.jsonl --index-path indexes/faiss_hnsw.index --meta-path indexes/faiss_meta.jsonl --index-type hnsw
```

### 8.2 跑索引对比评测

```bash
python scripts/evaluate_faiss_indexes.py \
  --eval-file data/processed/eval_qa.jsonl \
  --chunks data/processed/chunks.jsonl \
  --indexes indexes/faiss_flat.index indexes/faiss_ivf.index indexes/faiss_hnsw.index \
  --meta indexes/faiss_meta.jsonl \
  --output outputs/faiss_index_eval.csv
```

阶段性实践：

- [ ] 在 `docs/experiments_faiss.md` 记录 Recall@10、延迟、构建时间、内存占用。
- [ ] 写出 Flat、IVF、HNSW 的适用场景。

阶段性验收：

- [ ] 至少完成 Flat 和 HNSW 对比。
- [ ] 能解释“为什么小数据量 Flat 可能更合适”。
- [ ] 能解释“为什么数据量大时需要 IVF / HNSW”。

## 9. 阶段 7：Rerank 与生成约束

目标：提高最终答案相关性，并降低幻觉。

### 9.1 新增 rerank 模块

建议新增文件：

```text
src/financial_report_rag/reranker.py
scripts/search_with_rerank.py
```

运行：

```bash
python scripts/search_with_rerank.py \
  --query "新能源汽车行业 2025 年主要政策变化是什么？" \
  --top-k-retrieve 20 \
  --top-k-rerank 5
```

### 9.2 新增生成模块

建议新增文件：

```text
src/financial_report_rag/generator.py
scripts/answer_query.py
```

生成规则：

- 只基于给定证据回答。
- 答案必须带来源文档和页码。
- 证据不足时回答“不确定”。
- 关键数字必须能在证据中找到。

运行：

```bash
python scripts/answer_query.py \
  --query "比亚迪 Q3 毛利率是多少？" \
  --top-k 5
```

阶段性实践：

- [ ] 在 `docs/experiments_rerank.md` 记录 rerank 前后 Top5 变化。
- [ ] 在 `docs/badcases.md` 记录生成幻觉和引用错误案例。
- [ ] 设计 3 条证据不足的问题，验证系统会拒答。

阶段性验收：

- [ ] 支持 Top20 -> rerank -> Top5。
- [ ] 答案能展示来源文档和页码。
- [ ] 证据不足时不会硬编答案。

## 10. 阶段 8：Demo

目标：把链路包装成一个可以演示的工具。

建议新增文件：

```text
scripts/app_streamlit.py
```

运行：

```bash
streamlit run scripts/app_streamlit.py
```

Demo 页面至少包含：

- query 输入框。
- 最终答案。
- Top5 证据片段。
- 来源文档和页码。
- 召回分数 / rerank 分数。
- 不确定回答提示。

阶段性实践：

- [ ] 选 5 个稳定问题作为演示集。
- [ ] 录入 2 个失败案例，展示 badcase 复盘能力。
- [ ] 在 README 中补充 Demo 运行方式。

阶段性验收：

- [ ] 本地浏览器可以打开 Demo。
- [ ] 演示问题能稳定返回证据。
- [ ] 页面上能清楚看到引用来源。

## 11. 阶段 9：项目沉淀与面试材料

目标：让项目能讲清楚，而不是只会跑。

### 11.1 必备文档

建议创建：

```text
docs/notes_ragflow.md
docs/notes_langchain_chatchat.md
docs/notes_qanything.md
docs/experiments_chunking.md
docs/experiments_retrieval.md
docs/experiments_faiss.md
docs/experiments_rerank.md
docs/badcases.md
docs/interview_notes.md
```

### 11.2 面试高频问题准备

在 `docs/interview_notes.md` 中回答：

- chunk size 怎么选？
- 为什么不只用向量检索？
- reranker 到底提升多少？
- 空召回怎么处理？
- 幻觉怎么缓解？
- QPS 多少，瓶颈在哪里？
- PDF 多栏和表格带来了什么问题？

### 11.3 最终提交

```bash
git status
git add .
git commit -m "Implement financial report RAG pipeline"
git push
```

如果某些大文件不该提交，先检查：

```bash
git status --short
```

确认不要提交：

```text
data/raw/
data/processed/
indexes/
outputs/
models/
```

## 12. 推荐推进顺序

如果时间有限，按这个顺序推进：

1. 收集第一批 3-5 份测试 PDF，并记录到数据清单。
2. PDF 解析，输出 pages JSONL。
3. 基础切块，输出 chunks JSONL。
4. FAISS Flat 检索 baseline。
5. BM25 + 混合召回。
6. 20 条评测集 + Recall 指标。
7. rerank。
8. 简单生成和引用。
9. Streamlit Demo。
10. 扩大数据量和评测集。
11. 整理实验表和 badcase。

每做完一个阶段，都先回答三个问题：

- 这一阶段解决了什么具体问题？
- 有没有数字或例子证明它有效？
- 它暴露了下一个阶段要解决的什么问题？

能持续回答这三个问题，项目就会自然长成一个可讲、可验、可迭代的 RAG 系统。
