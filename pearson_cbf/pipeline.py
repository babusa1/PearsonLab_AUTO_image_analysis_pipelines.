"""
End-to-end CBF analysis pipeline orchestration
==============================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Coordinates the full Goal 1 workflow:

1. Discover input files (.tif or .csv)
2. For each video: load data → get ROIs → FFT → store ``CBFResult``
3. Export ``cbf_all_rois.csv`` and summary statistics
4. Generate Q1a–Q1d figures and ``run_manifest.json``

This is the main module called by ``pearson_cbf.cli.main()``.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

from pearson_cbf.config import CBFConfig, save_run_manifest
from pearson_cbf.genotype import infer_genotype
from pearson_cbf.io_loaders import discover_files, load_intensity_csv, load_tif_stack
from pearson_cbf.models import CBFResult, ROI
from pearson_cbf.plots import make_summary_figures, plot_roi_analysis
from pearson_cbf.roi_select import select_rois_interactive
from pearson_cbf.roi_store import load_rois, save_rois
from pearson_cbf.signal_fft import compute_cbf, extract_signal_from_stack
from pearson_cbf.statistics import run_statistics

logger = logging.getLogger(__name__)

# Minimum frame rate recommended for FFT-based CBF (Scopulovic et al. 2022)
_MIN_FPS_WARNING = 150.0


def _compute_cbf(signal: np.ndarray, cfg: CBFConfig) -> tuple[float, float, np.ndarray, np.ndarray]:
    """Run FFT CBF estimation using settings from ``cfg``."""
    return compute_cbf(
        signal,
        cfg.fps,
        cfg.freq_min_hz,
        cfg.freq_max_hz,
        sliding_window=cfg.sliding_window,
        local_sd_filter=cfg.local_sd_filter,
        low_power_percent=cfg.low_power_percent,
    )


def results_to_dataframe(results: list[CBFResult], cfg: CBFConfig) -> pd.DataFrame:
    """Convert list of ``CBFResult`` to a pandas DataFrame for CSV export."""
    rows = [
        {
            "file": r.file,
            "genotype": r.genotype,
            "cell_id": r.cell_id,
            "roi_label": r.roi_label,
            "cbf_hz": r.cbf_hz,
            "peak_power": r.peak_power,
            "frames": r.frames,
            "fps": cfg.fps,
            "pixel_um": cfg.pixel_um,
            "freq_min_hz": cfg.freq_min_hz,
            "freq_max_hz": cfg.freq_max_hz,
            "sliding_window": cfg.sliding_window,
            "local_sd_filter": cfg.local_sd_filter,
            "roi_x": r.roi_x,
            "roi_y": r.roi_y,
            "roi_w": r.roi_w,
            "roi_h": r.roi_h,
            "center_x": r.center_x,
            "center_y": r.center_y,
            "source": r.source,
        }
        for r in results
    ]
    return pd.DataFrame(rows)


def _get_rois(
    cfg: CBFConfig,
    video_stem: str,
    first_frame: np.ndarray,
    video_name: str,
) -> list[ROI]:
    """
    Load saved ROIs from JSON or prompt user to draw new ones.

    Raises
    ------
    RuntimeError
        If no saved ROIs and ``interactive_roi`` is False.
    """
    rois: list[ROI] | None = None
    if cfg.reuse_saved_rois:
        rois = load_rois(cfg.output_dir, video_stem)

    if rois is not None:
        logger.info("Loaded %d saved ROI(s) for %s", len(rois), video_name)
        return rois

    if not cfg.interactive_roi:
        raise RuntimeError(
            f"No saved ROIs for {video_name} and interactive_roi=False. "
            "Draw ROIs once, or set interactive_roi: true in config."
        )

    rois = select_rois_interactive(
        first_frame,
        min_roi_span=cfg.min_roi_span,
        rois_per_cell=cfg.rois_per_cell_default,
        video_label=video_name,
    )
    save_rois(cfg.output_dir, video_stem, rois)
    return rois


def process_tiff_file(path: Path, cfg: CBFConfig, results: list[CBFResult]) -> None:
    """
    Analyze one multi-frame TIFF: ROIs → intensity traces → CBF per ROI.

    Appends to ``results`` in place.
    """
    stack = load_tif_stack(path)
    genotype = infer_genotype(path.name)
    first_frame = stack[0]
    rois = _get_rois(cfg, path.stem, first_frame, path.name)

    for roi in rois:
        signal = extract_signal_from_stack(stack, roi)
        cbf_hz, peak_power, freqs, power = _compute_cbf(signal, cfg)
        center_x, center_y = roi.center
        logger.info("  %s (%s): CBF = %.2f Hz", roi.label, roi.cell_id, cbf_hz)

        plot_path = cfg.output_dir / "plots" / f"{path.stem}_{roi.label}_analysis.png"
        plot_roi_analysis(first_frame, signal, freqs, power, cbf_hz, cfg.fps, roi, plot_path)

        results.append(
            CBFResult(
                file=path.name,
                genotype=genotype,
                roi_label=roi.label,
                cell_id=roi.cell_id,
                cbf_hz=cbf_hz,
                peak_power=peak_power,
                frames=int(stack.shape[0]),
                roi_x=roi.x,
                roi_y=roi.y,
                roi_w=roi.w,
                roi_h=roi.h,
                center_x=center_x,
                center_y=center_y,
                source="tiff",
            )
        )


def process_csv_file(path: Path, cfg: CBFConfig, results: list[CBFResult]) -> None:
    """
    Analyze one FIJI Z-axis profile CSV (one ROI per file).

    Cell/ROI labels are parsed from the filename when possible.
    """
    signal = load_intensity_csv(path)
    genotype = infer_genotype(path.name)

    cell_match = re.search(r"cell[_\-]?(\w+)", path.stem, re.I)
    roi_match = re.search(r"roi[_\-]?(\w+)", path.stem, re.I)
    cell_id = f"cell_{cell_match.group(1)}" if cell_match else "cell_1"
    roi_label = f"roi_{roi_match.group(1)}" if roi_match else path.stem

    cbf_hz, peak_power, freqs, power = _compute_cbf(signal, cfg)
    logger.info("  %s: CBF = %.2f Hz", path.name, cbf_hz)

    placeholder_roi = ROI(0, 0, 0, 0, roi_label, cell_id)
    plot_path = cfg.output_dir / "plots" / f"{path.stem}_analysis.png"
    plot_roi_analysis(None, signal, freqs, power, cbf_hz, cfg.fps, placeholder_roi, plot_path)

    results.append(
        CBFResult(
            file=path.name,
            genotype=genotype,
            roi_label=roi_label,
            cell_id=cell_id,
            cbf_hz=cbf_hz,
            peak_power=peak_power,
            frames=len(signal),
            roi_x=0,
            roi_y=0,
            roi_w=0,
            roi_h=0,
            center_x=0.0,
            center_y=0.0,
            source="csv",
        )
    )


def run_pipeline(cfg: CBFConfig, *, recursive: bool = False) -> pd.DataFrame:
    """
    Run full Goal 1 analysis on all files in ``cfg.input_dir``.

    Parameters
    ----------
    cfg
        Validated configuration (paths, fps, FFT settings).
    recursive
        Search subfolders for input files.

    Returns
    -------
    pd.DataFrame
        One row per ROI (same content as ``cbf_all_rois.csv``).

    Raises
    ------
    FileNotFoundError
        No input files found.
    RuntimeError
        No successful ROI analyses.
    """
    cfg.validate()
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    input_files = discover_files(cfg.input_dir, cfg.input_mode, recursive=recursive)
    if not input_files:
        raise FileNotFoundError(
            f"No {cfg.input_mode} files in {cfg.input_dir}. "
            "Check path and file extensions (.tif or .csv)."
        )

    if cfg.fps < _MIN_FPS_WARNING and cfg.input_mode == "tiff":
        logger.warning(
            "FPS=%.1f is below %.0f. Scopulovic et al.: FFT-CBF needs ≥150 fps. "
            "Verify in FIJI: Image → Properties.",
            cfg.fps,
            _MIN_FPS_WARNING,
        )

    save_run_manifest(
        cfg,
        extra={"n_files": len(input_files), "files": [f.name for f in input_files]},
    )

    process_file = process_csv_file if cfg.input_mode == "csv" else process_tiff_file
    all_results: list[CBFResult] = []
    error_messages: list[str] = []

    for index, file_path in enumerate(input_files, start=1):
        logger.info("=" * 60)
        logger.info("Video %d / %d: %s", index, len(input_files), file_path.name)
        try:
            process_file(file_path, cfg, all_results)
        except Exception as exc:
            message = f"{file_path.name}: {exc}"
            logger.error("FAILED — %s", message)
            error_messages.append(message)

    if not all_results:
        raise RuntimeError("No successful analyses.\n" + "\n".join(error_messages))

    results_df = results_to_dataframe(all_results, cfg)
    results_df.to_csv(cfg.output_dir / "cbf_all_rois.csv", index=False)
    results_df[["file", "genotype", "cbf_hz", "frames"]].to_csv(
        cfg.output_dir / "all_cbf_results.csv", index=False
    )

    stats_output = run_statistics(results_df)
    pd.DataFrame([stats_output["summary"]]).to_csv(
        cfg.output_dir / "cbf_statistics.csv", index=False
    )

    if not stats_output.get("synchrony", pd.DataFrame()).empty:
        stats_output["synchrony"].to_csv(cfg.output_dir / "cbf_synchrony.csv", index=False)
    if not stats_output.get("spatial", pd.DataFrame()).empty:
        stats_output["spatial"].to_csv(cfg.output_dir / "cbf_spatial.csv", index=False)

    make_summary_figures(results_df, stats_output, cfg.output_dir)

    if error_messages:
        (cfg.output_dir / "errors.log").write_text("\n".join(error_messages), encoding="utf-8")

    logger.info("Done. Results → %s", cfg.output_dir)
    return results_df
