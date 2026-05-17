"""基于 rank_bm25 的中文关键词检索。"""

from __future__ import annotations

import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

import numpy as np
from rank_bm25 import BM25Okapi

from .vector_store import SearchResult

TokenizerName = Literal["jieba", "fallback"]

MIXED_TOKEN_RE = re.compile(
    r"[a-zA-Z0-9]+(?:[._/\-][a-zA-Z0-9]+)*|[\u4e00-\u9fff]+|[%]+|[^\s]"
)
CHINESE_RE = re.compile(r"^[\u4e00-\u9fff]+$")


@dataclass
class BM25BuildInfo:
    chunk_count: int
    token_count: int
    tokenizer: str
    include_source: bool


class BM25Store:
    """保存 BM25 语料、分词结果，并提供关键词检索。"""

    def __init__(
        self,
        chunks: list[dict],
        tokenized_corpus: list[list[str]],
        tokenizer: TokenizerName = "jieba",
        include_source: bool = False,
    ):
        """初始化 BM25 索引对象。"""
        if len(chunks) != len(tokenized_corpus):
            raise ValueError("chunks 和 tokenized_corpus 数量必须一致")
        if not chunks:
            raise ValueError("BM25 语料不能为空")
        self.chunks = chunks
        self.tokenized_corpus = tokenized_corpus
        self.tokenizer = tokenizer
        self.include_source = include_source
        self.bm25 = BM25Okapi(tokenized_corpus)

    @classmethod
    def from_chunks(
        cls,
        chunks: Iterable[dict],
        tokenizer: TokenizerName = "jieba",
        include_source: bool = False,
    ) -> "BM25Store":
        """从 chunk 元数据构建 BM25 检索器。"""
        validate_tokenizer_name(tokenizer)
        rows = [chunk for chunk in chunks if chunk.get("text", "").strip()]
        tokenized = [
            tokenize_for_search(chunk_search_text(chunk, include_source=include_source), tokenizer=tokenizer)
            for chunk in rows
        ]
        return cls(rows, tokenized, tokenizer=tokenizer, include_source=include_source)

    def save(self, path: Path) -> None:
        """把 BM25 语料和分词结果保存到磁盘。"""
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "chunks": self.chunks,
            "tokenized_corpus": self.tokenized_corpus,
            "tokenizer": self.tokenizer,
            "include_source": self.include_source,
        }
        with path.open("wb") as f:
            pickle.dump(payload, f)

    @classmethod
    def load(cls, path: Path) -> "BM25Store":
        """从磁盘读取 BM25 索引。"""
        with path.open("rb") as f:
            payload = pickle.load(f)
        return cls(
            payload["chunks"],
            payload["tokenized_corpus"],
            tokenizer=payload.get("tokenizer", "jieba"),
            include_source=payload.get("include_source", False),
        )

    def build_info(self) -> BM25BuildInfo:
        """生成 BM25 索引的登记信息。"""
        token_count = sum(len(tokens) for tokens in self.tokenized_corpus)
        return BM25BuildInfo(
            chunk_count=len(self.chunks),
            token_count=token_count,
            tokenizer=self.tokenizer,
            include_source=self.include_source,
        )

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """执行 BM25 检索并返回排序后的 chunk。"""
        query_tokens = tokenize_for_search(query, tokenizer=self.tokenizer)
        if not query_tokens:
            return []
        scores = np.asarray(self.bm25.get_scores(query_tokens), dtype="float32")
        top_k = max(0, min(top_k, len(scores)))
        if top_k == 0:
            return []
        indices = np.argsort(scores)[::-1][:top_k]
        return [
            SearchResult(score=float(scores[idx]), rank=rank, chunk=self.chunks[int(idx)])
            for rank, idx in enumerate(indices, start=1)
        ]


def chunk_search_text(chunk: dict, include_source: bool = False) -> str:
    """组合一个 chunk 中适合 BM25 检索的文本字段。"""
    metadata = chunk.get("metadata") or {}
    parts = [
        str(metadata.get("title") or ""),
        str(chunk.get("text") or ""),
    ]
    if include_source:
        parts.insert(0, str(chunk.get("source") or ""))
    return "\n".join(part for part in parts if part.strip())


def tokenize_for_search(text: str, tokenizer: TokenizerName = "jieba") -> list[str]:
    """按 Chatchat 思路使用 jieba 搜索分词。"""
    if tokenizer == "jieba":
        try:
            import jieba
        except ImportError as exc:
            raise RuntimeError("未安装 jieba，请先运行 `pip install jieba`。") from exc
        return [token.strip().lower() for token in jieba.lcut_for_search(text) if token.strip()]
    if tokenizer == "fallback":
        return fallback_tokenize(text)
    raise ValueError(f"不支持的 tokenizer：{tokenizer}")


def validate_tokenizer_name(tokenizer: TokenizerName) -> None:
    """检查分词器名称和依赖是否可用。"""
    if tokenizer == "jieba":
        try:
            import jieba  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("未安装 jieba，请先运行 `pip install jieba`。") from exc
        return
    if tokenizer == "fallback":
        return
    raise ValueError(f"不支持的 tokenizer：{tokenizer}")


def fallback_tokenize(text: str) -> list[str]:
    """显式选择 fallback 时，用字符 ngram 处理中文关键词。"""
    tokens: list[str] = []
    for token in MIXED_TOKEN_RE.findall(text.lower()):
        token = token.strip()
        if not token:
            continue
        tokens.append(token)
        if CHINESE_RE.match(token):
            tokens.extend(_ngrams(token, 2))
            tokens.extend(_ngrams(token, 3))
    return tokens


def _ngrams(text: str, n: int) -> list[str]:
    """生成中文短语 ngram，提升未分词环境下的关键词命中率。"""
    if len(text) <= n:
        return []
    return [text[i : i + n] for i in range(len(text) - n + 1)]
