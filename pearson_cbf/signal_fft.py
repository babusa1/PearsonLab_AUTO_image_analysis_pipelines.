"""Intensity extraction and FFT-based CBF estimation (Jeong / FreQ-aligned)."""

from __future__ import annotations

import numpy as np
from scipy.fft import rfft, rfftfreq

from pearson_cbf.models import ROI


def extract_signal_from_stack(stack: np.ndarray, roi: ROI) -> np.ndarray:
    region = stack[:, roi.y : roi.y + roi.h, roi.x : roi.x + roi.w]
    return region.mean(axis=(1, 2))


def detrend_and_window(signal: np.ndarray) -> np.ndarray:
    s = signal.astype(np.float64)
    s -= np.mean(s)
    std = np.std(s)
    if std > 0:
        s /= std
    return s * np.hanning(len(s))


def smooth_power_spectrum(power: np.ndarray, sliding_window: int) -> np.ndarray:
    """
    Moving-average smooth of |FFT|^2 (FreQ: sliding window = 2).

    Jeong et al. STAR Protocols 2022, step 26.
    """
    w = int(sliding_window)
    if w <= 1:
        return power.copy()
    kernel = np.ones(w, dtype=np.float64) / w
    return np.convolve(power, kernel, mode="same")


def apply_local_sd_peak_mask(
    power: np.ndarray,
    local_sd_filter: float,
    low_power_percent: float = 20.0,
) -> np.ndarray:
    """
    Suppress low-power spectral noise before peak pick (FreQ local SD filter = 3.0).

    Uses the lowest *low_power_percent* of bins to estimate background,
    then keeps bins >= mean + local_sd_filter * std (Jeong step 27).
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
    Dominant frequency in [freq_min, freq_max] Hz via windowed FFT.

    Parameters match Jeong et al. 2022 FreQ defaults where noted:
    - sliding_window: smooth power spectrum (default 2)
    - local_sd_filter: peak detection threshold (default 3.0; set 0 to disable)

    Returns
    -------
    cbf_hz, peak_power, frequencies, power_spectrum (smoothed, as used for peak)
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

    freqs_b = freqs[band]
    power_b = power[band]
    power_for_peak = apply_local_sd_peak_mask(
        power_b, local_sd_filter, low_power_percent
    )

    peak_i = int(np.argmax(power_for_peak))
    return float(freqs_b[peak_i]), float(power_for_peak[peak_i]), freqs, power
