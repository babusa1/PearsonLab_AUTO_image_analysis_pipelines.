# Pearson Lab — Pipeline 1: Cilia Beat Frequency (CBF)

[![GitHub](https://img.shields.io/badge/GitHub-PearsonLab_AUTO_image_analysis_pipelines-blue)](https://github.com/babusa1/PearsonLab_AUTO_image_analysis_pipelines)

Automated analysis of **cilia beat frequency (CBF)** in **wild-type (WT)** vs **Down syndrome (DS)** mouse airway videos (Goal 1).

> **New to Python?** Read **[docs/MASTER_GUIDE.md](docs/MASTER_GUIDE.md)** — full explanation of the problem, every folder, config files, and step-by-step run instructions.

| Question | What this pipeline does |
|----------|-------------------------|
| **Q1a** Mean CBF WT vs DS? | Mann-Whitney + comparison plot |
| **Q1b** Greater variability? | Levene test on per-video SD |
| **Q1c** Sync within one cell? | ≥2 ROIs on same cell (`s` key) |
| **Q1d** Spatial coordination? | Distance vs \|ΔCBF\| correlation |

This repo is **Pipeline 1 only**. Goals 2 (bead flow) and 3 (centrioles) are separate.

---

## Quick run (12 videos)

```powershell
conda activate pearsonlab
cd "c:\Resume\Shreya\pearson lab"
python run_cbf.py --input "D:\YOUR_VIDEO_FOLDER" --fps 150 --pixel-um 0.162 --no-prompt
```

**Install once:** `conda env create -f environment.yml` then `pip install -e .`

**ROI keys:** draw box → `n` (new cell) or `s` (same cell) → `q` (next video)

**Outputs:** `YOUR_FOLDER\results\goal1\` — see [Goal 1 deliverables](docs/MASTER_GUIDE.md#part-7--goal-1-complete-required-outputs) in the master guide.

---

## Documentation

| Document | Contents |
|----------|----------|
| **[docs/MASTER_GUIDE.md](docs/MASTER_GUIDE.md)** | **Start here** — problem, CBF method, all files explained, run steps |
| [docs/LAB_STANDARDS.md](docs/LAB_STANDARDS.md) | Reproducibility and data handling |
| [docs/FIJI_PREP.md](docs/FIJI_PREP.md) | Drift correction + FreQ before Python |
| [docs/FIJI_ZAXIS_EXPORT.md](docs/FIJI_ZAXIS_EXPORT.md) | Optional CSV export from FIJI |
| [docs/PAPER_COMPLIANCE.md](docs/PAPER_COMPLIANCE.md) | Match to Scopulovic & Jeong papers |

---

## Project layout

```
pearson lab/
  run_cbf.py              ← run this
  config.example.yaml     ← copy to config.yaml
  pearson_cbf/            ← Python package (engine)
  docs/                   ← guides
  scripts/                ← setup helpers
  environment.yml         ← conda dependencies
```

---

## Lab standards (summary)

| Rule | Action |
|------|--------|
| Never edit raw videos | FIJI → `fiji_processed/`; Python → `results/goal1/` |
| Same settings for all samples | One `config.yaml`; same FreQ settings in FIJI |
| Record fps in notebook | Copy `run_manifest.json` after each run |
| Filenames with `wt` or `ds` | e.g. `wt_mouse3_20250615_aligned.tif` |

Details: [docs/LAB_STANDARDS.md](docs/LAB_STANDARDS.md)

---

Pearson Lab, CU Boulder — Goal 1 analysis code. Confirm analysis parameters with your PI before changing defaults across genotypes.
