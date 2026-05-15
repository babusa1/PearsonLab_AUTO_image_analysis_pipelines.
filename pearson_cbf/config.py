"""Configuration loading for CBF pipeline."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CBFConfig:
    """All analysis parameters — keep identical across WT and DS samples."""

    input_dir: Path
    output_dir: Path
    fps: float
    pixel_um: float
    input_mode: str = "tiff"  # "tiff" | "csv"
    freq_min_hz: float = 10.0
    freq_max_hz: float = 40.0
    sliding_window: int = 2
    local_sd_filter: float = 3.0
    low_power_percent: float = 20.0
    reuse_saved_rois: bool = True
    interactive_roi: bool = True
    min_roi_span: int = 5
    rois_per_cell_default: int = 2
    skip_cell_prompt: bool = False
    non_interactive: bool = False

    def validate(self) -> None:
        if not self.input_dir.is_dir():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")
        if self.fps <= 0:
            raise ValueError("fps must be positive")
        if self.pixel_um <= 0:
            raise ValueError("pixel_um must be positive")
        if self.freq_min_hz >= self.freq_max_hz:
            raise ValueError("freq_min_hz must be < freq_max_hz")
        if self.input_mode not in ("tiff", "csv"):
            raise ValueError('input_mode must be "tiff" or "csv"')

    def to_manifest(self) -> dict[str, Any]:
        params = asdict(self)
        params["input_dir"] = str(self.input_dir)
        params["output_dir"] = str(self.output_dir)
        return {
            "pipeline": "pearson_cbf_goal1",
            "version": "1.1.0",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "parameters": params,
        }


def load_config_yaml(path: Path) -> CBFConfig:
    raw = yaml.safe_load(path.read_text())
    paths = raw.get("paths", {})
    microscope = raw.get("microscope", {})
    analysis = raw.get("analysis", {})
    roi = raw.get("roi", {})

    input_dir = Path(paths["input_dir"]).expanduser().resolve()
    output_dir = Path(paths.get("output_dir", input_dir / "results" / "goal1")).expanduser().resolve()

    return CBFConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        fps=float(microscope["fps"]),
        pixel_um=float(microscope["pixel_um"]),
        input_mode=str(analysis.get("input_mode", "tiff")),
        freq_min_hz=float(analysis.get("freq_min_hz", 10.0)),
        freq_max_hz=float(analysis.get("freq_max_hz", 40.0)),
        sliding_window=int(analysis.get("sliding_window", 2)),
        local_sd_filter=float(analysis.get("local_sd_filter", 3.0)),
        low_power_percent=float(analysis.get("low_power_percent", 20.0)),
        reuse_saved_rois=bool(roi.get("reuse_saved_rois", True)),
        interactive_roi=bool(roi.get("interactive_roi", True)),
        min_roi_span=int(roi.get("min_roi_span", 5)),
        rois_per_cell_default=int(roi.get("rois_per_cell_default", 2)),
        skip_cell_prompt=bool(roi.get("skip_cell_prompt", False)),
        non_interactive=bool(analysis.get("non_interactive", False)),
    )


def save_run_manifest(cfg: CBFConfig, extra: dict[str, Any] | None = None) -> Path:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = cfg.to_manifest()
    if extra:
        manifest["run"] = extra
    path = cfg.output_dir / "run_manifest.json"
    # JSON-serialize Paths
    def _fix(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, dict):
            return {k: _fix(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_fix(v) for v in obj]
        return obj

    path.write_text(json.dumps(_fix(manifest), indent=2))
    return path
