# FIJI preparation (before Python CBF)

Pipeline 1 in Python assumes videos are already suitable for FFT. **Do this in ImageJ/FIJI first.**

## Step 1 — Check frame rate (critical)

1. Open `.tif` in FIJI.
2. **Image → Properties**
3. Frame interval in seconds → `fps = 1 / interval`
4. **Must be ≥150 fps** for automated FFT (Scopulovic et al.)
5. Write fps in your lab notebook — use the **same number** in `run_cbf.py --fps`

## Step 2 — Drift correction (required)

1. Install **MultiStackReg** plugin.
2. Open cilia stack.
3. Run drift correction (translation).
4. Save as new file, e.g. `wt_mouse1_aligned.tif` in `fiji_processed/aligned_videos/`.
5. **Never overwrite** files in `raw_data/`.

**Discard** videos with focus drift (z-drift) — cannot be fixed.

## Step 3 — FreQ plugin (quality control)

Use **identical** settings for every WT and DS video:

| Setting | Value |
|---------|--------|
| Recording frequency | Your fps (e.g. 150) |
| Sliding window | 2 |
| Local SD filter | 3.0 |
| Frequency range | 10–40 Hz |

**Good QC:** heatmap shows variation; histogram peak ~14–20 Hz for mouse.

Record these settings in your notebook — they must not change between genotypes.

## Step 4 — Optional CSV export for Python

See **[FIJI_ZAXIS_EXPORT.md](FIJI_ZAXIS_EXPORT.md)** for full steps.

```powershell
python run_cbf.py --mode csv --input "D:\project\fiji_processed\intensity_data" --fps 150 --pixel-um 0.162 --no-prompt
```

Python applies the same **sliding window = 2** and **local SD = 3.0** as FreQ (Jeong et al. 2022).

## What to feed Python

Point `--input` at the folder containing **aligned** `.tif` files:

```powershell
python run_cbf.py --input "D:\project\fiji_processed\aligned_videos" --fps 150 --pixel-um 0.162 --no-prompt
```
