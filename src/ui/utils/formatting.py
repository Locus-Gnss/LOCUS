"""
LOCUS Defensive Data Formatting Utilities
Module: src.ui.utils.formatting
Ensures zero NoneType formatting crashes when inspecting incomplete or anomalous telemetry.
"""

from typing import Any
import pandas as pd


def safe_float(val: Any, default: float = 0.0) -> float:
    """
    Safely cast to float without throwing TypeError on None or NaN.
    """
    try:
        if val is None or pd.isna(val):
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_int(val: Any, default: int = 0) -> int:
    """
    Safely cast to int without throwing TypeError on None or NaN.
    """
    try:
        if val is None or pd.isna(val):
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


def safe_str(val: Any, default: str = "N/A") -> str:
    """
    Safely cast to string, replacing None or empty strings with default.
    """
    if val is None or pd.isna(val):
        return default
    s = str(val).strip()
    if s == "" or s.lower() == "none" or s.lower() == "nan":
        return default
    return s
