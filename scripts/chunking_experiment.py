#!/usr/bin/env python
"""兼容入口：转发到 scripts/experiments/chunking_experiment.py。"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).resolve().parent / "experiments" / "chunking_experiment.py"), run_name="__main__")
