#!/usr/bin/env python
"""兼容入口：转发到 scripts/analysis/visualize_chunks.py。"""

from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parent / "analysis" / "visualize_chunks.py"),
        run_name="__main__",
    )
