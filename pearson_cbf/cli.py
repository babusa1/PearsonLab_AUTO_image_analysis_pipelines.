"""
Command-line interface (CLI) for the CBF pipeline
================================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Parses user input from the terminal (or ``config.yaml``), builds a ``CBFConfig``
object with validated paths and microscope settings, and starts ``run_pipeline``.

Functions
---------
build_parser      — define all ``--input``, ``--fps``, etc. flags
resolve_config    — merge CLI args + YAML into ``CBFConfig``
main              — entry point; returns exit code 0 (success) or 1 (error)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from pearson_cbf.config import CBFConfig, load_config_yaml
from pearson_cbf.pipeline import run_pipeline

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for ``run_cbf.py``."""
    parser = argparse.ArgumentParser(
        prog="run_cbf",
        description="Pearson Lab Pipeline 1 — Cilia Beat Frequency (Goal 1, Q1a–Q1d)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (12 videos in one folder):
  python run_cbf.py --input "D:\\data\\cilia_videos" --fps 150 --pixel-um 0.162
  python run_cbf.py --config config.yaml
  python run_cbf.py --input ./fiji_processed/aligned_videos --fps 150 --pixel-um 0.162 --no-prompt
        """,
    )
    parser.add_argument("--config", "-c", type=Path, help="YAML config file")
    parser.add_argument("--input", "-i", type=Path, help="Folder with .tif videos or .csv profiles")
    parser.add_argument(
        "--output", "-o", type=Path, help="Results folder (default: <input>/results/goal1)"
    )
    parser.add_argument("--fps", type=float, help="Microscope frame rate (Hz)")
    parser.add_argument("--pixel-um", type=float, help="Pixel size (µm/pixel)")
    parser.add_argument("--mode", choices=("tiff", "csv"), default=None, help="Input type")
    parser.add_argument("--freq-min", type=float, default=10.0, help="FFT search min (Hz)")
    parser.add_argument("--freq-max", type=float, default=40.0, help="FFT search max (Hz)")
    parser.add_argument(
        "--sliding-window",
        type=int,
        default=None,
        help="FreQ: smooth power spectrum (Jeong default 2)",
    )
    parser.add_argument(
        "--local-sd-filter",
        type=float,
        default=None,
        help="FreQ: local SD peak threshold (Jeong default 3.0; 0=off)",
    )
    parser.add_argument("--recursive", action="store_true", help="Search subfolders for files")
    parser.add_argument("--no-reuse-rois", action="store_true", help="Force re-draw all ROIs")
    parser.add_argument(
        "--no-interactive", action="store_true", help="Fail if ROIs missing (batch re-run)"
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Require --input, --fps, --pixel-um (no dialogs)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    return parser


def _pick_folder_dialog() -> Path:
    """Open a folder picker dialog (requires display / tkinter)."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    chosen = filedialog.askdirectory(title="Select folder with TIFF videos")
    root.destroy()
    if not chosen:
        raise SystemExit("No folder selected.")
    return Path(chosen).resolve()


def _prompt_float(label: str) -> float:
    """Prompt until the user enters a valid number."""
    while True:
        raw = input(f"{label}: ").strip()
        try:
            return float(raw)
        except ValueError:
            print("  Enter a number.")


def resolve_config(args: argparse.Namespace) -> CBFConfig:
    """
    Build ``CBFConfig`` from CLI arguments and/or YAML file.

    CLI flags override YAML values when both are provided.
    """
    if args.config:
        cfg = load_config_yaml(args.config)
        if args.input:
            cfg.input_dir = args.input.resolve()
        if args.output:
            cfg.output_dir = args.output.resolve()
        if args.fps is not None:
            cfg.fps = args.fps
        if args.pixel_um is not None:
            cfg.pixel_um = args.pixel_um
        if args.sliding_window is not None:
            cfg.sliding_window = args.sliding_window
        if args.local_sd_filter is not None:
            cfg.local_sd_filter = args.local_sd_filter
        if args.mode is not None:
            cfg.input_mode = args.mode
        return cfg

    # Interactive path: folder dialog + prompts unless --no-prompt
    input_dir = args.input
    if input_dir is None:
        if args.no_prompt:
            raise SystemExit("Error: --input is required with --no-prompt")
        input_dir = _pick_folder_dialog()
    else:
        input_dir = input_dir.resolve()

    output_dir = (args.output or input_dir / "results" / "goal1").resolve()

    fps = args.fps
    pixel_um = args.pixel_um
    if fps is None:
        if args.no_prompt:
            raise SystemExit("Error: --fps is required with --no-prompt")
        fps = _prompt_float("Microscope frame rate (fps)")
    if pixel_um is None:
        if args.no_prompt:
            raise SystemExit("Error: --pixel-um is required with --no-prompt")
        pixel_um = _prompt_float("Pixel size (µm/pixel)")

    return CBFConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        fps=fps,
        pixel_um=pixel_um,
        input_mode=args.mode or "tiff",
        freq_min_hz=args.freq_min,
        freq_max_hz=args.freq_max,
        reuse_saved_rois=not args.no_reuse_rois,
        interactive_roi=not args.no_interactive,
        non_interactive=args.no_prompt,
        sliding_window=args.sliding_window if args.sliding_window is not None else 2,
        local_sd_filter=args.local_sd_filter if args.local_sd_filter is not None else 3.0,
    )


def main(argv: list[str] | None = None) -> int:
    """
    Run the CBF pipeline from the command line.

    Returns
    -------
    int
        0 on success, 1 on failure.
    """
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    try:
        cfg = resolve_config(args)
        run_pipeline(cfg, recursive=args.recursive)
    except Exception as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
