"""按问题类型选择检索策略。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .bm25_store import BM25Store
from .embeddings import EmbeddingConfig, FlagEmbeddingModel
from .hybrid_retriever import HybridSearchResult
from .hybrid_retriever import FusionMethod, fuse_results
from .parent_document import ParentDocumentStore, SearchLikeResult, expand_results_to_parents
from .reranker import CrossEncoderReranker, RerankConfig, RerankResult
from .vector_store import SearchResult, load_chunk_metadata, load_faiss_index, search_index


@dataclass
class RoutedRetrievalConfig:
    """保存当前实验采用的任务路由策略。"""

    parent_window_pages: int = 1
    parent_max_chars: int = 0
    fact_top_k: int = 5
    compare_candidate_top_k: int = 20
    compare_top_k: int = 5
    summary_candidate_top_k: int = 50
    summary_top_k: int = 8
    summary_per_source: int = 2


@dataclass
class RoutedRetrieverConfig:
    """保存默认 routed 检索入口需要加载的资源和参数。"""

    index_dir: str = "data/processed/indexes/bge_large_zh_v15"
    index_type: str = "flat"
    bm25_path: str = ""
    embedding_model: str = "models/bge-large-zh-v1.5"
    embedding_backend: str = "sentence-transformers"
    embedding_batch_size: int = 16
    embedding_max_length: int = 512
    normalize_embeddings: bool = True
    use_fp16: bool = False
    reranker_model: str = "models/bge-reranker-v2-m3"
    reranker_backend: str = "transformers"
    reranker_batch_size: int = 2
    reranker_max_length: int = 512
    score_activation: str = "none"
    score_threshold: float | None = None
    relative_drop_threshold: float | None = None
    vector_weight: float = 0.6
    bm25_weight: float = 0.4
    fusion: FusionMethod = "weighted"
    rrf_k: int = 60
    vector_higher_is_better: bool = True


@dataclass
class RoutedRetrievalOutput:
    """保存一次 routed 检索的中间结果和最终结果。"""

    query: str
    question_type: str
    strategy: str
    results: list[SearchLikeResult]
    hybrid_results: list[HybridSearchResult]
    rerank_results: list[RerankResult]


class RoutedRetriever:
    """项目默认检索入口：混合召回、按题型 rerank、父文档回填。"""

    def __init__(
        self,
        config: RoutedRetrieverConfig | None = None,
        route_config: RoutedRetrievalConfig | None = None,
        base_dir: Path | str | None = None,
    ):
        """加载索引、模型和父文档库，供后续多次查询复用。"""
        self.config = config or RoutedRetrieverConfig()
        self.route_config = route_config or RoutedRetrievalConfig()
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.index_dir = self._resolve_path(self.config.index_dir)
        self.bm25_path = self._resolve_path(self.config.bm25_path) if self.config.bm25_path else self.index_dir / "bm25.pkl"
        self.manifest = load_index_manifest(self.index_dir)
        self.metadata = load_chunk_metadata(self.index_dir / "chunks_meta.jsonl")
        self.embedder = self._load_embedder()
        self.index = load_faiss_index(self.index_dir / f"faiss_{self.config.index_type}.index")
        self.bm25_store = BM25Store.load(self.bm25_path)
        self.parent_store = ParentDocumentStore(self.metadata)
        self._reranker: CrossEncoderReranker | None = None

    def retrieve(self, query: str, question_type: str = "fact") -> RoutedRetrievalOutput:
        """执行一次 routed 检索，返回最终结果和关键中间结果。"""
        candidate_top_k = max_candidate_top_k(self.route_config)
        vector_results = self.vector_search(query, top_k=candidate_top_k)
        bm25_results = self.bm25_search(query, top_k=candidate_top_k)
        hybrid_results = self.hybrid_search(vector_results, bm25_results, top_k=candidate_top_k)
        rerank_results = self.compare_rerank(query, question_type, hybrid_results)
        final_results = route_results(
            question_type,
            hybrid_results,
            rerank_results,
            parent_store=self.parent_store,
            config=self.route_config,
        )
        return RoutedRetrievalOutput(
            query=query,
            question_type=normalize_question_type(question_type),
            strategy=strategy_name(question_type, self.route_config),
            results=final_results,
            hybrid_results=hybrid_results,
            rerank_results=rerank_results,
        )

    def vector_search(self, query: str, top_k: int) -> list[SearchResult]:
        """执行单条 query 的 FAISS 向量检索。"""
        query_vector = self.embedder.encode_queries([query])
        return search_index(self.index, self.metadata, query_vector, top_k=top_k)

    def bm25_search(self, query: str, top_k: int) -> list[SearchResult]:
        """执行单条 query 的 BM25 检索。"""
        return self.bm25_store.search(query, top_k=top_k)

    def hybrid_search(
        self,
        vector_results: list[SearchResult],
        bm25_results: list[SearchResult],
        top_k: int,
    ) -> list[HybridSearchResult]:
        """融合向量与 BM25 候选。"""
        return fuse_results(
            vector_results,
            bm25_results,
            top_k=top_k,
            vector_weight=self.config.vector_weight,
            bm25_weight=self.config.bm25_weight,
            method=self.config.fusion,
            vector_higher_is_better=self.config.vector_higher_is_better,
            rrf_k=self.config.rrf_k,
        )

    def compare_rerank(
        self,
        query: str,
        question_type: str,
        hybrid_results: list[HybridSearchResult],
    ) -> list[RerankResult]:
        """仅对 compare 问题执行二阶段 rerank。"""
        if normalize_question_type(question_type) != "compare":
            return []
        return self.reranker.rerank(
            query,
            hybrid_results[: self.route_config.compare_candidate_top_k],
            top_k=self.route_config.compare_top_k,
        )

    @property
    def reranker(self) -> CrossEncoderReranker:
        """懒加载 reranker，避免 fact/summary 查询无谓加载大模型。"""
        if self._reranker is None:
            self._reranker = CrossEncoderReranker(
                RerankConfig(
                    model_name=self._resolve_model_name(self.config.reranker_model),
                    backend=self.config.reranker_backend,
                    batch_size=self.config.reranker_batch_size,
                    max_length=self.config.reranker_max_length,
                    use_fp16=self.config.use_fp16,
                    score_activation=self.config.score_activation,
                    score_threshold=self.config.score_threshold,
                    relative_drop_threshold=self.config.relative_drop_threshold,
                )
            )
        return self._reranker

    def _load_embedder(self) -> FlagEmbeddingModel:
        """根据索引 manifest 优先恢复 embedding 配置。"""
        model_name = self.manifest.get("model", self.config.embedding_model)
        config = EmbeddingConfig(
            model_name=self._resolve_model_name(str(model_name)),
            backend=self.manifest.get("backend", self.config.embedding_backend),
            batch_size=self.config.embedding_batch_size,
            max_length=self.manifest.get("max_length", self.config.embedding_max_length),
            normalize=self.manifest.get("normalize", self.config.normalize_embeddings),
            use_fp16=self.manifest.get("use_fp16", self.config.use_fp16),
        )
        return FlagEmbeddingModel(config)

    def _resolve_path(self, path_text: str) -> Path:
        """把项目相对路径转成绝对路径。"""
        path = Path(path_text)
        if path.is_absolute():
            return path
        return self.base_dir / path

    def _resolve_model_name(self, model_name: str) -> str:
        """本地模型路径转绝对路径，Hub 模型名保持不变。"""
        path = Path(model_name).expanduser()
        if path.is_absolute() or model_name.startswith((".", "~", "models/")):
            return str(self._resolve_path(str(path)))
        candidate = self.base_dir / model_name
        if candidate.exists():
            return str(candidate)
        return model_name


def route_results(
    question_type: str,
    hybrid_results: list[HybridSearchResult],
    rerank_results: list[RerankResult],
    parent_store: ParentDocumentStore,
    config: RoutedRetrievalConfig,
) -> list[SearchLikeResult]:
    """根据问题类型返回最终检索结果。"""
    question_type = normalize_question_type(question_type)
    if question_type == "compare":
        selected: list[SearchLikeResult] = rerank_results[: config.compare_top_k]
    elif question_type == "summary":
        selected = select_source_diverse(
            hybrid_results[: config.summary_candidate_top_k],
            top_k=config.summary_top_k,
            per_source=config.summary_per_source,
        )
    else:
        selected = hybrid_results[: config.fact_top_k]

    return expand_results_to_parents(
        selected,
        parent_store=parent_store,
        mode="window",
        window_pages=config.parent_window_pages,
        max_chars=config.parent_max_chars,
        top_k=None,
    )


def select_source_diverse(
    results: list[HybridSearchResult],
    top_k: int,
    per_source: int = 1,
) -> list[HybridSearchResult]:
    """优先保留更多来源文档，适合汇总型多文档问题。"""
    selected: list[HybridSearchResult] = []
    source_counts: dict[str, int] = {}
    used_chunks: set[str] = set()

    for result in results:
        source = result_source(result)
        chunk_id = str(result.chunk.get("chunk_id") or "")
        if chunk_id and chunk_id in used_chunks:
            continue
        if source_counts.get(source, 0) >= per_source:
            continue
        selected.append(result)
        source_counts[source] = source_counts.get(source, 0) + 1
        if chunk_id:
            used_chunks.add(chunk_id)
        if len(selected) >= top_k:
            break

    if len(selected) < top_k:
        for result in results:
            chunk_id = str(result.chunk.get("chunk_id") or "")
            if chunk_id and chunk_id in used_chunks:
                continue
            selected.append(result)
            if chunk_id:
                used_chunks.add(chunk_id)
            if len(selected) >= top_k:
                break

    return selected


def result_source(result: SearchLikeResult) -> str:
    """提取结果来源，用于 source-level 去重。"""
    return str(result.chunk.get("source") or result.chunk.get("doc_id") or "")


def max_candidate_top_k(config: RoutedRetrievalConfig) -> int:
    """计算 routed 第一阶段混合召回需要的最大候选数。"""
    return max(config.fact_top_k, config.compare_candidate_top_k, config.summary_candidate_top_k)


def normalize_question_type(question_type: str) -> str:
    """规范化问题类型，未知类型默认按 fact 处理。"""
    normalized = (question_type or "").strip().lower()
    if normalized in {"fact", "compare", "summary"}:
        return normalized
    return "fact"


def strategy_name(question_type: str, config: RoutedRetrievalConfig) -> str:
    """给问题类型返回实际采用的 routed 策略名。"""
    question_type = normalize_question_type(question_type)
    if question_type == "compare":
        return f"hybrid_top{config.compare_candidate_top_k}_rerank_top{config.compare_top_k}_parent_window{config.parent_window_pages}"
    if question_type == "summary":
        return f"hybrid_top{config.summary_candidate_top_k}_source_diverse_top{config.summary_top_k}_parent_window{config.parent_window_pages}"
    return f"hybrid_top{config.fact_top_k}_parent_window{config.parent_window_pages}"


def load_index_manifest(index_dir: Path) -> dict:
    """读取索引构建登记信息。"""
    manifest_path = index_dir / "index_manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))
