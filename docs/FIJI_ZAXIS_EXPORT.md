# Export FIJI Z-axis profiles for Python CBF

Use this when ROIs are drawn in FIJI and you want Python to run the **same FFT settings as FreQ** on exported intensity traces.

## When to use CSV mode vs TIFF mode

| Mode | Command | Best for |
|------|---------|----------|
| **tiff** (default) | `--mode tiff` | 12 videos: draw ROIs in Python on first frame |
| **csv** | `--mode csv` | ROIs already drawn in FIJI; one CSV per ROI |

## Export steps (FIJI)

1. Open **drift-corrected** stack (`*_aligned.tif`).
2. Verify **Image → Properties** → note **fps** = `1 / frame interval`.
3. Draw ROI over beating cilia (polygon or rectangle).
4. **Image → Stacks → Plot Z-axis Profile**
5. In the plot window: **List → Save As…**
6. Save as e.g. `wt_mouse3_cell1_roi1_zprofile.csv`
7. Repeat for each ROI (Q1c: multiple CSVs per video with same `cell` in filename).

## Naming convention

```
wt_mouse3_20250615_cell1_roi1_zprofile.csv
wt_mouse3_20250615_cell1_roi2_zprofile.csv
ds_mouse2_20250615_cell1_roi1_zprofile.csv
```

Must contain `wt` or `ds`. Optional: `cell1`, `roi1` in filename for grouping.

## Run Python on CSV folder

```powershell
python run_cbf.py --mode csv --input "D:\project\fiji_processed\intensity_data" --fps 150 --pixel-um 0.162 --no-prompt
```

Uses Jeong/FreQ FFT settings from config: `sliding_window: 2`, `local_sd_filter: 3.0`, band 10–40 Hz.

## Expected CSV format

FIJI typically exports:

| Time | Mean |
|------|------|
| 0 | 142.3 |
| 1 | 145.1 |
| … | … |

The loader also accepts columns named `Gray Value`, `Intensity`, or tab-separated files.

## Troubleshooting

| Error | Fix |
|-------|-----|
| Need ≥8 frames | Longer video or larger ROI on moving cilia |
| No numeric column | Re-save from List window, not a screenshot |
| Wrong CBF | Wrong **fps** in `--fps` |
