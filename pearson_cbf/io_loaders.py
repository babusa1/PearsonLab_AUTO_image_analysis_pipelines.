"""Load TIFF stacks and FIJI intensity CSVs."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import tifffile


def discover_files(folder: Path, mode: str, recursive: bool = False) -> list[Path]:
    if mode == "csv":
        patterns = ["*.csv", "*.CSV"]
    else:
        patterns = ["*.tif", "*.TIF", "*.tiff", "*.TIFF"]

    files: list[Path] = []
    for pat in patterns:
        if recursive:
            files.extend(folder.rglob(pat))
        else:
            files.extend(folder.glob(pat))
    return sorted({f.resolve() for f in files})


def load_tif_stack(path: Path) -> np.ndarray:
    """Load multi-frame stack as (T, Y, X) float64."""
    stack = tifffile.imread(path)
    if stack.ndim == 2:
        stack = stack[np.newaxis, ...]
    elif stack.ndim == 4:
        stack = stack.reshape(-1, stack.shape[-2], stack.shape[-1])
    if stack.ndim != 3:
        raise ValueError(f"Expected 3D stack (T,Y,X), got shape {stack.shape} for {path.name}")
    return stack.astype(np.float64)


def _read_profile_table(path: Path) -> pd.DataFrame:
    """Read FIJI-exported profile CSV (comma or tab separated)."""
    last_err: Exception | None = None
    for kwargs in (
        {"sep": ","},
        {"sep": "\t"},
        {"sep": None, "engine": "python"},
    ):
        try:
            df = pd.read_csv(
                path,
                comment="#",
                skipinitialspace=True,
                **kwargs,
            )
            if df.shape[1] >= 1 and len(df) > 0:
                return df
        except Exception as exc:
            last_err = exc
    raise ValueError(f"Could not parse CSV {path.name}: {last_err}")


def _column_by_aliases(df: pd.DataFrame, aliases: tuple[str, ...]) -> str | None:
    cols = {re.sub(r"\s+", " ", c.lower().strip()): c for c in df.columns}
    for alias in aliases:
        if alias in cols:
            return cols[alias]
    return None


def load_intensity_csv(path: Path) -> np.ndarray:
    """
    Load FIJI Z-axis profile / Plot Z-axis Profile CSV.

    Supported layouts
    -----------------
    - Columns ``Time`` + ``Mean`` (or ``Gray Value``, ``Intensity``)
    - Single ``Mean`` column
    - Two numeric columns → uses the non-monotonic index column as intensity
    - First row may be headers (standard FIJI export)

    Export in FIJI
    --------------
    1. Draw ROI on aligned stack
    2. Image → Stacks → Plot Z-axis Profile
    3. List → Save As… → ``*_zprofile.csv``
    4. One file per ROI; name with ``wt``/``ds``, ``cell``, ``roi`` if possible
    """
    df = _read_profile_table(path)

    # Drop all-non-numeric rows (FIJI sometimes adds blanks)
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
        numeric = df.apply(pd.to_numeric, errors="coerce")
        numeric = numeric.dropna(axis=1, how="all")
        if numeric.shape[1] == 0:
            raise ValueError(
                f"No numeric intensity column in {path.name}. "
                "Re-export from FIJI: Plot Z-axis Profile → Save As CSV."
            )
        if numeric.shape[1] == 1:
            series = numeric.iloc[:, 0]
        else:
            # Time + Mean: pick column that is not a simple 0..N index
            best = numeric.shape[1] - 1
            for i in range(numeric.shape[1]):
                col = numeric.iloc[:, i].dropna().to_numpy()
                if len(col) < 3:
                    continue
                diffs = np.diff(col)
                if np.allclose(diffs, 1.0) or np.allclose(diffs, col[0] if len(col) > 1 else 1.0):
                    continue
                best = i
            series = numeric.iloc[:, best]

    series = series.dropna()
    if len(series) < 8:
        raise ValueError(
            f"{path.name}: only {len(series)} frames in profile (need ≥8). "
            "Check ROI and stack length in FIJI."
        )
    return series.to_numpy(dtype=np.float64)
