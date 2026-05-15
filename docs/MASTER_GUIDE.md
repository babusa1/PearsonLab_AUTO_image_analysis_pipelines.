# Master guide — Pearson Lab Goal 1 (CBF analysis)

**Read this first.** It explains the biology, the code, every folder, and how to run the project — written for someone new to Python.

**GitHub repository:** [babusa1/PearsonLab_AUTO_image_analysis_pipelines.](https://github.com/babusa1/PearsonLab_AUTO_image_analysis_pipelines.)

---

## Quick reference (start here)

### What is the problem?

**Down syndrome (DS) mice** may have **broken or poorly coordinated cilia beating**, similar to **primary ciliary dyskinesia (PCD)**. **Goal 1** asks: is **cilia beat frequency (CBF)** different in **DS vs wild-type (WT)**? The pipeline also tests **variability**, **within-cell synchrony**, and **spatial coordination** (questions **Q1a–Q1d**).

### What is `run_cbf.py`?

The **button you press** to start analysis. It calls the code inside `pearson_cbf/`.

### What is `pearson_cbf/`?

The **real program** (split into small files). You normally **do not edit** these — just run `run_cbf.py`.

### What is `config.yaml`?

A **settings file** (copy from `config.example.yaml`). Stores folder path, **fps**, pixel size. **YAML** = simple `name: value` text.

### What is `environment.yml`?

Instructions for **conda** to install Python + numpy + scipy once:

```powershell
conda env create -f environment.yml
```

### What is `pyproject.toml`?

Tells Python this is an installable package. Used by `pip install -e .` — **ignore for daily work**.

### What is `__pycache__`?

**Auto-generated** when Python runs. Safe to delete. **Do not share or commit** (already in `.gitignore`).

### What is `scripts/`?

Helper scripts (e.g. one-time conda setup). **Not** the main analysis.

---

## How to get the code (GitHub)

### First time on a new computer

```powershell
git clone https://github.com/babusa1/PearsonLab_AUTO_image_analysis_pipelines..git
cd PearsonLab_AUTO_image_analysis_pipelines.

conda env create -f environment.yml
conda activate pearsonlab
pip install -e .
```

### If you already have the folder

```powershell
cd "c:\Resume\Shreya\pearson lab"
git pull
conda activate pearsonlab
```

---

## How to run (12 videos)

```powershell
conda activate pearsonlab
cd "c:\Resume\Shreya\pearson lab"
python run_cbf.py --input "D:\YOUR_FOLDER_WITH_12_TIFS" --fps 150 --pixel-um 0.162 --no-prompt
```

Replace:

- `D:\YOUR_FOLDER_WITH_12_TIFS` — folder containing all `.tif` files  
- `150` — your **fps** from FIJI (**Image → Properties** → fps = 1 ÷ frame interval)  
- `0.162` — your **µm/pixel** calibration  

**Filenames** must contain `wt` or `ds` (e.g. `wt_mouse1_aligned.tif`).

### ROI keys (each video)

| Key | Action |
|-----|--------|
| Drag | Box around beating cilia |
| **`n`** | Save ROI on a **new cell** |
| **`s`** | Save ROI on **same cell** (use twice on one cell for Q1c) |
| **`u`** | Undo |
| **`q`** | Done → next video |

**Second run** (same command): ROIs reload automatically from `results/goal1/rois/`.

### Optional: use `config.yaml`

```powershell
copy config.example.yaml config.yaml
# Edit config.yaml in Notepad — set input_dir, fps, pixel_um

python run_cbf.py --config config.yaml
```

---

## Goal 1 — outputs that mean you are done

All files appear in: `YOUR_FOLDER\results\goal1\`

| Must have | Purpose |
|-----------|---------|
| **`cbf_all_rois.csv`** | Main results table → import to **R** |
| **`cbf_statistics.csv`** | P-values for Q1a–Q1d |
| **`run_manifest.json`** | Record of settings (paste into lab notebook) |
| **`goal1a_cbf_comparison.png`** | WT vs DS CBF plot |
| **`goal1b_variability.png`** | Variability (Q1b) |
| **`goal1c_synchrony.png`** | Within-cell sync (Q1c; needs `s` key) |
| **`goal1d_spatial.png`** | Spatial plot (Q1d; needs ≥2 ROIs per video) |
| **`rois/*.json`** | Saved ROI boxes (reproducibility) |

**Also from FIJI (not Python):** drift-corrected `.tif` files + **FreQ** heatmap screenshots (see `FIJI_PREP.md`).

**Still needed for publication:** R mixed model on `cbf_all_rois.csv` (get R script from your PI).

### Sanity check

Mouse airway CBF should be roughly **10–20 Hz** at room temperature. If values are ~5 Hz or ~60 Hz, **fix fps** in FIJI first, then re-run Python.

---

## Part 1 — The problem (why this code exists)

### Biology in one paragraph

People with **Down syndrome (DS)** often have serious **lung and airway problems**. The airways are lined with **motile cilia** — tiny hairs that beat together to push mucus and bacteria out of the lungs. In a related disease called **primary ciliary dyskinesia (PCD)**, broken cilia cause similar symptoms. The Pearson Lab sees **DS mouse airways** that look like PCD (mucus buildup, disorganized cilia anchors), but we need **numbers**, not just pictures.

### Goal 1 (this repository)

**Question:** Are **cilia beat frequencies (CBF)** different in **DS mice** compared to **wild-type (WT)** controls?

CBF = how many times per second each cilium beats (unit: **Hertz, Hz**).  
Healthy mouse airway cilia at room temperature: about **14–20 Hz**.

Goal 1 has four sub-questions (called Q1a–Q1d in your project notes):

| ID | Question | Plain English |
|----|----------|---------------|
| **Q1a** | Mean CBF WT vs DS? | On average, do DS cilia beat slower or faster? |
| **Q1b** | More variability in DS? | Are some regions fast and some slow (bad for coordinated clearance)? |
| **Q1c** | Sync within one cell? | Do all cilia on the **same cell** beat at the same rate? |
| **Q1d** | Spatial coordination? | Do **neighboring cells** beat in a coordinated way (metachronal waves)? |

**This Python project** measures CBF from videos and produces tables and graphs for Q1a–Q1d.  
**FIJI/ImageJ** is still required for drift correction and FreQ quality-control maps (see Part 5).

---

## Part 2 — How CBF is measured (the science + math)

### The idea

1. You record a **video** of beating cilia (many frames per second).
2. Cilia moving up/down make **pixel brightness change** over time in a small region.
3. That brightness trace is like a **wave**.
4. **FFT (Fast Fourier Transform)** converts “waves over time” into “how strong each frequency is.”
5. The **tallest peak** in the 10–40 Hz range = **CBF**.

```
Video frames  →  average brightness inside ROI over time  →  FFT  →  peak frequency = CBF (Hz)
```

### Methods from your reference papers

| Step | Source | What we do |
|------|--------|------------|
| ≥150 fps for mouse | Scopulovic 2022 | You verify fps in FIJI; script warns if &lt;150 |
| Drift correction | Jeong 2022 | **You** run MultiStackReg in FIJI before Python |
| FFT, band 10–40 Hz | Jeong 2022 | Python `signal_fft.py` |
| Smooth spectrum (window=2) | Jeong FreQ | Python `sliding_window: 2` |
| Local SD filter (=3.0) | Jeong FreQ | Python `local_sd_filter: 3.0` |
| FreQ heatmaps | Jeong 2022 | **You** run FreQ plugin in FIJI (not in Python) |

---

## Part 3 — Big picture: what runs where

```
YOUR DATA
  raw_data/                    ← microscope originals (never edit)
       ↓
  FIJI: MultiStackReg          ← fix camera drift
       ↓
  fiji_processed/aligned/      ← aligned .tif videos
       ↓
  FIJI: FreQ plugin            ← color maps / QC (optional but recommended)
       ↓
  PYTHON: run_cbf.py           ← THIS REPO — CBF per ROI, statistics, plots
       ↓
  results/goal1/               ← CSV + PNG outputs
       ↓
  R (later)                    ← mixed model, publication Figure 1
```

---

## Part 4 — Every folder and file (what it is)

### Top level

| Name | What it is | Do you edit it? |
|------|------------|-----------------|
| **`docs/`** | Human-readable guides (you are here) | Read only |
| **`pearson_cbf/`** | The actual Python **program** (library) | Rarely — only if fixing bugs |
| **`run_cbf.py`** | **Start button** — run this to analyze videos | No — just execute it |
| **`cbf_analysis.py`** | Same as `run_cbf.py` (old name kept for compatibility) | No |
| **`scripts/`** | Helper shell scripts (e.g. install conda once) | Run once for setup |
| **`config.example.yaml`** | **Template settings** — copy to `config.yaml` | Copy & edit `config.yaml` |
| **`environment.yml`** | List of software for **conda** install | No |
| **`requirements.txt`** | List of software for **pip** install | No |
| **`pyproject.toml`** | Python packaging metadata (`pip install -e .`) | No |
| **`README.md`** | Short overview + quick commands | Read |
| **`.gitignore`** | Tells Git what not to upload (data, cache) | No |

### `docs/` folder

| File | Purpose |
|------|---------|
| **MASTER_GUIDE.md** | This document |
| **LAB_STANDARDS.md** | Reproducibility rules for the lab |
| **FIJI_PREP.md** | Drift + FreQ in ImageJ before Python |
| **FIJI_ZAXIS_EXPORT.md** | Export CSV profiles from FIJI (optional path) |
| **PAPER_COMPLIANCE.md** | How code matches Scopulovic & Jeong papers |

### `pearson_cbf/` — the Python package (the “engine”)

Think of `pearson_cbf` as a **toolbox**. `run_cbf.py` is the **handle** you turn.

| File | Role (plain English) |
|------|----------------------|
| **`cli.py`** | Reads command-line options (`--input`, `--fps`, etc.) |
| **`config.py`** | Loads settings from `config.yaml` |
| **`pipeline.py`** | **Main workflow**: loop videos → ROIs → FFT → save results |
| **`signal_fft.py`** | **Math**: FFT, smoothing, find CBF peak |
| **`io_loaders.py`** | **Read files**: open `.tif` stacks or FIJI `.csv` |
| **`roi_select.py`** | **Draw boxes** on screen for each video |
| **`roi_store.py`** | **Save/load** ROI boxes to JSON (reproducibility) |
| **`genotype.py`** | Guess **WT vs DS** from filename |
| **`statistics.py`** | **Q1a–Q1d** statistical tests |
| **`plots.py`** | Make PNG graphs |
| **`models.py`** | Small data structures (ROI, results) |
| **`__init__.py`** | Marks folder as a Python package |
| **`__main__.py`** | Allows `python -m pearson_cbf` |

You do **not** need to open these files to run the analysis. Use `run_cbf.py`.

### `scripts/`

| File | Purpose |
|------|---------|
| **`setup_conda.ps1`** | Windows PowerShell: creates conda env `pearsonlab` (optional shortcut) |

### `__pycache__/` (you may see this appear)

- **Not part of the project design.** Python creates it automatically when you run code.
- Contains **compiled** copies of `.py` files (faster reruns).
- **Safe to delete.** Python recreates it.
- Listed in `.gitignore` — **do not commit** to Git.

---

## Part 5 — Config files explained (yaml, yml, toml, env)

You are **not** expected to know these formats by heart. You only need to **copy and edit one file**.

### `config.example.yaml` → `config.yaml`

- **YAML** = a simple text format: `name: value` (like a settings form).
- **`.yaml` and `.yml`** are the same thing.
- **What to do:**  
  ```text
  Copy config.example.yaml → config.yaml
  Edit paths and fps in config.yaml
  Run: python run_cbf.py --config config.yaml
  ```

Example inside `config.yaml`:

```yaml
paths:
  input_dir: "D:/my_videos"      # folder with 12 .tif files
microscope:
  fps: 150.0                       # MUST match FIJI frame rate
  pixel_um: 0.162                  # from microscope calibration
analysis:
  freq_min_hz: 10.0                # do not change between WT and DS
  freq_max_hz: 40.0
  sliding_window: 2                # Jeong / FreQ default
  local_sd_filter: 3.0
```

### `environment.yml`

- Used by **Anaconda/Miniconda** to create an isolated Python environment named **`pearsonlab`**.
- Lists Python version + packages (numpy, scipy, etc.).
- **One-time setup:** `conda env create -f environment.yml`

### `requirements.txt`

- Same idea as `environment.yml` but for **`pip install`** only.
- Used if you prefer `venv` instead of conda.

### `pyproject.toml`

- Tells Python this folder is an installable package named `pearson-cbf`.
- Enables `pip install -e .` so `import pearson_cbf` works.
- **You do not edit this** for normal lab work.

---

## Part 6 — Step-by-step: install and run (12 videos)

### A. One-time installation (Windows)

Open **PowerShell**:

```powershell
cd "c:\Resume\Shreya\pearson lab"

conda env create -f environment.yml
conda activate pearsonlab
pip install -e .
```

If `conda` is not installed, install [Miniconda](https://docs.conda.io/en/latest/miniconda.html) first.

### B. Prepare your videos

1. Put **12** `.tif` files in one folder, e.g. `D:\pearson_data\cilia_batch1\`
2. Names must include **`wt`** or **`ds`**, e.g. `wt_mouse1_aligned.tif`
3. Prefer **drift-corrected** files from FIJI (see `FIJI_PREP.md`)

### C. Find your microscope numbers (before Python)

In **FIJI**: open one video → **Image → Properties**

- **Frame interval** in seconds → `fps = 1 ÷ interval`  
  Example: interval `0.00667` s → fps ≈ **150**
- **Pixel width** in µm → use for `--pixel-um`

Write these in your lab notebook.

### D. Run Python (first time — draw ROIs)

```powershell
conda activate pearsonlab
cd "c:\Resume\Shreya\pearson lab"

python run_cbf.py --input "D:\pearson_data\cilia_batch1" --fps 150 --pixel-um 0.162 --no-prompt
```

**For each video** a window opens:

| Key | Action |
|-----|--------|
| Drag mouse | Draw rectangle on **beating** cilia |
| **`n`** | Save ROI, start a **new cell** |
| **`s`** | Save ROI on **same cell** (do twice on one cell for Q1c) |
| **`u`** | Undo last ROI |
| **`q`** | Done → next video |

Console shows: `Video 3 / 12: ...`

### E. Run again (no redraw)

Same command. ROIs load from `results/goal1/rois/` automatically.

### F. Alternative: use config file

```powershell
copy config.example.yaml config.yaml
# Edit config.yaml in Notepad — set input_dir, fps, pixel_um

python run_cbf.py --config config.yaml
```

---

## Part 7 — Goal 1 complete: required outputs

When Goal 1 is **done**, you should have the following.

### From FIJI (for lab notebook / QC)

| Output | Description |
|--------|-------------|
| Aligned `.tif` stacks | After MultiStackReg |
| FreQ CBF heatmaps | Screenshot or PNG per video |
| Recorded **fps** and FreQ settings | In notebook + `run_manifest.json` |

### From Python (`results/goal1/`)

| File | Required? | Used for |
|------|-----------|----------|
| **`cbf_all_rois.csv`** | **Yes** | Main table — every ROI, every video; import to **R** |
| **`cbf_statistics.csv`** | **Yes** | Summary p-values Q1a–Q1d |
| **`run_manifest.json`** | **Yes** | Proof of settings (fps, frequency band, date) |
| **`goal1a_cbf_comparison.png`** | **Yes** | Q1a figure — WT vs DS CBF |
| **`goal1b_variability.png`** | **Yes** | Q1b — variability |
| **`goal1c_synchrony.png`** | **Yes** (if Q1c ROIs drawn) | Within-cell sync |
| **`goal1d_spatial.png`** | **Yes** (if ≥2 ROIs/video) | Spatial correlation |
| **`plots/*.png`** | Recommended | Per-ROI diagnostic (signal + FFT) |
| **`rois/*.json`** | **Yes** | Saved ROI boxes (reproducibility) |
| **`all_cbf_results.csv`** | Optional | Simplified columns |
| **`cbf_synchrony.csv`** | Optional | Detail for Q1c |
| **`cbf_spatial.csv`** | Optional | Detail for Q1d |

### What “good” looks like biologically

- WT and DS CBF mostly in **10–20 Hz** for mouse trachea (room temp).
- Clear peak in FFT plot (not flat noise).
- If all CBF ≈ 5 Hz or 60 Hz → **wrong fps** — fix in FIJI first.

### What is still needed to **fully close** Goal 1 for publication

| Step | Tool | Status in this repo |
|------|------|---------------------|
| CBF per ROI + Q1a–d plots | Python | ✅ This repo |
| Final stats with nested mice/cells | **R (`lme4`)** | ⬜ You do separately on `cbf_all_rois.csv` |
| Publication Figure 1 | **R (`ggplot2`)** | ⬜ From R script in lab protocol |

**Practical “Goal 1 closed” checklist:**

- [ ] All 12 videos processed in FIJI (drift + FreQ QC)
- [ ] All 12 videos processed in Python with saved ROIs
- [ ] `cbf_all_rois.csv` and 4 `goal1*.png` files exist
- [ ] CBF values biologically plausible (~14–20 Hz)
- [ ] `run_manifest.json` archived in lab notebook
- [ ] R mixed model run on `cbf_all_rois.csv` (ask PI for R template)

---

## Part 8 — Glossary

| Term | Meaning |
|------|---------|
| **CBF** | Cilia beat frequency (beats per second, Hz) |
| **WT** | Wild type — normal control mice |
| **DS** | Down syndrome model mice |
| **ROI** | Region of interest — box drawn on cilia |
| **FFT** | Math that finds dominant frequency in a signal |
| **FIJI** | ImageJ — free microscopy image program |
| **FreQ** | FIJI plugin for CBF heatmaps |
| **fps** | Frames per second — video speed |
| **conda** | Package manager that creates `pearsonlab` environment |
| **pip** | Python package installer |

---

## Part 9 — Common problems

| Problem | Fix |
|---------|-----|
| `conda: not recognized` | Install Miniconda; restart PowerShell |
| `No module named pearson_cbf` | Run `pip install -e .` from project folder |
| Genotype `Unknown` | Add `wt` or `ds` to filename |
| Q1c skipped | Press **`s`** for 2nd ROI on same cell |
| Nonsense CBF | Fix **`--fps`** to match FIJI |
| Window does not open | Run on your PC with a screen (not remote-only) |

---

## Part 10 — What this repo does **not** do (Goals 2 & 3)

- **Goal 2** — fluorescent **bead tracking** / mucus velocity → TrackMate + future `goal2` code  
- **Goal 3** — **centriole** segmentation → future `goal3` code  

Only **Goal 1 (CBF)** is in this repository.

---

## Quick reference card

```powershell
conda activate pearsonlab
cd "c:\Resume\Shreya\pearson lab"
python run_cbf.py --input "YOUR_VIDEO_FOLDER" --fps 150 --pixel-um 0.162 --no-prompt
```

Outputs: `YOUR_VIDEO_FOLDER\results\goal1\`
