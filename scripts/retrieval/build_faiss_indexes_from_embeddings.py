#!/usr/bin/env python
"""从已保存的 embeddings.npy 构建 FAISS 索引。"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np


def find_project_root() -> Path:
    """从脚本位置向上查找项目根目录。"""
    for parent in Path(__file__).resolve().parents:
        if (parent / "src" / "financial_report_rag").exists():
            return parent
    raise RuntimeError("无法定位项目根目录")


ROOT = find_project_root()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from financial_report_rag.retrieval.vector_store import (  # noqa: E402
    FaissIndexConfig,
    build_faiss_index,
    save_faiss_index,
)


def parse_args() -> argparse.Namespace:
    """读取命令行参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embeddings", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--records-path", required=True)
    parser.add_argument(
        "--index-types",
        nargs="+",
        choices=["flat", "ivf", "hnsw"],
        required=True,
    )
    parser.add_argument("--metric", choices=["ip", "l2"], default="ip")
    parser.add_argument("--ivf-nlist", type=int, default=64)
    parser.add_argument("--ivf-nprobe", type=int, default=8)
    parser.add_argument("--hnsw-m", type=int, default=32)
    parser.add_argument("--hnsw-ef-construction", type=int, default=200)
    parser.add_argument("--hnsw-ef-search", type=int, default=64)
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把路径解析成绝对路径。"""
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def display_path(path: Path) -> str:
    """优先用项目相对路径展示文件。"""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> None:
    """执行 FAISS 索引构建并写出记录。"""
    args = parse_args()
    embedding_path = resolve_path(args.embeddings)
    output_dir = resolve_path(args.output_dir)
    records_path = resolve_path(args.records_path)
    vectors = np.load(embedding_path).astype("float32")

    index_records = []
    for index_type in args.index_types:
        index_config = FaissIndexConfig(
            index_type=index_type,
            metric=args.metric,
            ivf_nlist=args.ivf_nlist,
            ivf_nprobe=args.ivf_nprobe,
            hnsw_m=args.hnsw_m,
            hnsw_ef_construction=args.hnsw_ef_construction,
            hnsw_ef_search=args.hnsw_ef_search,
        )
        start_index = time.perf_counter()
        index, info = build_faiss_index(vectors, index_config)
        build_seconds = time.perf_counter() - start_index

        index_path = output_dir / f"faiss_{index_type}.index"
        save_faiss_index(index, index_path)
        index_records.append(
            {
                "index_type": info.index_type,
                "path": display_path(index_path),
                "dimension": info.dimension,
                "ntotal": info.ntotal,
                "metric": info.metric,
                "parameters": info.parameters,
                "build_seconds": round(build_seconds, 4),
                "file_size_mb": round(index_path.stat().st_size / 1024 / 1024, 4),
            }
        )

    records_path.write_text(json.dumps(index_records, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
