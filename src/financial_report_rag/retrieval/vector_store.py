"""基于 FAISS 的稠密向量检索。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import faiss
import numpy as np

from ..utils import read_jsonl, write_jsonl


@dataclass
class SearchResult:
    score: float
    rank: int
    chunk: dict


def build_flat_index(vectors: np.ndarray) -> faiss.Index:
    """用归一化向量构建 Inner Product Flat 索引。"""
    if vectors.ndim != 2 or vectors.shape[0] == 0:
        raise ValueError("vectors 必须是非空二维数组")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors.astype("float32"))
    return index


def save_faiss_index(index: faiss.Index, path: Path) -> None:
    """把 FAISS 索引保存到磁盘。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(path))


def load_faiss_index(path: Path) -> faiss.Index:
    """从磁盘读取 FAISS 索引。"""
    return faiss.read_index(str(path))


def save_chunk_metadata(chunks: Iterable[dict], path: Path) -> int:
    """保存与向量顺序一致的 chunk 元数据。"""
    return write_jsonl(path, chunks)


def load_chunk_metadata(path: Path) -> List[dict]:
    """读取与索引配套的 chunk 元数据。"""
    return list(read_jsonl(path))


def search_index(index: faiss.Index, metadata: list[dict], query_vector: np.ndarray, top_k: int) -> list[SearchResult]:
    """执行向量检索并返回带元数据的结果。"""
    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)
    scores, ids = index.search(query_vector.astype("float32"), top_k)

    results: list[SearchResult] = []
    for rank, (score, idx) in enumerate(zip(scores[0], ids[0]), start=1):
        if idx < 0 or idx >= len(metadata):
            continue
        results.append(SearchResult(score=float(score), rank=rank, chunk=metadata[idx]))
    return results
