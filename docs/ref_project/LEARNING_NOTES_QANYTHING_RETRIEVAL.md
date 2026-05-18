# QAnything 检索链路学习笔记

本文档用于学习 QAnything 中与以下内容相关的代码：

- 2-stage retrieval：先 embedding 粗筛，再 rerank 精排
- 父子文档召回策略
- rerank 阈值设计
- Milvus embedding 召回与 Elasticsearch BM25 混合检索

## 1. 建议先看的概念说明

先看项目文档中的两阶段检索说明：

- [`README_zh.md`](README_zh.md)

重点关注：

- “为什么是两阶段检索?”
- “一阶段检索（embedding）”
- “二阶段检索（rerank）”

QAnything 的核心思想是：

1. 第一阶段用 embedding 向量检索，从大规模知识库中快速召回一批候选文档。
2. 第二阶段用 rerank 模型对候选文档重新排序，提高最终送入 LLM 的上下文质量。

## 2. 总入口：请求如何进入检索链路

入口文件：

- [`qanything_kernel/qanything_server/handler.py`](qanything_kernel/qanything_server/handler.py)

重点看 `local_doc_chat` 相关逻辑。这里会从请求参数中读取：

- `kb_ids`：知识库 ID
- `question`：用户问题
- `rerank`：是否开启 rerank
- `top_k`：粗召回数量
- `hybrid_search`：是否开启混合检索
- `chunk_size`：父文档切块大小

然后调用：

```python
local_doc_qa.get_knowledge_based_answer(...)
```

也就是说，`handler.py` 主要负责接收请求、解析参数、调用核心 QA 流程。

## 3. 核心主线：local_doc_qa.py

核心文件：

- [`qanything_kernel/core/local_doc_qa.py`](qanything_kernel/core/local_doc_qa.py)

重点看三个函数。

### 3.1 `init_cfg()`

初始化核心组件：

```python
self.embeddings = YouDaoEmbeddings()
self.rerank = YouDaoRerank()
self.milvus_kb = VectorStoreMilvusClient()
self.es_client = StoreElasticSearchClient()
self.retriever = ParentRetriever(...)
```

这里把 embedding、rerank、Milvus、Elasticsearch、父子文档 retriever 串起来。

### 3.2 `get_source_documents()`

这是第一阶段 embedding 粗召回入口。

它调用：

```python
retriever.get_retrieved_documents(...)
```

返回的是初步召回的候选文档。

### 3.3 `get_knowledge_based_answer()`

这是完整 RAG 流程主函数。

大致流程：

1. 如果有历史对话，先做 query rewrite。
2. 调用 `get_source_documents()` 做 embedding 粗召回。
3. 可选加入 web search 结果。
4. 去重。
5. 如果开启 `rerank`，调用 rerank 模型精排。
6. 根据 rerank 分数做阈值过滤。
7. 截断到 `top_k`。
8. 拼接上下文，调用 LLM 生成答案。

## 4. 第一阶段：embedding 粗召回

相关文件：

- [`qanything_kernel/core/retriever/parent_retriever.py`](qanything_kernel/core/retriever/parent_retriever.py)
- [`qanything_kernel/core/retriever/vectorstore.py`](qanything_kernel/core/retriever/vectorstore.py)
- [`qanything_kernel/connector/embedding/embedding_for_online_client.py`](qanything_kernel/connector/embedding/embedding_for_online_client.py)
- [`qanything_kernel/dependent_server/embedding_server/embedding_server.py`](qanything_kernel/dependent_server/embedding_server/embedding_server.py)

调用链大致是：

```text
local_doc_qa.get_source_documents()
  -> ParentRetriever.get_retrieved_documents()
    -> SelfParentRetriever.aget_relevant_documents()
      -> Milvus similarity search
        -> YouDaoEmbeddings
          -> embedding_server /embedding
```

`embedding_for_online_client.py` 是 embedding 客户端，主要把文本发到本地 embedding 服务：

```python
self.url = f"http://{LOCAL_EMBED_SERVICE_URL}/embedding"
```

`embedding_server.py` 是 embedding 服务端，接收文本并返回向量。

## 5. 第二阶段：rerank 精排

相关文件：

- [`qanything_kernel/core/local_doc_qa.py`](qanything_kernel/core/local_doc_qa.py)
- [`qanything_kernel/connector/rerank/rerank_for_online_client.py`](qanything_kernel/connector/rerank/rerank_for_online_client.py)
- [`qanything_kernel/dependent_server/rerank_server/rerank_server.py`](qanything_kernel/dependent_server/rerank_server/rerank_server.py)

在 `local_doc_qa.py` 中，粗召回之后会判断：

