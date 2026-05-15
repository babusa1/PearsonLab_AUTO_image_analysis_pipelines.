"""Goal 1 statistical tests (Q1a–Q1d)."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def run_statistics(df: pd.DataFrame) -> dict:
    """Compute Q1a–Q1d; log summaries; return tables for export."""
    summary: dict = {}
    wt = df.loc[df["genotype"] == "WT", "cbf_hz"].dropna()
    ds = df.loc[df["genotype"] == "DS", "cbf_hz"].dropna()

    if len(wt) >= 2 and len(ds) >= 2:
        _, p_mw = stats.mannwhitneyu(wt, ds, alternative="two-sided")
        _, p_t = stats.ttest_ind(wt, ds, equal_var=False)
        summary.update(
            {
                "q1a_wt_mean_hz": float(wt.mean()),
                "q1a_ds_mean_hz": float(ds.mean()),
                "q1a_wt_sd_hz": float(wt.std(ddof=1)),
                "q1a_ds_sd_hz": float(ds.std(ddof=1)),
                "q1a_mannwhitney_p": float(p_mw),
                "q1a_ttest_p": float(p_t),
            }
        )
        logger.info("Q1a WT %.3f±%.3f Hz vs DS %.3f±%.3f Hz | Mann-Whitney p=%.4g", wt.mean(), wt.std(ddof=1), ds.mean(), ds.std(ddof=1), p_mw)

    per_file = df.groupby(["file", "genotype"], as_index=False)["cbf_hz"].agg(
        cbf_mean="mean", cbf_sd="std", n_rois="count"
    )
    per_file["cbf_sd"] = per_file["cbf_sd"].fillna(0.0)

    wt_sd = per_file.loc[per_file["genotype"] == "WT", "cbf_sd"]
    ds_sd = per_file.loc[per_file["genotype"] == "DS", "cbf_sd"]
    if len(wt_sd) >= 2 and len(ds_sd) >= 2:
        lev = stats.levene(wt_sd, ds_sd)
        summary.update(
            {
                "q1b_wt_sd_of_cbf": float(wt_sd.mean()),
                "q1b_ds_sd_of_cbf": float(ds_sd.mean()),
                "q1b_levene_p": float(lev.pvalue),
            }
        )
        logger.info("Q1b variability Levene p=%.4g", lev.pvalue)

    sync_rows = []
    for (file, cell_id), grp in df.groupby(["file", "cell_id"]):
        vals = grp["cbf_hz"].to_numpy()
        if len(vals) < 2:
            continue
        diffs = [abs(a - b) for i, a in enumerate(vals) for b in vals[i + 1 :]]
        sync_rows.append(
            {
                "file": file,
                "cell_id": cell_id,
                "genotype": grp["genotype"].iloc[0],
                "mean_abs_cbf_diff_hz": float(np.mean(diffs)),
                "n_rois": len(vals),
            }
        )
    sync_df = pd.DataFrame(sync_rows)

    if not sync_df.empty:
        wt_sync = sync_df.loc[sync_df["genotype"] == "WT", "mean_abs_cbf_diff_hz"]
        ds_sync = sync_df.loc[sync_df["genotype"] == "DS", "mean_abs_cbf_diff_hz"]
        if len(wt_sync) >= 1 and len(ds_sync) >= 1:
            _, p_s = stats.mannwhitneyu(wt_sync, ds_sync, alternative="two-sided")
            summary.update(
                {
                    "q1c_wt_mean_pairwise_diff_hz": float(wt_sync.mean()),
                    "q1c_ds_mean_pairwise_diff_hz": float(ds_sync.mean()),
                    "q1c_mannwhitney_p": float(p_s),
                }
            )
            logger.info("Q1c within-cell |ΔCBF| WT %.3f vs DS %.3f | p=%.4g", wt_sync.mean(), ds_sync.mean(), p_s)
    else:
        logger.warning("Q1c skipped: need ≥2 ROIs on same cell (use 's' key when drawing ROIs)")

    spatial_rows = []
    for file, grp in df.groupby("file"):
        if len(grp) < 2:
            continue
        centers = grp[["center_x", "center_y"]].to_numpy()
        cbfs = grp["cbf_hz"].to_numpy()
        dists, diffs = [], []
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                dists.append(float(np.linalg.norm(centers[i] - centers[j])))
                diffs.append(abs(cbfs[i] - cbfs[j]))
        if len(dists) >= 3:
            r, p_r = stats.pearsonr(dists, diffs)
            spatial_rows.append(
                {
                    "file": file,
                    "genotype": grp["genotype"].iloc[0],
                    "pearson_r": float(r),
                    "p_value": float(p_r),
                    "n_pairs": len(dists),
                }
            )
    spatial_df = pd.DataFrame(spatial_rows)

    return {
        "summary": summary,
        "per_file": per_file,
        "synchrony": sync_df,
        "spatial": spatial_df,
    }
