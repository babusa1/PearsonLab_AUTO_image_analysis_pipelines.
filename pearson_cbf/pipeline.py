"""End-to-end CBF analysis pipeline."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

from pearson_cbf.config import CBFConfig, save_run_manifest
from pearson_cbf.genotype import infer_genotype
from pearson_cbf.io_loaders import discover_files, load_intensity_csv, load_tif_stack
from pearson_cbf.models import CBFResult, ROI
from pearson_cbf.plots import make_summary_figures, plot_roi_analysis
from pearson_cbf.roi_select import select_rois_interactive
from pearson_cbf.roi_store import load_rois, save_rois
from pearson_cbf.signal_fft import extract_signal_from_stack
from pearson_cbf.statistics import run_statistics

logger = logging.getLogger(__name__)


def _compute_cbf(signal: np.ndarray, cfg: CBFConfig):
    from pearson_cbf.signal_fft import compute_cbf

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
    stem: str,
    first_frame,
    video_name: str,
) -> list[ROI]:
    rois = None
    if cfg.reuse_saved_rois:
        rois = load_rois(cfg.output_dir, stem)

    if rois is not None:
        logger.info("Loaded %d saved ROI(s) for %s", len(rois), video_name)
        return rois

    if not cfg.interactive_roi:
        raise RuntimeError(
            f"No saved ROIs for {video_name} and interactive_roi=False. "
            "Draw ROIs once with default settings, or set interactive_roi: true."
        )

    rois = select_rois_interactive(
        first_frame,
        min_roi_span=cfg.min_roi_span,
        rois_per_cell=cfg.rois_per_cell_default,
        video_label=video_name,
    )
    save_rois(cfg.output_dir, stem, rois)
    return rois


def process_tiff_file(path: Path, cfg: CBFConfig, results: list[CBFResult]) -> None:
    stack = load_tif_stack(path)
    genotype = infer_genotype(path.name)
    first = stack[0]
    rois = _get_rois(cfg, path.stem, first, path.name)

    for roi in rois:
        signal = extract_signal_from_stack(stack, roi)
        cbf, peak_pwr, freqs, power = _compute_cbf(signal, cfg)
        cx, cy = roi.center
        logger.info("  %s (%s): CBF = %.2f Hz", roi.label, roi.cell_id, cbf)

        plot_path = cfg.output_dir / "plots" / f"{path.stem}_{roi.label}_analysis.png"
        plot_roi_analysis(first, signal, freqs, power, cbf, cfg.fps, roi, plot_path)

        results.append(
            CBFResult(
                file=path.name,
                genotype=genotype,
                roi_label=roi.label,
                cell_id=roi.cell_id,
                cbf_hz=cbf,
                peak_power=peak_pwr,
                frames=int(stack.shape[0]),
                roi_x=roi.x,
                roi_y=roi.y,
                roi_w=roi.w,
                roi_h=roi.h,
                center_x=cx,
                center_y=cy,
                source="tiff",
            )
        )


def process_csv_file(path: Path, cfg: CBFConfig, results: list[CBFResult]) -> None:
    signal = load_intensity_csv(path)
    genotype = infer_genotype(path.name)
    cell_m = re.search(r"cell[_\-]?(\w+)", path.stem, re.I)
    roi_m = re.search(r"roi[_\-]?(\w+)", path.stem, re.I)
    cell_id = f"cell_{cell_m.group(1)}" if cell_m else "cell_1"
    roi_label = f"roi_{roi_m.group(1)}" if roi_m else path.stem

    cbf, peak_pwr, freqs, power = _compute_cbf(signal, cfg)
    logger.info("  %s: CBF = %.2f Hz", path.name, cbf)

    roi = ROI(0, 0, 0, 0, roi_label, cell_id)
    plot_path = cfg.output_dir / "plots" / f"{path.stem}_analysis.png"
    plot_roi_analysis(None, signal, freqs, power, cbf, cfg.fps, roi, plot_path)

    results.append(
        CBFResult(
            file=path.name,
            genotype=genotype,
            roi_label=roi_label,
            cell_id=cell_id,
            cbf_hz=cbf,
            peak_power=peak_pwr,
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
    Run full Goal 1 analysis on all files in input_dir.

    Returns
    -------
    DataFrame with one row per ROI (cbf_all_rois.csv content).
    """
    cfg.validate()
    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    files = discover_files(cfg.input_dir, cfg.input_mode, recursive=recursive)
    if not files:
        raise FileNotFoundError(
            f"No {cfg.input_mode} files in {cfg.input_dir}. "
            "Check path and that filenames end in .tif or .csv."
        )

    if cfg.fps < 150 and cfg.input_mode == "tiff":
        logger.warning(
            "FPS=%.1f is below 150. Scopulovic et al.: FFT-CBF needs ≥150 fps. "
            "Verify in FIJI: Image → Properties.",
            cfg.fps,
        )

    save_run_manifest(
        cfg,
        extra={"n_files": len(files), "files": [f.name for f in files]},
    )

    processor = process_csv_file if cfg.input_mode == "csv" else process_tiff_file
    results: list[CBFResult] = []
    errors: list[str] = []

    for idx, path in enumerate(files, start=1):
        logger.info("=" * 60)
        logger.info("Video %d / %d: %s", idx, len(files), path.name)
        try:
            processor(path, cfg, results)
        except Exception as exc:
            msg = f"{path.name}: {exc}"
            logger.error("FAILED — %s", msg)
            errors.append(msg)

    if not results:
        raise RuntimeError("No successful analyses.\n" + "\n".join(errors))

    df = results_to_dataframe(results, cfg)
    df.to_csv(cfg.output_dir / "cbf_all_rois.csv", index=False)
    df[["file", "genotype", "cbf_hz", "frames"]].to_csv(
        cfg.output_dir / "all_cbf_results.csv", index=False
    )

    stats_out = run_statistics(df)
    pd.DataFrame([stats_out["summary"]]).to_csv(cfg.output_dir / "cbf_statistics.csv", index=False)

    if not stats_out.get("synchrony", pd.DataFrame()).empty:
        stats_out["synchrony"].to_csv(cfg.output_dir / "cbf_synchrony.csv", index=False)
    if not stats_out.get("spatial", pd.DataFrame()).empty:
        stats_out["spatial"].to_csv(cfg.output_dir / "cbf_spatial.csv", index=False)

    make_summary_figures(df, stats_out, cfg.output_dir)

    if errors:
        (cfg.output_dir / "errors.log").write_text("\n".join(errors))

    logger.info("Done. Results → %s", cfg.output_dir)
    return df
