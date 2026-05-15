# Paper compliance: CBF pipeline vs. lab PDFs

This maps your two reference PDFs in `AdditionalDETAILS/` to **Pipeline 1** (`run_cbf.py` + FIJI steps).

| File in folder | Paper |
|----------------|--------|
| `CILIA FreQ.pdf` | **Scopulovic et al. 2022** — *Physiological Reports* — frame rate requirements for FFT vs manual CBF |
| `FreQ II.pdf` | **Jeong et al. 2022** — *STAR Protocols* — FreQ plugin, drift correction, FFT CBF + bead flow (TrackMate) |

**Short answer:** Python covers **core FFT-CBF statistics** (Q1a–d) but does **not** replace **FIJI + FreQ**. Use **both**: FIJI for QC/maps/drift, Python for ROI stats and WT vs DS.

---

## Overall coverage

| Layer | Scopulovic 2022 | Jeong 2022 (CBF part) | Your repo |
|-------|-----------------|------------------------|-----------|
| **Acquire ≥150 fps (mouse FFT)** | ✅ Required for automated FFT | ⚠ Zebrafish example uses ~100 Hz; mouse Pearson data should follow Scopulovic | ✅ Warning if fps &lt; 150 |
| **Drift correction (xy)** | Implied (same cilia compared across downsampling) | ✅ MultiStackReg before FreQ | ✅ Documented in `FIJI_PREP.md`; **you do in FIJI, not in Python** |
| **Discard z-drift** | — | ✅ Cannot correct | ✅ Documented |
| **FFT dominant peak** | ✅ MATLAB on kymograph | ✅ FreQ / MATLAB per-pixel | ✅ `scipy.fft` on ROI mean intensity |
| **Search band 10–40 Hz** | — | ✅ Steps 20, 28 | ✅ `freq_min_hz` / `freq_max_hz` |
| **FreQ per-pixel heatmaps** | — | ✅ Full field CBF maps | ❌ **Not in Python** — run FreQ in FIJI |
| **FreQ settings (window=2, local SD=3)** | — | ✅ Steps 26–27 | ✅ Python defaults (`sliding_window`, `local_sd_filter`) |
| **Manual kymograph fallback** | ✅ Gold standard at low fps | — | ❌ Not implemented (use if fps &lt; 150) |
| **WT vs DS + extra stats** | — | — | ✅ Q1a–d (Pearson project) |
| **Bead flow / TrackMate** | — | ✅ Steps 32–38 (Goal 2) | ❌ **Pipeline 2** — not this repo |

**Estimated coverage of the two papers’ CBF method:** ~**85%** in Python (FFT + Jeong params); ~**95%** if you also run **FIJI FreQ** for per-pixel heatmap QC.

---

## Paper 1: Scopulovic et al. 2022 (`CILIA FreQ.pdf`)

### What the paper says

1. CBF from high-speed video is standard for assessing motile cilia.
2. **Frame rate matters a lot** for **automated FFT** (more than for manual kymograph counting).
3. **Mouse airway** at room temp: mean CBF ~**14–15 Hz**; at 37°C ~**19 Hz**.
4. **≥150 fps** needed for accurate **FFT-based** CBF; 30 fps can underestimate by ~50% for faster-beating cilia.
5. Rule of thumb: sample at **3–4× the CBF** (not Nyquist alone).
6. At **&gt;150 fps**, automated FFT ≈ manual counting; below that, prefer manual.

### What your pipeline does

| Requirement | Covered? | Where |
|-------------|----------|--------|
| Use FFT for automated CBF | ✅ | `pearson_cbf/signal_fft.py` |
| Dominant peak in spectrum | ✅ | `argmax` in 10–40 Hz band |
| Warn if fps &lt; 150 | ✅ | `pipeline.run_pipeline()` |
| Expect mouse airway ~14–20 Hz | ✅ | README + you interpret results |
| Manual kymograph if low fps | ⚠ Partial | Document only — no kymograph tool in repo |
| Downsampling / multi-fps study | N/A | Paper experiment design, not needed for your analysis |

### Gaps vs Scopulovic

- You analyze **ROI mean intensity**, not **kymograph line profiles** — acceptable at ≥150 fps (paper Figure 2: FFT ≈ manual when fps high enough).
- No built-in **manual counting** mode — if videos are &lt;150 fps, use kymograph counts in FIJI instead of trusting Python FFT.

---

## Paper 2: Jeong et al. 2022 (`FreQ II.pdf`)

