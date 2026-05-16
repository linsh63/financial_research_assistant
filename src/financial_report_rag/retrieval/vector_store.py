"""基于 FAISS 的稠密向量检索。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import numpy as np

from ..utils import read_jsonl, write_jsonl


@dataclass
class SearchResult:
    score: float
    rank: int
    chunk: dict


@dataclass
class FaissIndexConfig:
    index_type: str = "flat"
    metric: str = "ip"
    ivf_nlist: int = 64
    ivf_nprobe: int = 8
    hnsw_m: int = 32
    hnsw_ef_construction: int = 200
    hnsw_ef_search: int = 64


@dataclass
class FaissBuildInfo:
    index_type: str
    dimension: int
    ntotal: int
    metric: str
    parameters: dict


def validate_vectors(vectors: np.ndarray) -> np.ndarray:
    """检查向量矩阵并转成 FAISS 需要的 float32。"""
    if vectors.ndim != 2 or vectors.shape[0] == 0:
        raise ValueError("vectors 必须是非空二维数组")
    return np.ascontiguousarray(vectors.astype("float32"))


def load_faiss():
    """延迟导入 FAISS，避免在 Mac 上先导入 FAISS 再加载 torch 导致进程退出。"""
    import faiss

    return faiss


def metric_type(metric: str) -> int:
    """把配置里的 metric 名称转成 FAISS 常量。"""
    faiss = load_faiss()
    metric = metric.lower()
    if metric in {"ip", "inner_product", "cosine"}:
        return faiss.METRIC_INNER_PRODUCT
    if metric in {"l2", "euclidean"}:
        return faiss.METRIC_L2
    raise ValueError(f"不支持的 FAISS metric：{metric}")


def build_flat_index(vectors: np.ndarray, metric: str = "ip") -> faiss.Index:
    """构建暴力精确检索索引，适合 baseline 和小数据。"""
    faiss = load_faiss()
    vectors = validate_vectors(vectors)
    if metric_type(metric) == faiss.METRIC_INNER_PRODUCT:
        index = faiss.IndexFlatIP(vectors.shape[1])
    else:
        index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)
    return index


def effective_ivf_nlist(vector_count: int, requested_nlist: int) -> int:
    """根据样本量调整 IVF 聚类数，避免小样本训练失败。"""
    if vector_count <= 1:
        return 1
    requested_nlist = max(1, min(requested_nlist, vector_count))
    if vector_count < requested_nlist * 39:
        return max(1, min(requested_nlist, vector_count // 39 or 1))
    return requested_nlist


def build_ivf_flat_index(
    vectors: np.ndarray,
    nlist: int = 64,
    nprobe: int = 8,
    metric: str = "ip",
) -> tuple[faiss.Index, int]:
    """构建 IVF Flat 索引，适合更大语料下做速度和召回折中。"""
    faiss = load_faiss()
    vectors = validate_vectors(vectors)
    faiss_metric = metric_type(metric)
    dimension = vectors.shape[1]
    actual_nlist = effective_ivf_nlist(vectors.shape[0], nlist)
    quantizer = faiss.IndexFlatIP(dimension) if faiss_metric == faiss.METRIC_INNER_PRODUCT else faiss.IndexFlatL2(dimension)
    index = faiss.IndexIVFFlat(quantizer, dimension, actual_nlist, faiss_metric)
    index.train(vectors)
    index.add(vectors)
    index.nprobe = max(1, min(nprobe, actual_nlist))
    return index, actual_nlist


def build_hnsw_index(
    vectors: np.ndarray,
    m: int = 32,
    ef_construction: int = 200,
    ef_search: int = 64,
    metric: str = "ip",
) -> faiss.Index:
    """构建 HNSW 近似索引，适合低延迟召回实验。"""
    faiss = load_faiss()
    vectors = validate_vectors(vectors)
    index = faiss.IndexHNSWFlat(vectors.shape[1], m, metric_type(metric))
    index.hnsw.efConstruction = ef_construction
    index.hnsw.efSearch = ef_search
    index.add(vectors)
    return index


def build_faiss_index(vectors: np.ndarray, config: FaissIndexConfig) -> tuple[faiss.Index, FaissBuildInfo]:
    """按配置构建 Flat / IVF / HNSW 中的一种 FAISS 索引。"""
    index_type = config.index_type.lower()
    vectors = validate_vectors(vectors)
    parameters: dict = {}

    if index_type == "flat":
        index = build_flat_index(vectors, metric=config.metric)
    elif index_type == "ivf":
        index, actual_nlist = build_ivf_flat_index(
            vectors,
            nlist=config.ivf_nlist,
            nprobe=config.ivf_nprobe,
            metric=config.metric,
        )
        parameters = {"nlist": actual_nlist, "requested_nlist": config.ivf_nlist, "nprobe": index.nprobe}
    elif index_type == "hnsw":
        index = build_hnsw_index(
            vectors,
            m=config.hnsw_m,
            ef_construction=config.hnsw_ef_construction,
            ef_search=config.hnsw_ef_search,
            metric=config.metric,
        )
        parameters = {
            "m": config.hnsw_m,
            "ef_construction": config.hnsw_ef_construction,
            "ef_search": config.hnsw_ef_search,
        }
    else:
        raise ValueError(f"不支持的索引类型：{config.index_type}")

    info = FaissBuildInfo(
        index_type=index_type,
        dimension=vectors.shape[1],
        ntotal=index.ntotal,
        metric=config.metric,
        parameters=parameters,
    )
    return index, info


def save_faiss_index(index: faiss.Index, path: Path) -> None:
    """把 FAISS 索引保存到磁盘。"""
    faiss = load_faiss()
    path.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(path))


def load_faiss_index(path: Path) -> faiss.Index:
    """从磁盘读取 FAISS 索引。"""
    faiss = load_faiss()
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
