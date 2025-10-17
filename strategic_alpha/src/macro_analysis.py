"""
Macro analysis module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
from rich.console import Console

from .config import Settings
from .utils import load_csv, save_plot, warn_missing_api

console = Console()

FRED_SERIES = {
    "cpi": "CPIAUCSL",
    "unemployment": "UNRATE",
    "fed_funds": "FEDFUNDS",
    "industrial_production": "INDPRO",
}


@dataclass
class MacroResult:
    """Container for macro analysis outputs."""

    data: pd.DataFrame
    metrics: dict[str, float]
    plot_path: Path


def _fetch_from_fred(
    settings: Settings, start: str, end: Optional[str]
) -> pd.DataFrame | None:
    if not settings.fred_api_key:
        warn_missing_api("FRED", "data/macro/sample_macro.csv")
        return None

    try:
        from fredapi import Fred

        fred = Fred(api_key=settings.fred_api_key)
    except Exception as exc:  # pragma: no cover - defensive
        console.print(
            f"[yellow]Warning[/yellow]: FRED fetch failed ({exc}). Using fallback data."
        )
        return None

    data_frames: dict[str, pd.Series] = {}
    for label, series_id in FRED_SERIES.items():
        try:
            series = fred.get_series(series_id, observation_start=start, observation_end=end)
            if series is None:
                continue
            series = pd.Series(series)
            series.index = pd.to_datetime(series.index)
            data_frames[label] = series
        except Exception as exc:  # pragma: no cover - defensive
            console.print(
                f"[yellow]Warning[/yellow]: Failed to load {series_id} from FRED ({exc})."
            )

    if not data_frames:
        return None

    df = pd.DataFrame(data_frames).sort_index()

    df["cpi_yoy"] = df["cpi"].pct_change(12) * 100
    df["industrial_production_yoy"] = df["industrial_production"].pct_change(12) * 100
    df.rename(
        columns={
            "unemployment": "unemployment_rate",
            "fed_funds": "fed_funds_rate",
        },
        inplace=True,
    )
    df = df[
        [
            "cpi_yoy",
            "unemployment_rate",
            "fed_funds_rate",
            "industrial_production_yoy",
        ]
    ].dropna()
    return df


def _load_fallback(settings: Settings) -> pd.DataFrame:
    csv_path = settings.data_dir / "macro" / "sample_macro.csv"
    df = load_csv(csv_path, parse_dates=["date"])
    df = df.set_index("date").sort_index()
    df.columns = [
        "cpi_yoy",
        "unemployment_rate",
        "fed_funds_rate",
        "industrial_production_yoy",
    ]
    return df


def macro_snapshot(
    settings: Settings, start: str = "2015-01-01", end: Optional[str] = None
) -> MacroResult:
    """
    Provide a macro snapshot using FRED if available, falling back to sample data.
    """

    if end is None:
        end = datetime.utcnow().strftime("%Y-%m-%d")

    data = _fetch_from_fred(settings, start=start, end=end)
    if data is None or data.empty:
        data = _load_fallback(settings)

    latest = data.iloc[-1]
    metrics = {
        "cpi_yoy": float(latest["cpi_yoy"]),
        "unemployment_rate": float(latest["unemployment_rate"]),
        "fed_funds_rate": float(latest["fed_funds_rate"]),
        "industrial_production_yoy": float(latest["industrial_production_yoy"]),
    }

    normalized = data.copy()

    def _zscore(col: pd.Series) -> pd.Series:
        std = col.std(ddof=0)
        if std == 0 or pd.isna(std):
            return col - col.mean()
        return (col - col.mean()) / std

    normalized = normalized.apply(_zscore)

    fig, ax = plt.subplots(figsize=(10, 5))
    normalized.plot(ax=ax)
    ax.set_title("Macro Indicator Z-Scores")
    ax.set_ylabel("Z-Score")
    ax.legend(loc="best")

    plot_path = settings.artifacts_dir / "macro.png"
    save_plot(fig, plot_path)

    return MacroResult(data=data, metrics=metrics, plot_path=plot_path)


__all__ = ["MacroResult", "macro_snapshot"]