### CBF-related steps (Pipeline 1)

| Jeong step | Topic | Your pipeline |
|------------|--------|---------------|
| 10–16 | Record cilia (brightfield, high fps) | Your `.tif` input (you acquire in lab) |
| 17–21 | MATLAB: align, FFT, 10–40 Hz, heatmaps | Partially replaced by **FreQ (FIJI)** + **Python FFT** |
| **Drift note** | xy drift → FFT artifacts; fix or discard | ✅ `FIJI_PREP.md` |
| **MultiStackReg** | Before FreQ | ✅ You must run in FIJI |
| 22–31 | **FreQ plugin**: heatmaps + batch UI | ❌ Run FreQ in FIJI — **required for QC maps** |
| Optional ROI in FreQ | User-drawn ROI | ✅ Python: interactive ROIs + JSON save |
| 32–47 | TrackMate + flow | **Pipeline 2** (beads) — separate |

### FFT principle (Jeong Figure 4A)

> Intensity oscillates in time → FFT → dominant frequency = CBF.

Your code: mean intensity inside ROI over time → detrend → Hanning → `rfft` → peak in [10, 40] Hz. **Same principle**, different implementation detail (single ROI trace vs FreQ’s per-pixel spectra).

### FreQ-specific parameters **not** in Python

| FreQ parameter | Jeong value | In `run_cbf.py`? |
|----------------|-------------|------------------|
| Recording frequency | Exact fps | ✅ `--fps` |
| Sliding window (smooth spectrum) | 2 | ✅ `--sliding-window 2` |
| Local SD filter | 3.0 | ✅ `--local-sd-filter 3.0` |
| Enhance peak detection (% low power, fold SD) | 20%, 1.5 (tunable) | ⚠ Simplified (`low_power_percent: 20`) |
| Limit frequency range | 10–40 Hz | ✅ |
| Per-pixel CBF heatmap + histogram | Output PNGs | ❌ — FreQ in FIJI only |

**Important:** Jeong states MATLAB and FreQ give **slightly different** heatmaps (Figures 4D2, 5B2, 10). ROI-level Python FFT will also differ slightly from FreQ maps — that is expected. Use FreQ for **spatial QC**; use Python for **statistics**.

### Mendeley practice data

Jeong: https://data.mendeley.com/datasets/p6sfdpjpj2/2  

Use this to validate: aligned stacks → FreQ → Python on same files → CBF ~10–20 Hz (tissue-dependent).

---

## Recommended complete workflow (matches both papers + lab protocol)

```
raw_data/cilia_videos/          (never edit)
        ↓
FIJI: MultiStackReg             (Jeong — drift)
        ↓
fiji_processed/aligned_videos/
        ↓
FIJI: FreQ (window=2, SD=3, 10–40 Hz)   (Jeong — QC heatmaps)
        ↓
Python: run_cbf.py on aligned .tif        (FFT per ROI, Q1a–d)
        ↓
R: lme4 on cbf_all_rois.csv               (Pearson — nested stats)
```

---

## Project questions (Q1a–d) vs papers

| Question | In papers? | In your code? |
|----------|------------|----------------|
| Q1a Mean CBF WT vs DS | Implied | ✅ |
| Q1b Variability | Implied (heterogeneity noted in Jeong) | ✅ Levene on per-video SD |
| Q1c Within-cell sync | Not in papers | ✅ (2+ ROIs, `s` key) |
| Q1d Spatial coordination | Not in papers | ✅ distance vs \|ΔCBF\| |

Q1c/Q1d are **Pearson project** extensions — correctly added beyond the papers.

---

## Action items for you

1. **Always** drift-correct in FIJI before Python (`FIJI_PREP.md`).
2. **Always** run **FreQ** with Jeong settings for lab notebook / QC figures.
3. Confirm **fps ≥ 150** on mouse trachea videos (Scopulovic).
4. On each video: **2+ ROIs on one cell** (`s` key) for Q1c.
5. If any video is &lt;150 fps, note in notebook and consider **manual** kymograph (Scopulovic) instead of trusting FFT alone.

---

## References (from your PDFs)

- Scopulovic L, et al. Quantifying cilia beat frequency using high-speed video microscopy. *Physiol Rep.* 2022;10:e15349. doi:10.14814/phy2.15349  
- Jeong I, et al. Measurement of ciliary beating and fluid flow in the zebrafish adult telencephalon. *STAR Protoc.* 2022;3:101542. doi:10.1016/j.xpro.2022.101542  
