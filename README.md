# 金融研报 RAG 问答系统

本项目面向金融研报和政策 PDF 问答场景，针对多栏排版、表格连续、页码证据定位和跨文档汇总等问题，设计并实现了一套可评测、可演示的 RAG 系统。

当前正式路线：

```text
PDF 解析 -> 表格保护切块 -> FAISS Dense 索引 + BM25 索引
        -> 按问题类型路由召回 -> Cross-Encoder rerank
        -> 父文档扩展 -> 证据约束生成 -> 规则评测 + LLM Judge
```

## 当前结果

数据与评测集：

| item | value |
|---|---:|
| PDF 文档 | 150 |
| 解析页面 | 1092 |
| 表格数量 | 1014 |
| chunk 数 | 6826 |
| 自建评测集 | 120 |
| 评测类型 | fact 70 / compare 30 / summary 20 |

检索阶段当前最佳策略是 `routed_v17_compare_raw_entity_slots`：

| scheme | Recall@5 | Recall@8 | HitAny@8 | HitAll@8 |
|---|---:|---:|---:|---:|
| routed_v17 | 94.90% | 96.35% | 98.33% | 94.17% |

按问题类型：

| question_type | strategy | Recall@8 | HitAll@8 |
|---|---|---:|---:|
| fact | hybrid Top5 + parent window | 97.14% | 97.14% |
| compare | query rewrite + entity slots + rerank + parent fill | 100.00% | 100.00% |
| summary | hybrid Top50 + source diverse Top8 | 88.08% | 75.00% |

生成阶段当前结果：

| metric | value |
|---|---:|
| answer_rate | 100.00% |
| citation_rate | 97.50% |
| reference_hit_all | 93.33% |
| numeric_coverage | 86.31% |
| judge_correct_rate | 80.00% |
| judge_avg_score | 86.62 |

完整实验总览见 [docs/experiments/summary.md](docs/experiments/summary.md)。

## 目录结构

```text
configs/                  RAG 流程配置
data/raw/                 原始 PDF，默认不提交到 Git
data/processed/           页面、chunk、索引、query rewrite 等中间产物
data/eval/                120 条自建评测集
data/generated/           生成答案和 dry-run 输出
demo/                     Streamlit 可视化 Demo
docs/                     项目文档、实验报告、badcase、面试问答
models/                   本地 embedding / reranker 模型，默认不提交到 Git
scripts/                  数据处理、索引构建、检索评测、生成评测脚本
src/financial_report_rag/  可复用核心代码
```

## 环境准备

建议使用当前项目的 Homebrew Python 虚拟环境：

```bash
cd /Users/linsh/Documents/Recommendation/project/ProjectSet/financial_research_assistant
source .venv-brew/bin/activate
pip install -r requirements.txt
```

本地模型默认放在：

```text
models/bge-large-zh-v1.5
models/bge-reranker-v2-m3
```

如果需要调用生成模型，设置 OpenAI-compatible API：

```bash
export DEEPSEEK_API_KEY="你的 key"
export OPENAI_BASE_URL="https://api.deepseek.com"
export OPENAI_MODEL="deepseek-chat"
```

## 运行 Demo

Demo 支持输入问题、展示路由策略、召回证据、引用来源和最终回答。没有 API Key 时也可以使用 dry-run 模式，只看检索证据和 prompt。

```bash
cd /Users/linsh/Documents/Recommendation/project/ProjectSet/financial_research_assistant
source .venv-brew/bin/activate
streamlit run demo/app.py
```

更多说明见 [docs/demo.md](docs/demo.md)。

## 常用命令

重建完整 FAISS + BM25 索引：

```bash
python scripts/retrieval/rebuild_full_indexes.py \
  --chunks data/processed/chunks/chunks_boundary.jsonl \
  --output-dir data/processed/indexes/bge_large_zh_v15 \
  --embedding-model models/bge-large-zh-v1.5 \
  --embedding-backend sentence-transformers \
  --tokenizer jieba
```

运行当前正式检索评测：

