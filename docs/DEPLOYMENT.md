# Deployment — install and run on any computer

This guide uses **placeholders**. Your folders **will differ** on each machine — that is normal.

| Placeholder | Meaning | Example on your PC |
|-------------|---------|---------------------|
| **`PROJECT_ROOT`** | Folder where this repo lives (clone or unzip here) | `C:\Users\you\Documents\PearsonLab_AUTO_image_analysis_pipelines.` |
| **`VIDEO_FOLDER`** | Folder containing your `.tif` cilia videos | `D:\lab\cilia_aligned` |

You never need to match someone else’s path like `c:\Resume\Shreya\pearson lab`.

---

## Prerequisites

1. **Windows** (these commands use PowerShell). macOS/Linux work similarly — use `bash`/`zsh` instead of PowerShell where noted.
2. **Git** (optional): [git-scm.com](https://git-scm.com/) — only if you clone from GitHub.
3. **Miniconda or Anaconda**: [docs.conda.io](https://docs.conda.io/en/latest/miniconda.html) — gives you `conda` and isolated environments.

---

## Step A — Put the code somewhere on your disk

Pick **any** folder you control (Desktop, Documents, lab drive).

### Option 1 — Clone from GitHub

```powershell
cd $HOME\Documents
git clone https://github.com/babusa1/PearsonLab_AUTO_image_analysis_pipelines..git
cd PearsonLab_AUTO_image_analysis_pipelines.
```

Your **`PROJECT_ROOT`** is now whatever folder `git clone` created (name ends with **`.`** — two dots before nothing else may look odd; it matches the repo name on GitHub).

### Option 2 — ZIP download

1. Download ZIP from GitHub → Extract **anywhere**.
2. Open PowerShell → `cd` into the extracted folder (the one that contains `run_cbf.py`, `environment.yml`, `pearson_cbf\`).

That folder is your **`PROJECT_ROOT`**.

---

## Step B — Create the Python environment (once per machine)

Run **inside `PROJECT_ROOT`** (same folder as `environment.yml`):

```powershell
cd "<PROJECT_ROOT>"
conda env create -f environment.yml
```

If conda says the env already exists and you want to refresh:

```powershell
conda env remove -n pearsonlab
conda env create -f environment.yml
```

---

## Step C — Install this package in editable mode (once per clone)

Still inside **`PROJECT_ROOT`**:

```powershell
conda activate pearsonlab
pip install -e .
```

This registers `pearson_cbf` so Python finds it when you run `run_cbf.py`.

---

## Step D — Put your videos somewhere

Your **`VIDEO_FOLDER`** can be **anywhere**: USB drive, network folder, Desktop.

Requirements:

- `.tif` / `.tiff` stacks (aligned from FIJI when possible).
- Filenames contain **`wt`** or **`ds`** (for genotype grouping).

Example:

```
VIDEO_FOLDER = D:\pearson_data\cilia_batch1\
```

---

## Step E — Run the pipeline

Every session:

```powershell
conda activate pearsonlab
cd "<PROJECT_ROOT>"
python run_cbf.py --input "<VIDEO_FOLDER>" --fps YOUR_FPS --pixel-um YOUR_PIXEL_UM --no-prompt
```

Replace:

| Replace | With |
|---------|------|
| `<PROJECT_ROOT>` | Full path to repo (contains `run_cbf.py`) |
| `<VIDEO_FOLDER>` | Full path to folder with `.tif` files |
| `YOUR_FPS` | From FIJI: Image → Properties → fps = 1 ÷ frame interval (often ~150) |
| `YOUR_PIXEL_UM` | Microns per pixel from microscope calibration |

**Example** (paths are fictional):

```powershell
conda activate pearsonlab
cd "C:\Users\labuser\projects\PearsonLab_AUTO_image_analysis_pipelines."
python run_cbf.py --input "E:\microscopy\cilia_aligned" --fps 150 --pixel-um 0.162 --no-prompt
```

---

## Step F — Where outputs go

Outputs are written **next to your videos**, not inside `PROJECT_ROOT`:

```
<VIDEO_FOLDER>\results\goal1\
```

Main files: `cbf_all_rois.csv`, `cbf_statistics.csv`, `goal1a_cbf_comparison.png`, etc.

---

## Optional — Config file instead of long command line

1. Inside **`PROJECT_ROOT`**, copy `config.example.yaml` → `config.yaml`.
2. Edit `config.yaml` in Notepad:
   - `input_dir`: path to **`VIDEO_FOLDER`** (use `/` or escaped `\`).
   - `fps`, `pixel_um`: same as Step E.

```powershell
conda activate pearsonlab
cd "<PROJECT_ROOT>"
python run_cbf.py --config config.yaml
```

---

## Checklist (copy into lab notebook)

| Step | Done |
|------|------|
| Installed conda | ☐ |
| Cloned/unzipped repo → chose **`PROJECT_ROOT`** | ☐ |
| Ran `conda env create -f environment.yml` in **`PROJECT_ROOT`** | ☐ |
| Ran `conda activate pearsonlab` then `pip install -e .` | ☐ |
| Verified FIJI fps / pixel size | ☐ |
| Ran `python run_cbf.py --input "<VIDEO_FOLDER>" ...` | ☐ |
| Checked `<VIDEO_FOLDER>\results\goal1\` | ☐ |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `conda` not recognized | Install Miniconda; restart terminal |
| Wrong folder | Run `dir run_cbf.py` — file must exist in current directory |
| `No module named pearson_cbf` | Run `pip install -e .` from **`PROJECT_ROOT`** |
| Cannot find videos | Quote paths with spaces; use full path for `--input` |

---

## Related docs

- [MASTER_GUIDE.md](MASTER_GUIDE.md) — biology, ROI keys, Goal 1 outputs  
- [FIJI_PREP.md](FIJI_PREP.md) — drift correction before Python  
- [MASTER_GUIDE_DEVELOPER.md](MASTER_GUIDE_DEVELOPER.md) — code structure  
