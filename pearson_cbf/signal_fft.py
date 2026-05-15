"""
FFT-based cilia beat frequency (CBF) estimation
================================================

Author:        Shreeya Malvi
Email:          shreeya.malvi@colorado.edu
Date Created:   2025-05-01
Date Modified:  2026-05-16
Version:        1.2.0

Module purpose
--------------
Core signal processing for Goal 1:

1. Extract mean pixel intensity inside an ROI across video frames.
2. Detrend and apply a Hanning window.
3. Real FFT → power spectrum.
4. Smooth spectrum (FreQ sliding window) and optional local-SD peak mask.
5. Report dominant frequency in [10, 40] Hz as CBF.

References: Jeong et al. STAR Protocols 2022; Scopulovic et al. Physiol Rep 2022.
"""

from __future__ import annotations

import numpy as np
from scipy.fft import rfft, rfftfreq

from pearson_cbf.models import ROI


def extract_signal_from_stack(stack: np.ndarray, roi: ROI) -> np.ndarray:
    """
    Average intensity inside ``roi`` for each time frame.

    Parameters
    ----------
    stack
        Shape ``(T, Y, X)`` from ``load_tif_stack``.
    roi
        Region over beating cilia.

    Returns
    -------
    np.ndarray
        1D signal of length ``T`` (arbitrary intensity units).
    """
    region = stack[:, roi.y : roi.y + roi.h, roi.x : roi.x + roi.w]
    return region.mean(axis=(1, 2))


def detrend_and_window(signal: np.ndarray) -> np.ndarray:
    """
    Remove DC component, normalize variance, apply Hanning window.

    Reduces spectral leakage before FFT.
    """
    s = signal.astype(np.float64)
    s -= np.mean(s)
    std = np.std(s)
    if std > 0:
        s /= std
    return s * np.hanning(len(s))


def smooth_power_spectrum(power: np.ndarray, sliding_window: int) -> np.ndarray:
    """
    Moving-average smooth of |FFT|² (FreQ: sliding window = 2).

    See Jeong et al. STAR Protocols 2022, step 26.
    """
    width = int(sliding_window)
    if width <= 1:
        return power.copy()
    kernel = np.ones(width, dtype=np.float64) / width
    return np.convolve(power, kernel, mode="same")


def apply_local_sd_peak_mask(
    power: np.ndarray,
    local_sd_filter: float,
    low_power_percent: float = 20.0,
) -> np.ndarray:
    """
    Suppress low-power spectral noise before peak detection.

    Estimates background from the lowest ``low_power_percent`` of frequency bins,
    then keeps bins >= mean + ``local_sd_filter`` × std (FreQ local SD = 3.0).
    """
    if local_sd_filter <= 0:
        return power.copy()

    n = len(power)
    k = max(1, int(np.ceil(n * low_power_percent / 100.0)))
    idx = np.argpartition(power, k - 1)[:k]
    noise = power[idx]
    noise_std = float(noise.std())
    if noise_std < 1e-12:
        noise_std = 1e-12
    threshold = float(noise.mean()) + local_sd_filter * noise_std
    masked = np.where(power >= threshold, power, 0.0)
    if masked.max() <= 0:
        return power.copy()
    return masked


def compute_cbf(
    signal: np.ndarray,
    fps: float,
    freq_min: float,
    freq_max: float,
    *,
    sliding_window: int = 2,
    local_sd_filter: float = 3.0,
    low_power_percent: float = 20.0,
) -> tuple[float, float, np.ndarray, np.ndarray]:
    """
    Estimate CBF as the dominant frequency in ``[freq_min, freq_max]`` Hz.

    Parameters
    ----------
    signal
        1D intensity trace (one value per frame).
    fps
        Recording frame rate (Hz); must match FIJI Image → Properties.
    freq_min, freq_max
        Search band for the CBF peak (typically 10–40 Hz).
    sliding_window, local_sd_filter, low_power_percent
        FreQ-aligned post-processing (Jeong et al. 2022).

    Returns
    -------
    cbf_hz : float
        Dominant beat frequency (Hz).
    peak_power : float
        Power at that frequency (quality indicator).
    freqs, power : np.ndarray
        Full one-sided spectrum (for plotting).
    """
    if len(signal) < 8:
        raise ValueError("Signal too short for FFT (need ≥8 frames).")

    windowed = detrend_and_window(signal)
    spectrum = rfft(windowed)
    power = np.abs(spectrum) ** 2
    freqs = rfftfreq(len(windowed), d=1.0 / fps)

    power = smooth_power_spectrum(power, sliding_window)

    band = (freqs >= freq_min) & (freqs <= freq_max)
    if not np.any(band):
        raise ValueError(f"No FFT bins in [{freq_min}, {freq_max}] Hz at fps={fps}.")

    freqs_band = freqs[band]
    power_band = power[band]
    power_for_peak = apply_local_sd_peak_mask(
        power_band, local_sd_filter, low_power_percent
    )

    peak_index = int(np.argmax(power_for_peak))
    cbf_hz = float(freqs_band[peak_index])
    peak_power = float(power_for_peak[peak_index])
    return cbf_hz, peak_power, freqs, power
