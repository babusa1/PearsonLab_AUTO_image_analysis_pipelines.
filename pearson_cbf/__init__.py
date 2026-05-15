"""
Pearson Lab — Pipeline 1: Cilia Beat Frequency (CBF) Analysis Package
======================================================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Institution:    University of Colorado Boulder
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Package overview
----------------
``pearson_cbf`` quantifies cilia beat frequency (CBF) from high-speed microscopy
videos or FIJI-exported intensity traces. It compares wild-type (WT) vs Down
syndrome (DS) samples and answers Goal 1 questions Q1a–Q1d (mean CBF, variability,
within-cell synchrony, spatial coordination).

Typical usage::

    from pearson_cbf import CBFConfig, run_pipeline

Or from the command line::

    python run_cbf.py --input <folder> --fps 150 --pixel-um 0.162
"""

from pearson_cbf.__about__ import (
    __author__,
    __date_created__,
    __date_modified__,
    __email__,
    __institution__,
    __project__,
    __version__,
)
from pearson_cbf.config import CBFConfig
from pearson_cbf.pipeline import run_pipeline

__all__ = [
    "CBFConfig",
    "run_pipeline",
    "__author__",
    "__email__",
    "__version__",
    "__date_created__",
    "__date_modified__",
    "__project__",
    "__institution__",
]
