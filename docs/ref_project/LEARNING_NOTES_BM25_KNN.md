# BM25 + KNN 混合检索代码简明笔记

这份笔记只总结 Langchain-Chatchat 中 BM25 + KNN 混合检索相关代码。

## 1. 一句话结论

Langchain-Chatchat 没有自己从零实现 BM25、KNN 或融合排序，而是调用 LangChain 生态中的组件：

- BM25：`langchain_community.retrievers.BM25Retriever`
- KNN：`vectorstore.as_retriever(...)`，底层通常是 FAISS
- 融合：`langchain.retrievers.EnsembleRetriever`

项目自己做的主要是把这些组件串起来。

## 2. 核心代码文件

| 文件 | 作用 |
| --- | --- |
| `libs/chatchat-server/chatchat/server/file_rag/retrievers/ensemble.py` | BM25 + KNN 混合检索核心。 |
| `libs/chatchat-server/chatchat/server/knowledge_base/kb_service/faiss_kb_service.py` | FAISS 知识库服务，检索时会调用 `ensemble`。 |
| `libs/chatchat-server/chatchat/server/file_rag/utils.py` | Retriever 注册表，负责把 `"ensemble"` 映射到 `EnsembleRetrieverService`。 |
| `libs/chatchat-server/chatchat/server/knowledge_base/kb_service/base.py` | 知识库服务抽象层，根据向量库类型选择具体服务。 |
| `libs/chatchat-server/chatchat/server/knowledge_base/kb_doc_api.py` | API 层检索入口 `search_docs()`。 |
| `libs/chatchat-server/chatchat/server/knowledge_base/kb_cache/faiss_cache.py` | FAISS 向量库加载、缓存、保存。 |

## 3. 运行顺序

FAISS 知识库检索时，BM25 + KNN 的调用链大概是：

```text
kb_doc_api.search_docs()
  -> KBServiceFactory.get_service_by_name()
  -> FaissKBService.search_docs()
  -> FaissKBService.do_search()
  -> get_Retriever("ensemble")
  -> EnsembleRetrieverService.from_vectorstore()
  -> BM25Retriever + FAISS vector retriever
  -> EnsembleRetriever 融合结果
```

## 4. 各文件之间的关系

### 4.1 `kb_doc_api.py`

`search_docs()` 是知识库检索的 API 服务函数。

它做的事情很简单：

```text
根据 knowledge_base_name 找到 KBService
  -> 调用 kb.search_docs(query, top_k, score_threshold)
```

它不关心底层到底是 FAISS、Milvus 还是其他向量库。

### 4.2 `base.py`

`KBService` 是统一接口。

```python
KBService.search_docs()
```

会调用子类实现：

```python
self.do_search(query, top_k, score_threshold)
```

`KBServiceFactory` 负责根据知识库配置选择具体服务：

```text
faiss -> FaissKBService
milvus -> MilvusKBService
pg -> PGKBService
es -> ESKBService
```

所以它是“多向量库适配”的分发层。

### 4.3 `faiss_kb_service.py`

这是 FAISS 知识库服务。

关键点在 `do_search()`：

```python
retriever = get_Retriever("ensemble").from_vectorstore(
    vs,
    top_k=top_k,
    score_threshold=score_threshold,
)
docs = retriever.get_relevant_documents(query)
```

这说明：

- FAISS 服务自己不直接写 BM25 + KNN。
- 它只是拿到 FAISS vectorstore。
- 然后把 vectorstore 交给 `ensemble` 检索器。

### 4.4 `file_rag/utils.py`

这是 retriever 注册表。

```python
Retrivals = {
    "milvusvectorstore": MilvusVectorstoreRetrieverService,
    "vectorstore": VectorstoreRetrieverService,
    "ensemble": EnsembleRetrieverService,
}
```

所以：

```python
get_Retriever("ensemble")
```

实际返回的是：

```python
EnsembleRetrieverService
```

### 4.5 `ensemble.py`

这是最核心的文件。

它构造三样东西：

1. KNN / 向量检索器：

```python
faiss_retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": score_threshold, "k": top_k},
)
```

2. BM25 检索器：

```python
docs = list(vectorstore.docstore._dict.values())
bm25_retriever = BM25Retriever.from_documents(
    docs,
    preprocess_func=jieba.lcut_for_search,
)
bm25_retriever.k = top_k
```

3. 融合检索器：

```python
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, faiss_retriever],
    weights=[0.5, 0.5],
)
```

也就是：

```text
BM25 关键词检索
  +
FAISS KNN 向量检索
  +
EnsembleRetriever 加权融合
```

## 5. BM25 是什么

BM25 是关键词检索排序算法，可以理解为 TF-IDF 的改进版。

它主要考虑：

- 查询词在文档中出现多少次。
- 查询词是否足够稀有。
- 文档长度是否过长。

它擅长：

- 精确关键词。
- 专有名词。
- 编号。
- 人名、地名、术语。

它不擅长：

- 同义词。
- 改写表达。
- 字面不匹配但语义相近的问题。

所以 RAG 里经常把它和 KNN 向量检索结合：

```text
BM25 负责关键词精确命中
KNN 负责语义相似召回
```

## 6. 不同 retriever 的理解

可以把 retriever 理解成“检索算法/检索策略的封装”。

在这个项目里：

```text
vectorstore       -> 纯向量检索
milvusvectorstore -> Milvus 向量检索适配
ensemble          -> BM25 + KNN 混合检索
```

它们都有类似接口：

```python
retriever.get_relevant_documents(query)
```

业务层只调用统一接口，具体算法由选择哪个 retriever 决定。

## 7. 自己实现时重点参考

如果你想自己写一个 BM25 + KNN 混合检索，优先参考：

1. `ensemble.py`
   - 学怎么构造 BM25、KNN 和融合器。

2. `faiss_kb_service.py`
   - 学怎么把向量库接入业务检索链路。

3. `file_rag/utils.py`
   - 学怎么通过注册表切换不同检索策略。

最小实现思路：

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
import jieba

def build_hybrid_retriever(vectorstore, top_k=5, score_threshold=0.5):
    knn = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"score_threshold": score_threshold, "k": top_k},
    )

    docs = list(vectorstore.docstore._dict.values())
    bm25 = BM25Retriever.from_documents(
        docs,
        preprocess_func=jieba.lcut_for_search,
    )
    bm25.k = top_k

    return EnsembleRetriever(
        retrievers=[bm25, knn],
        weights=[0.5, 0.5],
    )
```

## 8. 需要注意

当前项目中：

- FAISS 知识库走 `ensemble`，也就是 BM25 + KNN。
- Milvus 知识库走 `milvusvectorstore`，主要是向量检索。
- 临时文件对话 `file_chat.py` 直接走 FAISS 向量检索，不走 `ensemble.py`。
