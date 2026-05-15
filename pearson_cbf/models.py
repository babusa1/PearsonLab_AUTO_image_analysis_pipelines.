"""
Data models for CBF analysis
============================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Defines immutable-style dataclasses used across the pipeline:

- ``ROI``       : rectangular region on a video frame (cilia field)
- ``CBFResult`` : one measured CBF value for a single ROI in one file
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ROI:
    """
    Rectangular region of interest over beating cilia.

    Attributes
    ----------
    x, y, w, h : Pixel coordinates and size (width, height)
    label      : Identifier e.g. ``roi_1``
    cell_id    : Multiciliated cell grouping e.g. ``cell_1`` (for Q1c synchrony)
    """

    x: int
    y: int
    w: int
    h: int
    label: str = "roi_1"
    cell_id: str = "cell_1"

    @property
    def center(self) -> tuple[float, float]:
        """Center (x, y) in pixels — used for Q1d spatial distance."""
        return (self.x + self.w / 2.0, self.y + self.h / 2.0)


@dataclass
class CBFResult:
    """
    One CBF measurement from one ROI in one input file.

    Written as one row in ``cbf_all_rois.csv``.
    """

    file: str
    genotype: str
    roi_label: str
    cell_id: str
    cbf_hz: float
    peak_power: float
    frames: int
    roi_x: int
    roi_y: int
    roi_w: int
    roi_h: int
    center_x: float
    center_y: float
    source: str  # "tiff" or "csv"
