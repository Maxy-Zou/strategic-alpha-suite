"""
Macro data accessors that wrap the strategic_alpha backend.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd

from .config import get_backend_module, get_settings

macro_module = get_backend_module("macro_analysis")


def load_macro_snapshot(
    start: str = "2015-01-01",
    end: Optional[str] = None,
    settings: Optional[Any] = None,
) -> Any:
    """Fetch macro snapshot using backend module."""
    if end is None:
        end = datetime.utcnow().strftime("%Y-%m-%d")

    settings = settings or get_settings()
    return macro_module.macro_snapshot(settings=settings, start=start, end=end)


def macro_dataframe(result: Any) -> pd.DataFrame:
    """Return macro time series data."""
    return result.data.copy()


def macro_commentary(metrics: Dict[str, float]) -> str:
    """
    Generate lightweight text commentary from macro metrics.
    """
    inflation = metrics.get("cpi_yoy", 0.0)
    unemployment = metrics.get("unemployment_rate", 0.0)
    fed_funds = metrics.get("fed_funds_rate", 0.0)
    ip = metrics.get("industrial_production_yoy", 0.0)

    lines = [
        f"Inflation prints at {inflation:.2f}%, suggesting "
        f"{'persistent pressures' if inflation > 3.0 else 'a moderating trend'}.",
        f"Unemployment at {unemployment:.2f}% signals "
        f"{'tight labor conditions' if unemployment < 4 else 'a softening jobs market'}.",
        f"Policy stance remains {'restrictive' if fed_funds > 4 else 'accommodative'} "
        f"with the Fed Funds Rate at {fed_funds:.2f}%.",
        f"Industrial production YoY of {ip:.2f}% indicates "
        f"{'expansion in output' if ip > 0 else 'contraction risk'}."
    ]
    return " ".join(lines)


__all__ = ["load_macro_snapshot", "macro_dataframe", "macro_commentary"]
