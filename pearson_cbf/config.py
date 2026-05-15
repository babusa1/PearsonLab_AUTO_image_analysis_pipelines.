"""
Configuration and run manifest for CBF analysis
================================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Defines ``CBFConfig`` (all analysis parameters in one dataclass), loads settings
from ``config.yaml``, and writes ``run_manifest.json`` for lab notebook /
reproducibility. Parameters must stay identical across WT and DS samples.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from pearson_cbf.__about__ import __author__, __email__, __version__

# Jeong et al. 2022 FreQ defaults — do not change between genotypes mid-study
DEFAULT_FREQ_MIN_HZ = 10.0
DEFAULT_FREQ_MAX_HZ = 40.0
DEFAULT_SLIDING_WINDOW = 2
DEFAULT_LOCAL_SD_FILTER = 3.0
DEFAULT_LOW_POWER_PERCENT = 20.0


@dataclass
class CBFConfig:
    """
    Complete configuration for one CBF analysis run.

    Attributes
    ----------
    input_dir, output_dir : Paths to data and results
    fps, pixel_um         : Microscope calibration (must match FIJI metadata)
    input_mode            : ``"tiff"`` (video stacks) or ``"csv"`` (FIJI Z-profiles)
    freq_min_hz, freq_max_hz : FFT search band for CBF peak (Hz)
    sliding_window, local_sd_filter : FreQ-aligned FFT post-processing
    reuse_saved_rois      : If True, load ROI JSON instead of redrawing
    interactive_roi       : If True, open matplotlib ROI selector when needed
    """

    input_dir: Path
    output_dir: Path
    fps: float
    pixel_um: float
    input_mode: str = "tiff"
    freq_min_hz: float = DEFAULT_FREQ_MIN_HZ
    freq_max_hz: float = DEFAULT_FREQ_MAX_HZ
    sliding_window: int = DEFAULT_SLIDING_WINDOW
    local_sd_filter: float = DEFAULT_LOCAL_SD_FILTER
    low_power_percent: float = DEFAULT_LOW_POWER_PERCENT
    reuse_saved_rois: bool = True
    interactive_roi: bool = True
    min_roi_span: int = 5
    rois_per_cell_default: int = 2
    skip_cell_prompt: bool = False
    non_interactive: bool = False

    def validate(self) -> None:
        """Raise ``ValueError`` or ``FileNotFoundError`` if settings are invalid."""
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
        if self.sliding_window < 1:
            raise ValueError("sliding_window must be >= 1")
        if not 0 < self.low_power_percent <= 100:
            raise ValueError("low_power_percent must be in (0, 100]")

    def to_manifest(self) -> dict[str, Any]:
        """Serialize config + metadata for ``run_manifest.json``."""
        params = asdict(self)
        params["input_dir"] = str(self.input_dir)
        params["output_dir"] = str(self.output_dir)
        return {
            "pipeline": "pearson_cbf_goal1",
            "version": __version__,
            "author": __author__,
            "email": __email__,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "parameters": params,
        }


def load_config_yaml(path: Path) -> CBFConfig:
    """
    Load ``CBFConfig`` from a YAML file (see ``config.example.yaml``).

    Parameters
    ----------
    path
        Path to ``config.yaml``.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    paths = raw.get("paths", {})
    microscope = raw.get("microscope", {})
    analysis = raw.get("analysis", {})
    roi = raw.get("roi", {})

    input_dir = Path(paths["input_dir"]).expanduser().resolve()
    output_dir = Path(
        paths.get("output_dir", input_dir / "results" / "goal1")
    ).expanduser().resolve()

    return CBFConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        fps=float(microscope["fps"]),
        pixel_um=float(microscope["pixel_um"]),
        input_mode=str(analysis.get("input_mode", "tiff")),
        freq_min_hz=float(analysis.get("freq_min_hz", DEFAULT_FREQ_MIN_HZ)),
        freq_max_hz=float(analysis.get("freq_max_hz", DEFAULT_FREQ_MAX_HZ)),
        sliding_window=int(analysis.get("sliding_window", DEFAULT_SLIDING_WINDOW)),
        local_sd_filter=float(analysis.get("local_sd_filter", DEFAULT_LOCAL_SD_FILTER)),
        low_power_percent=float(analysis.get("low_power_percent", DEFAULT_LOW_POWER_PERCENT)),
        reuse_saved_rois=bool(roi.get("reuse_saved_rois", True)),
        interactive_roi=bool(roi.get("interactive_roi", True)),
        min_roi_span=int(roi.get("min_roi_span", 5)),
        rois_per_cell_default=int(roi.get("rois_per_cell_default", 2)),
        skip_cell_prompt=bool(roi.get("skip_cell_prompt", False)),
        non_interactive=bool(analysis.get("non_interactive", False)),
    )


def save_run_manifest(cfg: CBFConfig, extra: dict[str, Any] | None = None) -> Path:
    """
    Write ``run_manifest.json`` under ``cfg.output_dir``.

    Returns path to the written file.
    """
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = cfg.to_manifest()
    if extra:
        manifest["run"] = extra

    out_path = cfg.output_dir / "run_manifest.json"

    def _json_safe(obj: Any) -> Any:
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, dict):
            return {k: _json_safe(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_json_safe(v) for v in obj]
        return obj

    out_path.write_text(json.dumps(_json_safe(manifest), indent=2), encoding="utf-8")
    return out_path
