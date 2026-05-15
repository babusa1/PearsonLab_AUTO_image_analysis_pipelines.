"""Pearson Lab — Pipeline 1: Cilia Beat Frequency (CBF) analysis."""

__version__ = "1.1.0"

from pearson_cbf.config import CBFConfig
from pearson_cbf.pipeline import run_pipeline

__all__ = ["CBFConfig", "run_pipeline", "__version__"]
