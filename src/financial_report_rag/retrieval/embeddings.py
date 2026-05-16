"""向量检索 baseline 使用的 Embedding 封装。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np


@dataclass
class EmbeddingConfig:
    model_name: str = "BAAI/bge-large-zh-v1.5"
    backend: str = "sentence-transformers"
    batch_size: int = 16
    max_length: int = 512
    normalize: bool = True
    use_fp16: bool = False
    query_instruction: str = "为这个句子生成表示以用于检索相关文章："


class FlagEmbeddingModel:
    """FlagEmbedding 的轻量适配层，隔离不同版本的 API 差异。"""

    def __init__(self, config: EmbeddingConfig):
        """初始化 embedding 模型。"""
        self.config = config
        self.backend = _normalize_backend(config.backend)
        self.model = self._load_model(config)

    def _load_model(self, config: EmbeddingConfig):
        """按后端加载 embedding 模型实例。"""
        if self.backend == "sentence-transformers":
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "未安装 sentence-transformers，请先运行 `pip install -r requirements.txt`。"
                ) from exc
            return SentenceTransformer(config.model_name)

        try:
            from FlagEmbedding import FlagModel
        except ImportError as exc:
            raise RuntimeError(
                "未安装 FlagEmbedding，请先运行 `pip install -r requirements.txt`。"
            ) from exc

        try:
            return FlagModel(
                config.model_name,
                query_instruction_for_retrieval=config.query_instruction,
                use_fp16=config.use_fp16,
            )
        except TypeError:
            return FlagModel(config.model_name, use_fp16=config.use_fp16)

    def encode_passages(self, texts: Iterable[str]) -> np.ndarray:
        """编码文档 chunk 文本。"""
        return self._encode(list(texts), is_query=False)

    def encode_queries(self, texts: Iterable[str]) -> np.ndarray:
        """编码用户查询文本。"""
        return self._encode(list(texts), is_query=True)

    def _encode(self, texts: List[str], is_query: bool) -> np.ndarray:
        """根据文本类型调用合适的编码接口。"""
        if not texts:
            return np.zeros((0, 0), dtype="float32")

        if self.backend == "sentence-transformers":
            encoded_texts = texts
            if is_query and self.config.query_instruction:
                encoded_texts = [self.config.query_instruction + text for text in texts]
            vectors = self.model.encode(
                encoded_texts,
                batch_size=self.config.batch_size,
                normalize_embeddings=self.config.normalize,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            return np.asarray(vectors, dtype="float32")

        method_names = ["encode_queries", "encode"] if is_query else ["encode_corpus", "encode"]
        last_error = None
        for method_name in method_names:
            method = getattr(self.model, method_name, None)
            if method is None:
                continue
            try:
                vectors = method(
                    texts,
                    batch_size=self.config.batch_size,
                    max_length=self.config.max_length,
                    normalize_embeddings=self.config.normalize,
                )
                return np.asarray(vectors, dtype="float32")
            except TypeError as exc:
                last_error = exc
                try:
                    vectors = method(texts, batch_size=self.config.batch_size)
                    vectors = np.asarray(vectors, dtype="float32")
                    if self.config.normalize:
                        vectors = _normalize(vectors)
                    return vectors
                except TypeError as fallback_exc:
                    last_error = fallback_exc

        raise RuntimeError("当前 FlagEmbedding 版本无法完成文本编码。") from last_error


def _normalize(vectors: np.ndarray) -> np.ndarray:
    """对向量做 L2 归一化。"""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


def _normalize_backend(backend: str) -> str:
    """规范化 embedding 后端名称。"""
    normalized = backend.lower().replace("_", "-")
    if normalized in {"sentence-transformers", "sentence-transformer", "st"}:
        return "sentence-transformers"
    if normalized in {"flagembedding", "flag-embedding", "flag"}:
        return "flagembedding"
    raise ValueError(f"不支持的 embedding backend：{backend}")
