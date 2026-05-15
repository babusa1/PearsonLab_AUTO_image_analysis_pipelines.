"""
Persist ROI definitions (JSON) for reproducible re-runs
=======================================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Saves and loads ROI rectangles to ``results/goal1/rois/<video_stem>_rois.json``
so a second pipeline run uses the same regions without redrawing (lab
reproducibility requirement).
"""

from __future__ import annotations

import json
from pathlib import Path

from pearson_cbf.models import ROI


def rois_path(output_dir: Path, video_stem: str) -> Path:
    """Path to the JSON file for one video's ROIs."""
    return output_dir / "rois" / f"{video_stem}_rois.json"


def save_rois(output_dir: Path, video_stem: str, rois: list[ROI]) -> Path:
    """
    Write ROI list to JSON.

    Returns
    -------
    Path
        File that was written.
    """
    path = rois_path(output_dir, video_stem)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "x": r.x,
            "y": r.y,
            "w": r.w,
            "h": r.h,
            "label": r.label,
            "cell_id": r.cell_id,
        }
        for r in rois
    ]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_rois(output_dir: Path, video_stem: str) -> list[ROI] | None:
    """
    Load ROIs from JSON if the file exists.

    Returns
    -------
    list[ROI] or None
        ``None`` if no saved file for this video.
    """
    path = rois_path(output_dir, video_stem)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        ROI(
            x=int(entry["x"]),
            y=int(entry["y"]),
            w=int(entry["w"]),
            h=int(entry["h"]),
            label=str(entry.get("label", f"roi_{index + 1}")),
            cell_id=str(entry.get("cell_id", "cell_1")),
        )
        for index, entry in enumerate(data)
    ]