```bash
python scripts/evaluation/evaluate_routed_retrieval.py \
  --eval data/eval/financial_qa_dev.jsonl \
  --index-dir data/processed/indexes/bge_large_zh_v15 \
  --index-type flat \
  --bm25-path data/processed/indexes/bge_large_zh_v15/bm25.pkl \
  --embedding-model models/bge-large-zh-v1.5 \
  --embedding-backend sentence-transformers \
  --reranker-model models/bge-reranker-v2-m3 \
  --reranker-backend transformers \
  --compare-rewrite-file data/processed/query_rewrites/compare_financial_table_no_unit_rule.jsonl \
  --compare-rewrite-mode separate \
  --compare-rewrite-top-k 8 \
  --compare-rewrite-per-query-keep 2 \
  --compare-coarse-to-fine-supplement \
  --compare-coarse-doc-top-n 2 \
  --compare-coarse-adaptive-doc-ratio 3.0 \
  --compare-coarse-page-top-k 12 \
  --compare-coarse-per-entity-keep 4 \
  --compare-coarse-guarantee-per-entity 4 \
  --compare-parent-fill \
  --compare-parent-fill-pool 12 \
  --parent-window-pages 1 \
  --output docs/experiments/rerank/17_routed_compare_raw_entity_slots/report.md \
  --details-output docs/experiments/rerank/17_routed_compare_raw_entity_slots/details.json
```

运行全量回答生成：

```bash
python scripts/generation/generate_answers.py \
  --eval data/eval/financial_qa_dev.jsonl \
  --output data/generated/eval_runs/routed_v17_deepseek_full_answers.jsonl \
  --base-url "$OPENAI_BASE_URL" \
  --model "$OPENAI_MODEL" \
  --api-key-env DEEPSEEK_API_KEY \
  --index-dir data/processed/indexes/bge_large_zh_v15 \
  --index-type flat \
  --bm25-path data/processed/indexes/bge_large_zh_v15/bm25.pkl \
  --embedding-model models/bge-large-zh-v1.5 \
  --embedding-backend sentence-transformers \
  --reranker-model models/bge-reranker-v2-m3 \
  --reranker-backend transformers \
  --compare-rewrite-file data/processed/query_rewrites/compare_financial_table_no_unit_rule.jsonl \
  --compare-rewrite-mode separate \
  --compare-rewrite-top-k 8 \
  --compare-rewrite-per-query-keep 2 \
  --compare-coarse-to-fine-supplement \
  --compare-coarse-doc-top-n 2 \
  --compare-coarse-adaptive-doc-ratio 3.0 \
  --compare-coarse-page-top-k 12 \
  --compare-coarse-per-entity-keep 4 \
  --compare-coarse-guarantee-per-entity 4 \
  --compare-parent-fill \
  --compare-parent-fill-pool 12 \
  --parent-window-pages 1 \
  --max-contexts 8 \
  --max-chars-per-context 1800 \
  --max-total-context-chars 9000 \
  --sleep-seconds 1
```

运行生成效果评测：

```bash
python scripts/evaluation/evaluate_generation.py \
  --eval data/eval/financial_qa_dev.jsonl \
  --pred data/generated/eval_runs/routed_v17_deepseek_full_answers.jsonl \
  --output docs/experiments/generation/routed_v17_deepseek_full/report.md \
  --details-output docs/experiments/generation/details/routed_v17_deepseek_full/details.json \
  --match-level page
```

## 文档入口

- [docs/README.md](docs/README.md)：文档导航。
- [docs/architecture.md](docs/architecture.md)：系统架构和模块选型。
- [docs/demo.md](docs/demo.md)：Demo 使用说明。
- [docs/experiments/summary.md](docs/experiments/summary.md)：阶段性实验总览。
- [docs/experiments/generation/badcase_analysis/report.md](docs/experiments/generation/badcase_analysis/report.md)：生成 badcase 分析。
- [docs/experiments/rerank/badcase_analysis.md](docs/experiments/rerank/badcase_analysis.md)：检索 badcase 分析。
- [docs/interview/high_frequency_questions.md](docs/interview/high_frequency_questions.md)：面试高频追问。

## 项目亮点

- 深入参考 RAGFlow DeepDoc 的 PDF 解析思想，针对多栏文本、表格区域和页面块顺序做了定制处理。
- 采用表格保护切块策略，避免表格行被切断，保留表格作为完整证据块。
- 基于 `bge-large-zh-v1.5 + FAISS` 和 `jieba BM25` 构建混合召回。
- 参考 Langchain-Chatchat 和 QAnything 的思路，引入多路召回、Cross-Encoder rerank、父子文档扩展和阈值/路由实验。
- 自建 120 条三类评测集，形成检索、生成、LLM Judge 和 badcase 分析闭环。
