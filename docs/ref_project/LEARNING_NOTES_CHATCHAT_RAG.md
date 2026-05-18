# Langchain-Chatchat RAG 学习笔记

这份笔记用于定位和学习 Langchain-Chatchat 项目中与以下主题相关的代码：

- 中文分词与切块。
- FAISS / Milvus 多向量库适配。
- BM25 + KNN 混合检索。

本文件只做代码阅读索引和链路说明，不涉及代码修改。

## 1. 总体链路

Langchain-Chatchat 的知识库 RAG 主线可以概括为：

```text
上传文件
  -> document loader 加载文件
  -> text splitter 切块
  -> embedding
  -> 写入向量库 FAISS / Milvus / PG / ES / Chroma 等
  -> search_docs 检索
  -> retriever 执行向量检索或 BM25 + KNN 融合
  -> kb_chat / file_chat 组织上下文并调用 LLM
```

关键理解：

- 切块入口主要在 `knowledge_base/utils.py`。
- 向量库统一抽象在 `kb_service/base.py`。
- FAISS、Milvus 等向量库各自有对应的 `KBService` 子类。
- BM25 + KNN 混合检索主要在 `file_rag/retrievers/ensemble.py`。

## 2. 主要代码文件

| 主题 | 文件 | 作用 |
| --- | --- | --- |
| 配置 | `libs/chatchat-server/chatchat/settings.py` | 配置默认向量库、chunk size、overlap、splitter、top_k、score_threshold。 |
| 文件加载与切块入口 | `libs/chatchat-server/chatchat/server/knowledge_base/utils.py` | `KnowledgeFile`、`make_text_splitter()`、`docs2texts()`。 |
| 中文普通切分 | `libs/chatchat-server/chatchat/server/file_rag/text_splitter/chinese_text_splitter.py` | 基于中文标点进行句子切分。 |
| 中文递归切分 | `libs/chatchat-server/chatchat/server/file_rag/text_splitter/chinese_recursive_text_splitter.py` | 默认中文递归 splitter，按换行、句号、逗号等逐级拆分。 |
| 中文标题增强 | `libs/chatchat-server/chatchat/server/file_rag/text_splitter/zh_title_enhance.py` | 检测标题，并把标题语义补到后续 chunk。 |
| 知识库抽象 | `libs/chatchat-server/chatchat/server/knowledge_base/kb_service/base.py` | `KBService` 抽象基类与 `KBServiceFactory`。 |
| FAISS 实现 | `libs/chatchat-server/chatchat/server/knowledge_base/kb_service/faiss_kb_service.py` | FAISS 知识库增删改查。 |
| FAISS 缓存 | `libs/chatchat-server/chatchat/server/knowledge_base/kb_cache/faiss_cache.py` | FAISS 本地 index 加载、保存、线程安全缓存。 |
| Milvus 实现 | `libs/chatchat-server/chatchat/server/knowledge_base/kb_service/milvus_kb_service.py` | Milvus 知识库连接、添加文档、检索。 |
| Retriever 注册 | `libs/chatchat-server/chatchat/server/file_rag/utils.py` | `get_Retriever()` 根据名称返回 retriever service。 |
| 普通向量检索 | `libs/chatchat-server/chatchat/server/file_rag/retrievers/vectorstore.py` | 基于 LangChain vectorstore 的 similarity 检索。 |
| Milvus 检索适配 | `libs/chatchat-server/chatchat/server/file_rag/retrievers/milvus_vectorstore.py` | Milvus vectorstore retriever 适配。 |
| BM25 + KNN 融合 | `libs/chatchat-server/chatchat/server/file_rag/retrievers/ensemble.py` | BM25 + FAISS vector retriever 融合。 |
| 知识库检索 API | `libs/chatchat-server/chatchat/server/knowledge_base/kb_doc_api.py` | `search_docs()`、`upload_docs()`、`update_docs()`。 |
| 知识库问答 | `libs/chatchat-server/chatchat/server/chat/kb_chat.py` | 本地知识库问答入口。 |
| 临时文件问答 | `libs/chatchat-server/chatchat/server/chat/file_chat.py` | 临时文件 RAG，使用临时 FAISS 向量库。 |

## 3. 中文分词与切块

### 3.1 配置入口

文件：

```text
libs/chatchat-server/chatchat/settings.py
```

重点配置：

```python
CHUNK_SIZE = 750
OVERLAP_SIZE = 150
TEXT_SPLITTER_NAME = "ChineseRecursiveTextSplitter"
```

`text_splitter_dict` 里定义了支持的 splitter：

- `ChineseRecursiveTextSplitter`
- `SpacyTextSplitter`
- `RecursiveCharacterTextSplitter`
- `MarkdownHeaderTextSplitter`

### 3.2 splitter 创建入口

文件：

```text
libs/chatchat-server/chatchat/server/knowledge_base/utils.py
```

核心函数：

```python
make_text_splitter(splitter_name, chunk_size, chunk_overlap)
```

逻辑：

