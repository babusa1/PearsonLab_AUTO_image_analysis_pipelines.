"""Data models for CBF analysis."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ROI:
    """Rectangular region over beating cilia."""

    x: int
    y: int
    w: int
    h: int
    label: str = "roi_1"
    cell_id: str = "cell_1"

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.w / 2.0, self.y + self.h / 2.0)


@dataclass
class CBFResult:
    """One ROI measurement from one video or CSV."""

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
    source: str
