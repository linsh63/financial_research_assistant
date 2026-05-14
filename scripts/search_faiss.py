#!/usr/bin/env python
"""兼容入口：转发到 scripts/retrieval/search_faiss.py。"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "retrieval" / "search_faiss.py"), run_name="__main__")