1. 优先从 `chatchat.server.file_rag.text_splitter` 找自定义 splitter。
2. 找不到时退回 LangChain 内置 splitter。
3. 根据配置决定用 tiktoken、huggingface tokenizer，或直接按字符长度切。

### 3.3 文件到 chunk

同一个文件中的 `KnowledgeFile.docs2texts()` 是真正执行切块的位置：

```text
KnowledgeFile.file2docs()
  -> loader.load()
  -> KnowledgeFile.docs2texts()
  -> make_text_splitter()
  -> text_splitter.split_documents()
  -> zh_title_enhance()
```

也就是说，文件进入知识库时，大体会走：

```text
文件
  -> loader
  -> Document 列表
  -> splitter
  -> chunk Document 列表
```

### 3.4 中文 splitter

文件：

```text
libs/chatchat-server/chatchat/server/file_rag/text_splitter/chinese_recursive_text_splitter.py
```

核心类：

```python
ChineseRecursiveTextSplitter
```

默认分隔符：

```python
[
    "\n\n",
    "\n",
    "。|！|？",
    "\.\s|\!\s|\?\s",
    "；|;\s",
    "，|,\s",
]
```

逻辑：

1. 先找当前文本中可用的最粗粒度分隔符。
2. 用该分隔符切开文本。
3. 小于 `chunk_size` 的片段暂存。
4. 大于 `chunk_size` 的片段继续用更细粒度分隔符递归切。
5. 最后调用 LangChain 的 `_merge_splits()` 合并，并处理 `chunk_overlap`。

文件：

```text
libs/chatchat-server/chatchat/server/file_rag/text_splitter/chinese_text_splitter.py
```

核心类：

```python
ChineseTextSplitter
```

它更像基于中文标点的句子切分器，会处理：

- 句号、问号、感叹号。
- 中文/英文省略号。
- PDF 多余空白和换行。
- 过长句子再按逗号、空格等继续拆。

### 3.5 中文标题增强

文件：

```text
libs/chatchat-server/chatchat/server/file_rag/text_splitter/zh_title_enhance.py
```

核心函数：

```python
zh_title_enhance(docs)
```

逻辑：

1. 判断某个 chunk 是否可能是标题。
2. 如果是标题，记录到 `metadata["category"] = "cn_Title"`。
3. 后续 chunk 会补一句：

```text
下文与(标题)有关。原文内容
```

目的是让后续 chunk 在缺少标题上下文时，也能带上章节语义。

## 4. FAISS / Milvus 多向量库适配

### 4.1 抽象基类

文件：

```text
libs/chatchat-server/chatchat/server/knowledge_base/kb_service/base.py
```

核心类：

```python
KBService
```

统一接口：

- `create_kb()`
- `add_doc()`
- `delete_doc()`
- `update_doc()`
- `search_docs()`
- `do_search()`
- `do_add_doc()`
- `do_delete_doc()`

其中 `add_doc()` 和 `search_docs()` 是外部常用入口，具体逻辑委托给子类实现：

```text
KBService.add_doc()
  -> do_add_doc()

KBService.search_docs()
  -> do_search()
```

### 4.2 向量库工厂

同文件中的：

```python
KBServiceFactory.get_service()
```

负责根据向量库类型创建具体服务：

- `faiss` -> `FaissKBService`
- `milvus` -> `MilvusKBService`
- `pg` -> `PGKBService`
- `es` -> `ESKBService`
- `chromadb` -> `ChromaKBService`
- `zilliz` -> `ZillizKBService`

这就是多向量库适配的核心设计：

```text
统一 KBService 接口
  + 不同向量库子类实现
  + Factory 动态选择
```

### 4.3 FAISS 实现

文件：

```text
libs/chatchat-server/chatchat/server/knowledge_base/kb_service/faiss_kb_service.py
```

核心类：

```python
FaissKBService
```

关键逻辑：

- `load_vector_store()` 从 `kb_faiss_pool` 获取线程安全 FAISS 实例。
- `do_add_doc()` 对文本做 embedding，然后 `vs.add_embeddings()`。
- `do_search()` 使用 `get_Retriever("ensemble")`。
- `save_vector_store()` 保存本地 FAISS index。

注意：FAISS 的检索在这里默认走 `ensemble`，也就是 BM25 + KNN 混合检索。

### 4.4 FAISS 缓存池

文件：

```text
libs/chatchat-server/chatchat/server/knowledge_base/kb_cache/faiss_cache.py
```

核心类：

- `ThreadSafeFaiss`
- `KBFaissPool`
- `MemoFaissPool`

职责：

- 从磁盘加载 FAISS index。
- 没有 index 时创建空向量库。
- 通过锁保证多线程安全。
- 保存 index 到本地路径。

知识库 FAISS：

```python
kb_faiss_pool
```

临时文件对话 FAISS：

```python
memo_faiss_pool
```

### 4.5 Milvus 实现

文件：

```text
libs/chatchat-server/chatchat/server/knowledge_base/kb_service/milvus_kb_service.py
```

核心类：

```python
MilvusKBService
```