```python
if rerank and len(source_documents) > 1 and num_tokens_rerank(query) <= 300:
```

满足条件后调用：

```python
source_documents = await self.rerank.arerank_documents(condense_question, source_documents)
```

`rerank_for_online_client.py` 会请求本地 rerank 服务：

```python
self.url = f"http://{LOCAL_RERANK_SERVICE_URL}/rerank"
```

`rerank_server.py` 提供 `/rerank` 接口，内部调用 ONNX rerank 后端模型。

## 6. rerank 阈值设计

重点文件：

- [`qanything_kernel/core/local_doc_qa.py`](qanything_kernel/core/local_doc_qa.py)

QAnything 的 rerank 阈值主要有两层。

### 6.1 绝对分数阈值

rerank 后会过滤低分文档：

```python
if filtered_documents := [doc for doc in source_documents if doc.metadata['score'] >= 0.28]:
    source_documents = filtered_documents
```

也就是说，rerank 分数低于 `0.28` 的文档通常会被丢弃。

### 6.2 相对分差阈值

保留第一名文档之后，继续比较后续文档和第一名的分差：

```python
relative_difference = (saved_docs[0].metadata['score'] - doc.metadata['score']) / saved_docs[0].metadata['score']
if relative_difference > 0.5:
    break
```

含义是：

- 如果某个文档比第一名低太多，就停止继续保留后面的文档。
- 这里的 `0.5` 是一个相对分差阈值。

所以 QAnything 的 rerank 过滤不是只看固定分数，还会看“和第一名相比差多少”。

## 7. 父子文档召回策略

核心文件：

- [`qanything_kernel/core/retriever/parent_retriever.py`](qanything_kernel/core/retriever/parent_retriever.py)
- [`qanything_kernel/core/retriever/docstrore.py`](qanything_kernel/core/retriever/docstrore.py)
- [`qanything_kernel/core/retriever/general_document.py`](qanything_kernel/core/retriever/general_document.py)

核心类：

```python
class SelfParentRetriever(ParentDocumentRetriever)
class ParentRetriever
class MysqlStore(InMemoryStore)
```

父子文档策略的逻辑是：

1. 入库时，原文先被切成 parent chunk。
2. 每个 parent chunk 再切成更小的 child chunk。
3. child chunk 写入 Milvus，用于向量召回。
4. parent chunk 写入 MySQL，用于最终返回。
5. 查询时先召回 child chunk。
6. 根据 child chunk 中保存的 parent id，回到 MySQL 取 parent chunk。

代码中对应逻辑：

```python
sub_docs = self.child_splitter.split_documents([doc])
_doc.metadata[self.id_key] = _id
docs.extend(sub_docs)
full_docs.append((_id, doc))
```

其中：

- `docs` 是 child docs，会进入 Milvus。
- `full_docs` 是 parent docs，会进入 MySQL docstore。

查询时：

```python
res = await self.vectorstore.asimilarity_search_with_score(...)
sub_docs = [doc for doc, _ in res]
ids = [...]
docs = await self.docstore.amget(ids)
```

也就是：先命中 child，再取回 parent。

## 8. 文档切分和入库

相关文件：

- [`qanything_kernel/core/retriever/general_document.py`](qanything_kernel/core/retriever/general_document.py)
- [`qanything_kernel/dependent_server/insert_files_serve/insert_files_server.py`](qanything_kernel/dependent_server/insert_files_serve/insert_files_server.py)

`general_document.py` 负责把不同格式的文件转成 LangChain `Document`：

- PDF
- Markdown
- TXT
- 图片 OCR
- DOCX
- XLSX
- PPTX
- CSV
- URL
- FAQ

重点看：

```python
split_file_to_docs()
inject_metadata()
```

`insert_files_server.py` 中会调用：

```python
local_file.split_file_to_docs()
retriever.insert_documents(local_file.docs, chunk_size)
```

也就是说：

```text
文件解析 -> Document 列表 -> 父子切块 -> child 入 Milvus -> parent 入 MySQL
```

## 9. 混合检索：Milvus embedding + Elasticsearch BM25

相关文件：

- [`qanything_kernel/core/retriever/parent_retriever.py`](qanything_kernel/core/retriever/parent_retriever.py)
- [`qanything_kernel/core/retriever/elasticsearchstore.py`](qanything_kernel/core/retriever/elasticsearchstore.py)

如果请求中 `hybrid_search=True`，`ParentRetriever.get_retrieved_documents()` 会在 Milvus 召回之后，再调用 Elasticsearch：

```python
es_sub_docs = await self.es_store.asimilarity_search(query, k=top_k, filter=filter)
```

