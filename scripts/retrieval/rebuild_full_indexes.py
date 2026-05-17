#!/usr/bin/env python
"""用完整 chunks 顺序重建 FAISS 和 BM25 索引。"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def find_project_root() -> Path:
    """从脚本位置向上查找项目根目录。"""
    for parent in Path(__file__).resolve().parents:
        if (parent / "src" / "financial_report_rag").exists():
            return parent
    raise RuntimeError("无法定位项目根目录")


ROOT = find_project_root()


def parse_args() -> argparse.Namespace:
    """读取完整索引重建参数。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--chunks",
        default="data/processed/chunks/chunks_boundary.jsonl",
        help="完整 chunk 文件。当前 sample 文件不适合正式评测，请传完整 chunks。",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed/indexes/bge_large_zh_v15",
        help="完整索引输出目录。",
    )
    parser.add_argument("--model", default="models/bge-large-zh-v1.5")
    parser.add_argument(
        "--backend",
        choices=["sentence-transformers", "flagembedding"],
        default="sentence-transformers",
        help="Mac 本地推荐 sentence-transformers，服务器可改为 flagembedding。",
    )
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--limit", type=int, default=0, help="调试时只索引前 N 个 chunk；正式重建保持 0。")
    parser.add_argument("--force-embeddings", action="store_true", help="重新编码 embeddings.npy。")
    parser.add_argument("--no-normalize", action="store_true")
    parser.add_argument("--use-fp16", action="store_true")
    parser.add_argument("--index-types", nargs="+", choices=["flat", "ivf", "hnsw"], default=["flat", "ivf", "hnsw"])
    parser.add_argument("--metric", choices=["ip", "l2"], default="ip")
    parser.add_argument("--ivf-nlist", type=int, default=64)
    parser.add_argument("--ivf-nprobe", type=int, default=8)
    parser.add_argument("--hnsw-m", type=int, default=32)
    parser.add_argument("--hnsw-ef-construction", type=int, default=200)
    parser.add_argument("--hnsw-ef-search", type=int, default=64)
    parser.add_argument("--tokenizer", choices=["jieba", "fallback"], default="jieba")
    parser.add_argument("--include-source", action="store_true", help="把 source 文件名加入 BM25 检索文本。")
    parser.add_argument("--dry-run", action="store_true", help="只打印将要执行的命令，不真正构建索引。")
    return parser.parse_args()


def resolve_path(path_text: str) -> Path:
    """把项目相对路径解析成绝对路径。"""
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


def build_faiss_command(args: argparse.Namespace) -> list[str]:
    """生成 FAISS 重建命令。"""
    command = [
        sys.executable,
        str(ROOT / "scripts" / "retrieval" / "build_faiss_index.py"),
        "--chunks",
        args.chunks,
        "--output-dir",
        args.output_dir,
        "--model",
        args.model,
        "--backend",
        args.backend,
        "--batch-size",
        str(args.batch_size),
        "--max-length",
        str(args.max_length),
        "--limit",
        str(args.limit),
        "--metric",
        args.metric,
        "--ivf-nlist",
        str(args.ivf_nlist),
        "--ivf-nprobe",
        str(args.ivf_nprobe),
        "--hnsw-m",
        str(args.hnsw_m),
        "--hnsw-ef-construction",
        str(args.hnsw_ef_construction),
        "--hnsw-ef-search",
        str(args.hnsw_ef_search),
        "--index-types",
        *args.index_types,
    ]
    if args.force_embeddings:
        command.append("--force-embeddings")
    if args.no_normalize:
        command.append("--no-normalize")
    if args.use_fp16:
        command.append("--use-fp16")
    return command


def build_bm25_command(args: argparse.Namespace) -> list[str]:
    """生成 BM25 重建命令，使用 FAISS 阶段写出的 chunks_meta.jsonl。"""
    chunks_meta = str(Path(args.output_dir) / "chunks_meta.jsonl")
    command = [
        sys.executable,
        str(ROOT / "scripts" / "retrieval" / "build_bm25_index.py"),
        "--chunks-meta",
        chunks_meta,
        "--output-dir",
        args.output_dir,
        "--tokenizer",
        args.tokenizer,
        "--limit",
        str(args.limit),
    ]
    if args.include_source:
        command.append("--include-source")
    return command


def run_command(command: list[str], dry_run: bool) -> None:
    """打印并按需执行一条命令。"""
    print(shlex.join(command))
    if dry_run:
        return
    subprocess.run(command, cwd=ROOT, check=True)


def write_rebuild_manifest(args: argparse.Namespace, faiss_command: list[str], bm25_command: list[str]) -> Path:
    """保存完整索引重建的编排记录。"""
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "rebuild_manifest.json"
    payload = {
        "rebuilt_at": datetime.now().isoformat(timespec="seconds"),
        "chunks": args.chunks,
        "output_dir": args.output_dir,
        "faiss_command": faiss_command,
        "bm25_command": bm25_command,
        "dry_run": args.dry_run,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    """顺序执行 FAISS 与 BM25 索引重建。"""
    args = parse_args()
    chunks_path = resolve_path(args.chunks)
    if not chunks_path.exists() and not args.dry_run:
        raise SystemExit(f"完整 chunks 文件不存在：{display_path(chunks_path)}")

    faiss_command = build_faiss_command(args)
    bm25_command = build_bm25_command(args)

    print("# FAISS")
    run_command(faiss_command, dry_run=args.dry_run)
    print("# BM25")
    run_command(bm25_command, dry_run=args.dry_run)

    if args.dry_run:
        print("dry-run: 没有写入索引。")
        return

    manifest_path = write_rebuild_manifest(args, faiss_command, bm25_command)
    print(f"rebuild_manifest: {display_path(manifest_path)}")


if __name__ == "__main__":
    main()
