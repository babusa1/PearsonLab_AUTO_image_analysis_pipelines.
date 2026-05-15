#!/usr/bin/env python
"""
Pearson Lab — CBF Analysis Entry Point (run_cbf.py)
===================================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Main script you execute to run the full Goal 1 CBF pipeline. Parses command-line
arguments (or config.yaml), then delegates to ``pearson_cbf.cli`` and
``pearson_cbf.pipeline``.

Example
-------
::

    python run_cbf.py --input "D:\\videos" --fps 150 --pixel-um 0.162 --no-prompt
"""

from pearson_cbf.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
