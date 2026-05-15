"""Persist ROI definitions for reproducible re-runs."""

from __future__ import annotations

import json
from pathlib import Path

from pearson_cbf.models import ROI


def rois_path(output_dir: Path, stem: str) -> Path:
    return output_dir / "rois" / f"{stem}_rois.json"


def save_rois(output_dir: Path, stem: str, rois: list[ROI]) -> Path:
    path = rois_path(output_dir, stem)
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
    path.write_text(json.dumps(payload, indent=2))
    return path


def load_rois(output_dir: Path, stem: str) -> list[ROI] | None:
    path = rois_path(output_dir, stem)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return [
        ROI(
            x=int(d["x"]),
            y=int(d["y"]),
            w=int(d["w"]),
            h=int(d["h"]),
            label=str(d.get("label", f"roi_{i + 1}")),
            cell_id=str(d.get("cell_id", "cell_1")),
        )
        for i, d in enumerate(data)
    ]
