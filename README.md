# 金融研报助手

本项目面向金融研报和政策 PDF 问答场景，目标是构建一个 RAG 系统：用户用自然语言提问，系统从 PDF 中检索相关段落，生成答案，并标注来源文档和页码。

## 项目目标

- 解析金融研报、年报、行业报告和政策文件 PDF。
- 对比不同 chunk size 和 overlap 对召回效果的影响。
- 构建 FAISS 向量检索和 BM25 关键词检索 baseline。
- 实现混合召回、rerank 和引用来源校验。
- 自建离线 QA 评测集，记录 Recall、引用命中率和坏例。
- 做一个可演示的问答 Demo，支持返回答案、证据片段和来源页码。

## 目录结构

- `configs/`：RAG 流程配置和实验配置。
- `data/raw/`：原始 PDF 和原始评测数据，默认不提交到 Git。
- `data/processed/`：解析后的 chunks、索引和评测产物，默认不提交到 Git。
- `scripts/`：PDF 解析、建索引、检索、评测和 Demo 脚本。
- `src/financial_report_rag/`：项目可复用代码。
- `docs/`：实验报告、坏例分析、系统设计和面试笔记。

## 硬件说明

这个项目最适合在 MacBook Air 本地推进。PDF 解析、BM25、FAISS CPU 索引和小型 embedding 模型都可以本地运行；如果需要 7B/8B 生成模型或较大的 reranker，可以使用量化本地模型、小模型，或直接接入 API。
