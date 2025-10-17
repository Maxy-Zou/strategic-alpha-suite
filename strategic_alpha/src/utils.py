"""
Utility helpers for data loading, plotting, and external API access.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from rich.console import Console

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class PriceData:
    """Container for downloaded price data."""

    prices: pd.DataFrame
    info: dict[str, dict[str, float | str]]


def load_csv(path: Path, parse_dates: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Load a CSV file into a DataFrame.

    Args:
        path: Path to the CSV file.
        parse_dates: Columns to parse as dates.

    Returns:
        DataFrame with loaded data.
    """
    if not path.exists():
        raise FileNotFoundError(f"Sample dataset not found: {path}")
    return pd.read_csv(path, parse_dates=parse_dates)


def ensure_directory(path: Path) -> None:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def save_plot(fig: plt.Figure, path: Path) -> Path:
    """Persist a Matplotlib figure to disk."""
    ensure_directory(path.parent)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
    logger.info("Saved plot to %s", path)
    return path


def safe_download_prices(
    tickers: Iterable[str], start: str, end: str
) -> PriceData | None:
    """
    Download historical price data from yfinance.

    Returns:
        PriceData with adjusted close prices and ticker info, or None on failure.
    """
    tickers_list = list(tickers)
    try:
        data = yf.download(
            tickers=tickers_list,
            start=start,
            end=end,
            auto_adjust=True,
            progress=False,
            actions=False,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("yfinance download failed: %s", exc)
        console.print(
            "[yellow]Warning[/yellow]: yfinance download failed; proceeding with fallback data."
        )
        return None

    if data.empty:
        logger.warning("No data returned for tickers: %s", tickers_list)
        return None

    if isinstance(data.columns, pd.MultiIndex):
        if ("Adj Close", tickers_list[0]) in data.columns:
            prices = data["Adj Close"]
        elif ("Close", tickers_list[0]) in data.columns:
            prices = data["Close"]
        else:
            prices = data.xs("Adj Close", level=0, axis=1, drop_level=True)
    else:
        if "Adj Close" in data.columns:
            prices = data["Adj Close"]
        elif "Close" in data.columns:
            prices = data["Close"]
        else:
            prices = data.iloc[:, 0]
        prices = prices.to_frame(name=tickers_list[0])

    prices = prices.dropna(how="all")

    info: dict[str, dict[str, float | str]] = {}
    for ticker in tickers_list:
        try:
            yf_ticker = yf.Ticker(ticker)
            info[ticker] = yf_ticker.info or {}
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Failed to fetch info for %s: %s", ticker, exc)
            info[ticker] = {}

    return PriceData(prices=prices, info=info)


def read_text_file(path: Path) -> str:
    """Read a text file safely."""
    if not path.exists():
        raise FileNotFoundError(f"Sample text file not found: {path}")
    return path.read_text(encoding="utf-8")


def warn_missing_api(service: str, fallback: str) -> None:
    """Emit a console warning when falling back to sample data."""
    console.print(
        f"[yellow]Warning[/yellow]: {service} credentials not found. Using fallback data from {fallback}."
    )
