"""
Genotype classification from filenames
======================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Infers experimental group (WT, DS, or Unknown) from video/CSV filenames so
results can be grouped automatically without a separate metadata spreadsheet.
"""

from __future__ import annotations

import re


def infer_genotype(filename: str) -> str:
    """
    Classify genotype from a filename.

    Parameters
    ----------
    filename
        Base name or full path (only the name is used).

    Returns
    -------
    str
        ``"WT"``, ``"DS"``, or ``"Unknown"``.

    Examples
    --------
    >>> infer_genotype("wt_mouse3_20250615_aligned.tif")
    'WT'
    >>> infer_genotype("DS_M2_video.tif")
    'DS'
    """
    name = filename.lower()

    # Word-boundary aware tokens reduce false positives
    if re.search(r"(^|[_\-.])wt([_\-.]|$)", name) or "wildtype" in name or "wild_type" in name:
        return "WT"
    if re.search(r"(^|[_\-.])ds([_\-.]|$)", name) or ("down" in name and "syndrome" in name):
        return "DS"
    if "wt" in name:
        return "WT"
    if "ds" in name:
        return "DS"
    return "Unknown"
