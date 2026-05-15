#!/usr/bin/env python
"""
Backward-compatible launcher for Pipeline 1 (CBF).

Prefer:
  python run_cbf.py --input YOUR_FOLDER --fps 150 --pixel-um 0.162
"""

from pearson_cbf.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