Elasticsearch 初始化时使用 BM25 策略：

```python
strategy=ElasticsearchStore.BM25RetrievalStrategy()
```

所以混合检索逻辑是：

```text
Milvus embedding 召回
  + Elasticsearch BM25 召回
  -> 按 doc_id 去重
  -> 合并候选文档
  -> 后续进入 rerank
```

注意：这里不是像 LangChain-Chatchat 那样用 `EnsembleRetriever` 做加权融合，而是把 Milvus 结果和 ES 结果合并后，再交给 rerank 精排。

## 10. 关键配置

配置文件：

- [`qanything_kernel/configs/model_config.py`](qanything_kernel/configs/model_config.py)

重点配置：

```python
VECTOR_SEARCH_TOP_K = 30
VECTOR_SEARCH_SCORE_THRESHOLD = 0.3
LOCAL_RERANK_SERVICE_URL = "localhost:8001"
LOCAL_EMBED_SERVICE_URL = "localhost:9001"
DEFAULT_CHILD_CHUNK_SIZE = 400
DEFAULT_PARENT_CHUNK_SIZE = 800
SEPARATORS = ["\n\n", "\n", "。", "，", ",", ".", ""]
```

需要注意：

- `VECTOR_SEARCH_TOP_K` 是默认粗召回数量。
- `DEFAULT_PARENT_CHUNK_SIZE` 控制 parent chunk 大小。
- `DEFAULT_CHILD_CHUNK_SIZE` 控制 child chunk 大小。
- `VECTOR_SEARCH_SCORE_THRESHOLD` 在当前主链路里不是最核心的过滤点。
- 实际 rerank 阈值重点看 `local_doc_qa.py` 中的 `0.28` 和 `0.5`。

## 11. 推荐阅读顺序

建议按下面顺序读：

1. [`README_zh.md`](README_zh.md)  
   先理解 QAnything 为什么采用两阶段检索。

2. [`qanything_kernel/qanything_server/handler.py`](qanything_kernel/qanything_server/handler.py)  
   看请求参数如何进入 RAG 主流程。

3. [`qanything_kernel/core/local_doc_qa.py`](qanything_kernel/core/local_doc_qa.py)  
   重点串起：query rewrite、embedding 粗召回、rerank 精排、阈值过滤、答案生成。

4. [`qanything_kernel/core/retriever/parent_retriever.py`](qanything_kernel/core/retriever/parent_retriever.py)  
   重点理解父子文档召回。

5. [`qanything_kernel/core/retriever/general_document.py`](qanything_kernel/core/retriever/general_document.py)  
   看文件如何被解析成 Document，并注入 metadata。

6. [`qanything_kernel/core/retriever/vectorstore.py`](qanything_kernel/core/retriever/vectorstore.py)  
   看 Milvus 向量库如何被封装。

7. [`qanything_kernel/connector/embedding/embedding_for_online_client.py`](qanything_kernel/connector/embedding/embedding_for_online_client.py)  
   看 embedding 客户端如何请求本地服务。

8. [`qanything_kernel/connector/rerank/rerank_for_online_client.py`](qanything_kernel/connector/rerank/rerank_for_online_client.py)  
   看 rerank 客户端如何请求本地服务，并如何把分数写回文档 metadata。

9. [`qanything_kernel/core/retriever/elasticsearchstore.py`](qanything_kernel/core/retriever/elasticsearchstore.py)  
   看 BM25 检索如何接入。

10. [`qanything_kernel/configs/model_config.py`](qanything_kernel/configs/model_config.py)  
    最后回来看 top_k、chunk size、embedding/rerank 服务地址和阈值配置。

## 12. 如果你要参考它自己实现 RAG

最值得借鉴的是这三个设计：

1. **两阶段检索**
   - 先用 embedding 召回较多候选。
   - 再用 rerank 对候选文档精排。

2. **父子文档召回**
   - 小 chunk 用于召回，保证匹配准确。
   - 大 chunk 用于返回，保证上下文完整。

3. **混合检索后统一 rerank**
   - Milvus 负责语义召回。
   - Elasticsearch BM25 负责关键词召回。
   - 合并去重后交给 rerank 统一排序。

一个可以参考的简化实现流程：

```text
上传文件
  -> 解析成 Document
  -> parent chunk
  -> child chunk
  -> child 写入向量库
  -> parent 写入 docstore

用户提问
  -> query rewrite，可选
  -> embedding 检索 child
  -> 根据 parent id 取 parent
  -> 可选 BM25 补充召回
  -> 合并去重
  -> rerank
  -> 阈值过滤
  -> top_k 截断
  -> 拼 prompt
  -> LLM 生成答案
```
