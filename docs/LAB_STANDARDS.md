# Lab standards — reproducibility and data handling

How Pearson Lab expectations map to this project (Pipeline 1: CBF).

## Three summer deliverables

| # | Question | Pipeline | Tools |
|---|----------|----------|-------|
| 1 | Are cilia beat frequencies altered in DS? | **Pipeline 1 — CBF** (this repo) | FIJI + Python + R |
| 2 | Is mucociliary flow disrupted? | Pipeline 2 — Flow | TrackMate + Python + R |
| 3 | Is centriole layout altered? | Pipeline 3 — Centrioles | Python + R |

---

## Data handling rules

### 1. Never edit raw files

Keep original microscope files in `raw_data/`. Save FIJI outputs under `fiji_processed/`. Python writes only to `results/goal1/`.

### 2. Same parameters for every sample

Use one `config.yaml` with the same `fps`, `freq_min_hz` (10), `freq_max_hz` (40), `sliding_window` (2), and `local_sd_filter` (3.0) for all WT and DS videos. Use identical FreQ settings in FIJI for every video.

### 3. Record settings in your lab notebook

After each Python run, copy `results/goal1/run_manifest.json` into your notebook (fps, date, file list).

### 4. File naming

Include genotype, animal ID, and date, e.g. `wt_mouse3_20250615_aligned.tif`. The script detects `wt` or `ds` in the filename.

### 5. Reproducible reruns

ROI boxes are saved in `results/goal1/rois/`. A second run reloads them automatically.

### 6. Presentation

Pipeline 1 produces Goal 1 figures and `cbf_all_rois.csv` for the final R figure and lab meeting slides.

---

## First successful test (minimum)

1. Process one WT and one DS video in FIJI (drift correction + FreQ QC).
2. Run Python on both; draw **2 ROIs on one cell** (press `s` for the second ROI).
3. Confirm CBF is roughly **10–20 Hz** for mouse airway.
4. Save `goal1a_cbf_comparison.png` and a FreQ heatmap screenshot for your notebook.
