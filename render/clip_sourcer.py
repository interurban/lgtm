"""Backward-compatible entry: full network clip sourcing lives in clip_fetch.py."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    cmd = [sys.executable, str(root / "clip_fetch.py")] + sys.argv[1:]
    raise SystemExit(subprocess.call(cmd))
