"""
Pearson Lab CBF — module execution (python -m pearson_cbf)
=========================================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Modified:  2026-05-16
Version:        1.2.0

Allows running the pipeline as::

    python -m pearson_cbf --input <folder> --fps 150 --pixel-um 0.162
"""

from pearson_cbf.cli import main

raise SystemExit(main())
