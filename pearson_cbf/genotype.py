"""Infer WT / DS from filenames."""

from __future__ import annotations

import re


def infer_genotype(filename: str) -> str:
    """
    Classify genotype from filename.

    Examples that work:
      wt_mouse1_20250601.tif
      DS_M3_aligned.tif
      wildtype_sample2.tif
    """
    name = filename.lower()
    if re.search(r"(^|[_\-.])wt([_\-.]|$)", name) or "wildtype" in name or "wild_type" in name:
        return "WT"
    if re.search(r"(^|[_\-.])ds([_\-.]|$)", name) or ("down" in name and "syndrome" in name):
        return "DS"
    if "wt" in name:
        return "WT"
    if "ds" in name:
        return "DS"
    return "Unknown"
