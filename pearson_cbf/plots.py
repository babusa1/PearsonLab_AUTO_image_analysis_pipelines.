"""Diagnostic and summary figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from pearson_cbf.models import ROI


def plot_roi_analysis(
    first_frame,
    signal,
    freqs,
    power,
    cbf: float,
    fps: float,
    roi: ROI,
    save_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))

    if first_frame is not None:
        axes[0].imshow(first_frame, cmap="gray")
        axes[0].add_patch(
            plt.Rectangle(
                (roi.x, roi.y), roi.w, roi.h, fill=False, edgecolor="lime", linewidth=2
            )
        )
        axes[0].set_title(f"{roi.label} ({roi.cell_id})")
    else:
        axes[0].text(0.5, 0.5, "CSV input", ha="center", va="center")
    axes[0].axis("off")

    t = np.arange(len(signal)) / fps
    axes[1].plot(t, signal, color="steelblue", lw=0.8)
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
    summary = stats_out.get("summary", {})

    fig, ax = plt.subplots(figsize=(6, 5))
    for geno, color, pos in [("WT", "#4C72B0", 0), ("DS", "#DD8452", 1)]:
        sub = df[df["genotype"] == geno]
        if sub.empty:
            continue
        jitter = np.random.normal(pos, 0.06, len(sub))
        ax.scatter(jitter, sub["cbf_hz"], s=60, alpha=0.85, label=geno, color=color)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["WT", "DS"])
    ax.set_ylabel("CBF (Hz)")
    p = summary.get("q1a_mannwhitney_p")
    title = "Q1a: CBF by genotype"
    if p is not None:
        title += f"\nMann-Whitney p = {p:.4g}"
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / "goal1a_cbf_comparison.png", dpi=200)
    plt.close(fig)

    per_file = stats_out.get("per_file")
    if per_file is not None and not per_file.empty:
        fig, ax = plt.subplots(figsize=(6, 5))
        for geno, color in [("WT", "#4C72B0"), ("DS", "#DD8452")]:
            sub = per_file[per_file["genotype"] == geno]
            if not sub.empty:
                ax.scatter([geno] * len(sub), sub["cbf_sd"], s=70, color=color)
        lev_p = summary.get("q1b_levene_p")
        t = "Q1b: Within-video CBF variability"
        if lev_p is not None:
            t += f"\nLevene p = {lev_p:.4g}"
        ax.set_title(t)
        ax.set_ylabel("SD of CBF (Hz)")
        fig.tight_layout()
        fig.savefig(output_dir / "goal1b_variability.png", dpi=200)
        plt.close(fig)

    sync = stats_out.get("synchrony")
    if sync is not None and not sync.empty:
        fig, ax = plt.subplots(figsize=(6, 5))
        for geno, color in [("WT", "#4C72B0"), ("DS", "#DD8452")]:
            sub = sync[sync["genotype"] == geno]
            if not sub.empty:
                ax.scatter([geno] * len(sub), sub["mean_abs_cbf_diff_hz"], s=70, color=color)
        ax.set_title("Q1c: Within-cell synchrony (lower = better)")
        ax.set_ylabel("Mean |ΔCBF| within cell (Hz)")
        fig.tight_layout()
        fig.savefig(output_dir / "goal1c_synchrony.png", dpi=200)
        plt.close(fig)

    dist_all, diff_all, colors = [], [], []
    for _, grp in df.groupby("file"):
        if len(grp) < 2:
            continue
        centers = grp[["center_x", "center_y"]].to_numpy()
        cbfs = grp["cbf_hz"].to_numpy()
        c = "#4C72B0" if grp["genotype"].iloc[0] == "WT" else "#DD8452"
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                dist_all.append(float(np.linalg.norm(centers[i] - centers[j])))
                diff_all.append(abs(cbfs[i] - cbfs[j]))
                colors.append(c)
    if dist_all:
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.scatter(dist_all, diff_all, c=colors, alpha=0.6, s=40)
        if len(dist_all) >= 3:
            r, p = stats.pearsonr(dist_all, diff_all)
            z = np.polyfit(dist_all, diff_all, 1)
            xs = np.linspace(min(dist_all), max(dist_all), 50)
            ax.plot(xs, np.poly1d(z)(xs), "k--", lw=1)
            ax.set_title(f"Q1d: Distance vs |ΔCBF| (r={r:.3f}, p={p:.4g})")
        ax.set_xlabel("ROI distance (pixels)")
        ax.set_ylabel("|ΔCBF| (Hz)")
        fig.tight_layout()
        fig.savefig(output_dir / "goal1d_spatial.png", dpi=200)
        plt.close(fig)
