"""
Figure generation for CBF analysis
==================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Creates matplotlib figures:

- Per-ROI diagnostics (frame + intensity trace + FFT spectrum)
- Summary panels for Q1a–Q1d (``goal1a_*.png`` … ``goal1d_*.png``)
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from pearson_cbf.models import ROI


def plot_roi_analysis(
    first_frame,
    signal: np.ndarray,
    freqs: np.ndarray,
    power: np.ndarray,
    cbf: float,
    fps: float,
    roi: ROI,
    save_path: Path,
) -> None:
    """
    Save a 3-panel diagnostic figure for one ROI.

    Panels: (1) frame with ROI box, (2) intensity vs time, (3) FFT with CBF peak.
    """
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

    if first_frame is not None:
        axes[0].imshow(first_frame, cmap="gray")
        axes[0].add_patch(
            plt.Rectangle(
                (roi.x, roi.y),
                roi.w,
                roi.h,
                fill=False,
                edgecolor="lime",
                linewidth=2,
            )
        )
        axes[0].set_title(f"{roi.label} ({roi.cell_id})")
    else:
        axes[0].text(0.5, 0.5, "CSV input", ha="center", va="center")
    axes[0].axis("off")

    time_axis = np.arange(len(signal)) / fps
    axes[1].plot(time_axis, signal, color="steelblue", lw=0.8)
    axes[1].set_xlabel("Time (s)")
    axes[1].set_ylabel("Intensity (a.u.)")

    axes[2].plot(freqs, power, color="0.35", lw=0.8)
    axes[2].axvline(cbf, color="crimson", ls="--", label=f"CBF = {cbf:.2f} Hz")
    axes[2].set_xlim(0, min(60, float(freqs[-1])))
    axes[2].set_xlabel("Frequency (Hz)")
    axes[2].set_ylabel("|FFT|²")
    axes[2].legend()

    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def make_summary_figures(df: pd.DataFrame, stats_out: dict, output_dir: Path) -> None:
    """
    Write Q1a–Q1d summary PNG files into ``output_dir``.

    Skips panels when the required statistics or data are missing.
    """
    summary = stats_out.get("summary", {})

    # Q1a — CBF by genotype
    fig, ax = plt.subplots(figsize=(6, 5))
    for genotype, color in [("WT", "#4C72B0"), ("DS", "#DD8452")]:
        subset = df[df["genotype"] == genotype]
        if subset.empty:
            continue
        x_pos = 0 if genotype == "WT" else 1
        jitter = np.random.normal(x_pos, 0.06, len(subset))
        ax.scatter(jitter, subset["cbf_hz"], s=60, alpha=0.85, label=genotype, color=color)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["WT", "DS"])
    ax.set_ylabel("CBF (Hz)")
    p_value = summary.get("q1a_mannwhitney_p")
    title = "Q1a: CBF by genotype"
    if p_value is not None:
        title += f"\nMann-Whitney p = {p_value:.4g}"
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "goal1a_cbf_comparison.png", dpi=200)
    plt.close(fig)

    # Q1b — within-video variability
    per_file = stats_out.get("per_file")
    if per_file is not None and not per_file.empty:
        fig, ax = plt.subplots(figsize=(6, 5))
        for genotype, color in [("WT", "#4C72B0"), ("DS", "#DD8452")]:
            subset = per_file[per_file["genotype"] == genotype]
            if not subset.empty:
                ax.scatter([genotype] * len(subset), subset["cbf_sd"], s=70, color=color)
        levene_p = summary.get("q1b_levene_p")
        title = "Q1b: Within-video CBF variability"
        if levene_p is not None:
            title += f"\nLevene p = {levene_p:.4g}"
        ax.set_title(title)
        ax.set_ylabel("SD of CBF (Hz)")
        fig.tight_layout()
        fig.savefig(output_dir / "goal1b_variability.png", dpi=200)
        plt.close(fig)

    # Q1c — within-cell synchrony
    synchrony = stats_out.get("synchrony")
    if synchrony is not None and not synchrony.empty:
        fig, ax = plt.subplots(figsize=(6, 5))
        for genotype, color in [("WT", "#4C72B0"), ("DS", "#DD8452")]:
            subset = synchrony[synchrony["genotype"] == genotype]
            if not subset.empty:
                ax.scatter(
                    [genotype] * len(subset),
                    subset["mean_abs_cbf_diff_hz"],
                    s=70,
                    color=color,
                )
        ax.set_title("Q1c: Within-cell synchrony (lower = better)")
        ax.set_ylabel("Mean |ΔCBF| within cell (Hz)")
        fig.tight_layout()
        fig.savefig(output_dir / "goal1c_synchrony.png", dpi=200)
        plt.close(fig)

    # Q1d — pooled spatial correlation
    distances_all: list[float] = []
    diffs_all: list[float] = []
    point_colors: list[str] = []
    for _, group in df.groupby("file"):
        if len(group) < 2:
            continue
        centers = group[["center_x", "center_y"]].to_numpy()
        cbfs = group["cbf_hz"].to_numpy()
        color = "#4C72B0" if group["genotype"].iloc[0] == "WT" else "#DD8452"
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                distances_all.append(float(np.linalg.norm(centers[i] - centers[j])))
                diffs_all.append(abs(cbfs[i] - cbfs[j]))
                point_colors.append(color)

    if distances_all:
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.scatter(distances_all, diffs_all, c=point_colors, alpha=0.6, s=40)
        if len(distances_all) >= 3:
            r_value, p_value = stats.pearsonr(distances_all, diffs_all)
            fit = np.poly1d(np.polyfit(distances_all, diffs_all, 1))
            x_line = np.linspace(min(distances_all), max(distances_all), 50)
            ax.plot(x_line, fit(x_line), "k--", lw=1)
            ax.set_title(f"Q1d: Distance vs |ΔCBF| (r={r_value:.3f}, p={p_value:.4g})")
        ax.set_xlabel("ROI distance (pixels)")
        ax.set_ylabel("|ΔCBF| (Hz)")
        fig.tight_layout()
        fig.savefig(output_dir / "goal1d_spatial.png", dpi=200)
        plt.close(fig)
