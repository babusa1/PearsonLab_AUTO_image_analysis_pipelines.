#!/usr/bin/env python
"""
Pearson Lab — CBF Analysis (backward-compatible launcher)
=========================================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Alias for ``run_cbf.py``. Kept so older instructions that reference
``python cbf_analysis.py`` continue to work. Prefer ``run_cbf.py`` for new work.
"""

from pearson_cbf.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
