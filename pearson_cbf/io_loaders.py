"""
Input file loading (TIFF stacks and FIJI CSV profiles)
======================================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Discovers input files in a folder and loads them into NumPy arrays:

- Multi-frame ``.tif`` / ``.tiff`` cilia videos → shape ``(T, Y, X)``
- FIJI Z-axis profile ``.csv`` files → 1D intensity vs time

See ``docs/FIJI_ZAXIS_EXPORT.md`` for CSV export instructions.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile


def discover_files(folder: Path, mode: str, recursive: bool = False) -> list[Path]:
    """
    List ``.tif`` or ``.csv`` files in ``folder``.

    Parameters
    ----------
    mode
        ``"tiff"`` or ``"csv"``.
    recursive
        If True, search subdirectories.
    """
    if mode == "csv":
        patterns = ("*.csv", "*.CSV")
    else:
        patterns = ("*.tif", "*.TIF", "*.tiff", "*.TIFF")

    found: list[Path] = []
    for pattern in patterns:
        if recursive:
            found.extend(folder.rglob(pattern))
        else:
            found.extend(folder.glob(pattern))
    return sorted({p.resolve() for p in found})


def load_tif_stack(path: Path) -> np.ndarray:
    """
    Load a microscopy stack as float64 array ``(T, Y, X)``.

    Handles 2D single frames and 4D stacks (collapses extra dims to time).
    """
    stack = tifffile.imread(path)
    if stack.ndim == 2:
        stack = stack[np.newaxis, ...]
    elif stack.ndim == 4:
        stack = stack.reshape(-1, stack.shape[-2], stack.shape[-1])
    if stack.ndim != 3:
        raise ValueError(
            f"Expected 3D stack (T,Y,X), got shape {stack.shape} for {path.name}"
        )
    return stack.astype(np.float64)


def _read_profile_table(path: Path) -> pd.DataFrame:
    """Try comma-, then tab-separated parsing for FIJI exports."""
    last_error: Exception | None = None
    for kwargs in (
        {"sep": ","},
        {"sep": "\t"},
        {"sep": None, "engine": "python"},
    ):
        try:
            df = pd.read_csv(path, comment="#", skipinitialspace=True, **kwargs)
            if df.shape[1] >= 1 and len(df) > 0:
                return df
        except Exception as exc:
            last_error = exc
    raise ValueError(f"Could not parse CSV {path.name}: {last_error}")


def _column_by_aliases(df: pd.DataFrame, aliases: tuple[str, ...]) -> str | None:
    """Match column names case-insensitively."""
    normalized = {re.sub(r"\s+", " ", c.lower().strip()): c for c in df.columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def load_intensity_csv(path: Path) -> np.ndarray:
    """
    Load FIJI Z-axis / Plot Z-axis Profile CSV as a 1D intensity trace.

    Raises
    ------
    ValueError
        If no numeric column or fewer than 8 time points.
    """
    df = _read_profile_table(path)
    df = df.dropna(how="all")

    intensity_col = _column_by_aliases(
        df,
        (
            "mean",
            "gray value",
            "gray_value",
            "gray value (arbitrary units)",
            "intensity",
            "avg",
            "average",
            "value",
        ),
    )

    if intensity_col is not None:
        series = pd.to_numeric(df[intensity_col], errors="coerce")
    else:
        numeric = df.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
        if numeric.shape[1] == 0:
            raise ValueError(
                f"No numeric intensity column in {path.name}. "
                "Re-export from FIJI: Plot Z-axis Profile → Save As CSV."
            )
        if numeric.shape[1] == 1:
            series = numeric.iloc[:, 0]
        else:
            # Prefer column that is not a simple frame index 0,1,2,...
            best_col = numeric.shape[1] - 1
            for col_idx in range(numeric.shape[1]):
                col = numeric.iloc[:, col_idx].dropna().to_numpy()
                if len(col) < 3:
                    continue
                diffs = np.diff(col)
                if np.allclose(diffs, 1.0):
                    continue
                best_col = col_idx
            series = numeric.iloc[:, best_col]

    series = series.dropna()
    if len(series) < 8:
        raise ValueError(
            f"{path.name}: only {len(series)} frames in profile (need ≥8). "
            "Check ROI and stack length in FIJI."
        )
    return series.to_numpy(dtype=np.float64)