关键逻辑：

- `_load_milvus()` 创建 LangChain `Milvus` vectorstore。
- 连接参数来自 `Settings.kb_settings.kbs_config["milvus"]`。
- index/search 参数来自 `milvus_kwargs`。
- `do_add_doc()` 调用 `self.milvus.add_documents(docs)`。
- `do_search()` 使用 `get_Retriever("milvusvectorstore")`。

注意：Milvus 当前走的是 `milvusvectorstore`，主要是向量检索路径，不是 FAISS 那个 BM25 + KNN `ensemble` 路径。

## 5. BM25 + KNN 混合检索

核心文件：

```text
libs/chatchat-server/chatchat/server/file_rag/retrievers/ensemble.py
```

核心类：

```python
EnsembleRetrieverService
```

核心逻辑：

```python
faiss_retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": score_threshold, "k": top_k},
)

bm25_retriever = BM25Retriever.from_documents(
    docs,
    preprocess_func=jieba.lcut_for_search,
)

ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, faiss_retriever],
    weights=[0.5, 0.5],
)
```

拆开看：

- KNN / 向量检索：`vectorstore.as_retriever(...)`
- BM25 检索：`BM25Retriever.from_documents(...)`
- 中文分词：`jieba.lcut_for_search`
- 融合方式：LangChain `EnsembleRetriever`
- 融合权重：`[0.5, 0.5]`

### 5.1 FAISS 知识库检索链路

```text
kb_doc_api.search_docs()
  -> KBServiceFactory.get_service_by_name()
  -> FaissKBService.search_docs()
  -> FaissKBService.do_search()
  -> get_Retriever("ensemble")
  -> EnsembleRetrieverService
  -> BM25Retriever + FAISS retriever
```

所以，FAISS 本地知识库搜索默认会进入 BM25 + KNN 融合。

### 5.2 Milvus 知识库检索链路

```text
kb_doc_api.search_docs()
  -> KBServiceFactory.get_service_by_name()
  -> MilvusKBService.search_docs()
  -> MilvusKBService.do_search()
  -> get_Retriever("milvusvectorstore")
  -> MilvusVectorstoreRetrieverService
  -> Milvus similarity_search_with_score
```

所以，Milvus 当前主要是向量检索，不是 `ensemble.py` 里的 BM25 + KNN 融合。

### 5.3 临时文件对话链路

文件：

```text
libs/chatchat-server/chatchat/server/chat/file_chat.py
```

临时文件上传后进入：

```text
upload_temp_docs()
  -> KnowledgeFile.file2text()
  -> memo_faiss_pool.load_vector_store()
  -> vs.add_documents()
```

临时文件检索时：

```text
file_chat()
  -> embed query
  -> memo_faiss_pool.acquire()
  -> vs.similarity_search_with_score_by_vector()
```

注意：这个临时文件对话路径是直接 FAISS 向量检索，不走 `ensemble.py`。

## 6. 推荐阅读顺序

建议按下面顺序看：

1. `libs/chatchat-server/chatchat/settings.py`
2. `libs/chatchat-server/chatchat/server/knowledge_base/utils.py`
3. `libs/chatchat-server/chatchat/server/file_rag/text_splitter/chinese_recursive_text_splitter.py`
4. `libs/chatchat-server/chatchat/server/file_rag/text_splitter/chinese_text_splitter.py`
5. `libs/chatchat-server/chatchat/server/file_rag/text_splitter/zh_title_enhance.py`
6. `libs/chatchat-server/chatchat/server/knowledge_base/kb_service/base.py`
7. `libs/chatchat-server/chatchat/server/knowledge_base/kb_service/faiss_kb_service.py`
8. `libs/chatchat-server/chatchat/server/knowledge_base/kb_cache/faiss_cache.py`
9. `libs/chatchat-server/chatchat/server/file_rag/retrievers/ensemble.py`
10. `libs/chatchat-server/chatchat/server/knowledge_base/kb_service/milvus_kb_service.py`
11. `libs/chatchat-server/chatchat/server/file_rag/retrievers/milvus_vectorstore.py`
12. `libs/chatchat-server/chatchat/server/knowledge_base/kb_doc_api.py`
13. `libs/chatchat-server/chatchat/server/chat/kb_chat.py`
14. `libs/chatchat-server/chatchat/server/chat/file_chat.py`

## 7. 对比 RAGFlow 的一个观察

RAGFlow 的重点在更完整的文档解析、版面理解、表格结构识别，以及检索时的 token/vector/rank feature 融合。

Langchain-Chatchat 这里更适合学习：

- LangChain splitter 的组织方式。
- 中文递归切块。
- 多向量库统一接口。
- FAISS 本地 index 缓存。
- 用 LangChain `BM25Retriever + EnsembleRetriever` 快速搭建 BM25 + KNN 混合检索。

如果你要给自己的 RAG 复用思路，可以优先参考：

```text
ChineseRecursiveTextSplitter
KBService + KBServiceFactory
FaissKBService
MilvusKBService
EnsembleRetrieverService
```
