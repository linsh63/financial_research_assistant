"""QAnything 风格的二阶段 rerank 精排。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

import numpy as np

from .hybrid_retriever import HybridSearchResult
from .vector_store import SearchResult

RerankerBackend = Literal["flagembedding", "transformers"]
ScoreActivation = Literal["none", "sigmoid"]


@dataclass
class RerankConfig:
    """保存 reranker 模型和过滤参数。"""

    model_name: str = "BAAI/bge-reranker-v2-m3"
    backend: RerankerBackend = "flagembedding"
    batch_size: int = 8
    max_length: int = 512
    use_fp16: bool = False
    score_activation: ScoreActivation = "none"
    score_threshold: float | None = None
    relative_drop_threshold: float | None = None


@dataclass
class RerankResult:
    """保存 rerank 后的结果和原始召回信息。"""

    score: float
    rank: int
    chunk: dict
    retrieval_score: float
    retrieval_rank: int
    rerank_score: float


class CrossEncoderReranker:
    """用 cross-encoder 对 query 与候选 chunk 做相关性精排。"""

    def __init__(self, config: RerankConfig):
        """按配置加载 reranker 后端。"""
        self.config = config
        if config.backend == "flagembedding":
            self.model = self._load_flag_reranker(config)
            self.tokenizer = None
        elif config.backend == "transformers":
            self.model, self.tokenizer = self._load_transformers_reranker(config)
        else:
            raise ValueError(f"不支持的 reranker backend：{config.backend}")

    def rerank(self, query: str, candidates: list[SearchResult | HybridSearchResult], top_k: int) -> list[RerankResult]:
        """对候选 chunk 精排，并返回 TopK。"""
        if not candidates:
            return []
        passages = [str(candidate.chunk.get("text") or "") for candidate in candidates]
        scores = self.score(query, passages)
        results = [
            RerankResult(
                score=float(score),
                rank=0,
                chunk=candidate.chunk,
                retrieval_score=float(candidate.score),
                retrieval_rank=int(candidate.rank),
                rerank_score=float(score),
            )
            for candidate, score in zip(candidates, scores)
        ]
        results.sort(key=lambda item: item.rerank_score, reverse=True)
        results = self._apply_qanything_filters(results)
        trimmed = results[:top_k]
        for rank, result in enumerate(trimmed, start=1):
            result.rank = rank
        return trimmed

    def score(self, query: str, passages: list[str]) -> list[float]:
        """批量计算 query-passage 相关性分数。"""
        if self.config.backend == "flagembedding":
            return self._score_with_flagembedding(query, passages)
        return self._score_with_transformers(query, passages)

    def _load_flag_reranker(self, config: RerankConfig):
        """加载 FlagEmbedding reranker。"""
        try:
            from FlagEmbedding import FlagReranker
        except ImportError as exc:
            raise RuntimeError("未安装 FlagEmbedding，请先运行 `pip install -r requirements.txt`。") from exc
        return FlagReranker(config.model_name, use_fp16=config.use_fp16)

    def _load_transformers_reranker(self, config: RerankConfig):
        """加载 transformers sequence-classification reranker。"""
        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError("未安装 torch/transformers，请先运行 `pip install -r requirements.txt`。") from exc

        tokenizer = AutoTokenizer.from_pretrained(config.model_name)
        model = AutoModelForSequenceClassification.from_pretrained(config.model_name)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        if config.use_fp16 and device.type == "cuda":
            model.half()
        model.eval()
        return model, tokenizer

    def _score_with_flagembedding(self, query: str, passages: list[str]) -> list[float]:
        """使用 FlagEmbedding 的 compute_score 计算相关性。"""
        pairs = [[query, passage] for passage in passages]
        try:
            scores = self.model.compute_score(
                pairs,
                batch_size=self.config.batch_size,
                max_length=self.config.max_length,
            )
        except TypeError:
            scores = self.model.compute_score(pairs, batch_size=self.config.batch_size)
        return [self._activate_score(float(score)) for score in _as_list(scores)]

    def _score_with_transformers(self, query: str, passages: list[str]) -> list[float]:
        """使用 transformers 直接计算相关性。"""
        import torch

        scores: list[float] = []
        device = next(self.model.parameters()).device
        for start in range(0, len(passages), self.config.batch_size):
            batch_passages = passages[start : start + self.config.batch_size]
            encoded = self.tokenizer(
                [query] * len(batch_passages),
                batch_passages,
                padding=True,
                truncation=True,
                max_length=self.config.max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(device) for key, value in encoded.items()}
            with torch.no_grad():
                logits = self.model(**encoded, return_dict=True).logits
            batch_scores = _logits_to_scores(logits.detach().cpu().numpy())
            scores.extend(self._activate_score(float(score)) for score in batch_scores)
        return scores

    def _activate_score(self, score: float) -> float:
        """按需把原始分数映射到 0-1。"""
        if self.config.score_activation == "sigmoid":
            return 1.0 / (1.0 + math.exp(-score))
        return score

    def _apply_qanything_filters(self, results: list[RerankResult]) -> list[RerankResult]:
        """复刻 QAnything 的绝对阈值和相对分差过滤。"""
        if not results:
            return []

        filtered = results
        if self.config.score_threshold is not None:
            thresholded = [result for result in filtered if result.rerank_score >= self.config.score_threshold]
            if thresholded:
                filtered = thresholded

        if self.config.relative_drop_threshold is not None and len(filtered) > 1:
            best_score = filtered[0].rerank_score
            if best_score != 0:
                kept = [filtered[0]]
                for result in filtered[1:]:
                    relative_drop = (best_score - result.rerank_score) / abs(best_score)
                    if relative_drop > self.config.relative_drop_threshold:
                        break
                    kept.append(result)
                filtered = kept

        return filtered


def _as_list(scores: object) -> list[float]:
    """把不同后端返回的分数统一成 list。"""
    if isinstance(scores, np.ndarray):
        return scores.reshape(-1).astype(float).tolist()
    if isinstance(scores, list):
        return [float(score) for score in scores]
    if isinstance(scores, tuple):
        return [float(score) for score in scores]
    return [float(scores)]


def _logits_to_scores(logits: np.ndarray) -> list[float]:
    """把 sequence-classification logits 转成排序分数。"""
    if logits.ndim == 1:
        return logits.astype(float).tolist()
    if logits.shape[1] == 1:
        return logits[:, 0].astype(float).tolist()
    exp = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs = exp / exp.sum(axis=1, keepdims=True)
    return probs[:, -1].astype(float).tolist()
