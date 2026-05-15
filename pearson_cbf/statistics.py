"""
Goal 1 statistical tests (Q1a–Q1d)
==================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Computes project statistics comparing WT vs DS:

- Q1a : Mann-Whitney + Welch t-test on CBF (Hz)
- Q1b : Levene test on per-video SD of CBF
- Q1c : Within-cell mean |ΔCBF| between ROIs on the same cell
- Q1d : Per-video Pearson correlation of ROI distance vs |ΔCBF|

Note: Final publication analysis should also use R ``lme4`` for nested
mice/cells (see lab protocol); these tests operate at the ROI level.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def run_statistics(df: pd.DataFrame) -> dict:
    """
    Run Q1a–Q1d and return tables for CSV export and plotting.

    Parameters
    ----------
    df
        Output of ``results_to_dataframe`` (one row per ROI).

    Returns
    -------
    dict
        Keys: ``summary``, ``per_file``, ``synchrony``, ``spatial`` (DataFrames
        may be empty if insufficient data).
    """
    summary: dict = {}

    wt_cbf = df.loc[df["genotype"] == "WT", "cbf_hz"].dropna()
    ds_cbf = df.loc[df["genotype"] == "DS", "cbf_hz"].dropna()

    # --- Q1a: mean CBF ---
    if len(wt_cbf) >= 2 and len(ds_cbf) >= 2:
        _, p_mann_whitney = stats.mannwhitneyu(wt_cbf, ds_cbf, alternative="two-sided")
        _, p_welch = stats.ttest_ind(wt_cbf, ds_cbf, equal_var=False)
        summary.update(
            {
                "q1a_wt_mean_hz": float(wt_cbf.mean()),
                "q1a_ds_mean_hz": float(ds_cbf.mean()),
                "q1a_wt_sd_hz": float(wt_cbf.std(ddof=1)),
                "q1a_ds_sd_hz": float(ds_cbf.std(ddof=1)),
                "q1a_mannwhitney_p": float(p_mann_whitney),
                "q1a_ttest_p": float(p_welch),
            }
        )
        logger.info(
            "Q1a WT %.3f±%.3f Hz vs DS %.3f±%.3f Hz | Mann-Whitney p=%.4g",
            wt_cbf.mean(),
            wt_cbf.std(ddof=1),
            ds_cbf.mean(),
            ds_cbf.std(ddof=1),
            p_mann_whitney,
        )

    # --- Q1b: variability (SD of CBF across ROIs within each video) ---
    per_file = df.groupby(["file", "genotype"], as_index=False)["cbf_hz"].agg(
        cbf_mean="mean", cbf_sd="std", n_rois="count"
    )
    per_file["cbf_sd"] = per_file["cbf_sd"].fillna(0.0)

    wt_sd = per_file.loc[per_file["genotype"] == "WT", "cbf_sd"]
    ds_sd = per_file.loc[per_file["genotype"] == "DS", "cbf_sd"]
    if len(wt_sd) >= 2 and len(ds_sd) >= 2:
        levene_result = stats.levene(wt_sd, ds_sd)
        summary.update(
            {
                "q1b_wt_sd_of_cbf": float(wt_sd.mean()),
                "q1b_ds_sd_of_cbf": float(ds_sd.mean()),
                "q1b_levene_p": float(levene_result.pvalue),
            }
        )
        logger.info("Q1b variability Levene p=%.4g", levene_result.pvalue)

    # --- Q1c: within-cell synchrony ---
    synchrony_rows: list[dict] = []
    for (file_name, cell_id), group in df.groupby(["file", "cell_id"]):
        cbf_values = group["cbf_hz"].to_numpy()
        if len(cbf_values) < 2:
            continue
        pairwise_diffs = [
            abs(a - b)
            for i, a in enumerate(cbf_values)
            for b in cbf_values[i + 1 :]
        ]
        synchrony_rows.append(
            {
                "file": file_name,
                "cell_id": cell_id,
                "genotype": group["genotype"].iloc[0],
                "mean_abs_cbf_diff_hz": float(np.mean(pairwise_diffs)),
                "n_rois": len(cbf_values),
            }
        )
    synchrony_df = pd.DataFrame(synchrony_rows)

    if not synchrony_df.empty:
        wt_sync = synchrony_df.loc[synchrony_df["genotype"] == "WT", "mean_abs_cbf_diff_hz"]
        ds_sync = synchrony_df.loc[synchrony_df["genotype"] == "DS", "mean_abs_cbf_diff_hz"]
        if len(wt_sync) >= 1 and len(ds_sync) >= 1:
            _, p_sync = stats.mannwhitneyu(wt_sync, ds_sync, alternative="two-sided")
            summary.update(
                {
                    "q1c_wt_mean_pairwise_diff_hz": float(wt_sync.mean()),
                    "q1c_ds_mean_pairwise_diff_hz": float(ds_sync.mean()),
                    "q1c_mannwhitney_p": float(p_sync),
                }
            )
            logger.info(
                "Q1c within-cell |ΔCBF| WT %.3f vs DS %.3f | p=%.4g",
                wt_sync.mean(),
                ds_sync.mean(),
                p_sync,
            )
    else:
        logger.warning("Q1c skipped: need ≥2 ROIs on same cell (use 's' key when drawing ROIs)")

    # --- Q1d: spatial correlation per file ---
    spatial_rows: list[dict] = []
    for file_name, group in df.groupby("file"):
        if len(group) < 2:
            continue
        centers = group[["center_x", "center_y"]].to_numpy()
        cbfs = group["cbf_hz"].to_numpy()
        distances: list[float] = []
        cbf_diffs: list[float] = []
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                distances.append(float(np.linalg.norm(centers[i] - centers[j])))
                cbf_diffs.append(abs(cbfs[i] - cbfs[j]))
        if len(distances) >= 3:
            r_value, p_value = stats.pearsonr(distances, cbf_diffs)
            spatial_rows.append(
                {
                    "file": file_name,
                    "genotype": group["genotype"].iloc[0],
                    "pearson_r": float(r_value),
                    "p_value": float(p_value),
                    "n_pairs": len(distances),
                }
            )
    spatial_df = pd.DataFrame(spatial_rows)

    return {
        "summary": summary,
        "per_file": per_file,
        "synchrony": synchrony_df,
        "spatial": spatial_df,
    }
