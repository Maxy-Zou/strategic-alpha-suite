"""
Risk modeling: VaR calculations and stress scenarios.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable

import numpy as np
import pandas as pd
from rich.console import Console
from scipy.stats import norm

from .config import Settings, get_settings
from .utils import ensure_directory, safe_download_prices

console = Console()


def _synthesize_price_path(ticker: str, start: str, end: str) -> pd.Series:
    dates = pd.date_range(start=start, end=end, freq="B")
    if len(dates) < 100:
        dates = pd.date_range(end=end, periods=252, freq="B")
    base = np.linspace(100.0, 120.0, len(dates))
    seasonal = 2.0 * np.sin(np.linspace(0, 3.14, len(dates)))
    series = base + seasonal
    return pd.Series(series, index=dates, name=ticker)


def _get_price_frame(tickers: Iterable[str], start: str, end: str) -> pd.DataFrame:
    price_data = safe_download_prices(tickers, start, end)
    if price_data and not price_data.prices.empty:
        if isinstance(price_data.prices.columns, pd.MultiIndex):
            prices = price_data.prices["Adj Close"]
        else:
            prices = price_data.prices
        return prices.dropna(how="all")

    console.print(
        "[yellow]Warning[/yellow]: Using synthetic price paths due to data unavailability."
    )
    frames = [_synthesize_price_path(ticker, start, end) for ticker in tickers]
    return pd.concat(frames, axis=1)


def compute_var_historical(returns: pd.Series, confidence: float) -> float:
    """Historical VaR at specified confidence level."""
    percentile = np.percentile(returns, (1 - confidence) * 100)
    return -float(percentile)


def compute_var_cov(returns: pd.Series, confidence: float) -> float:
    """Variance-covariance VaR assuming normality."""
    mean = returns.mean()
    std = returns.std(ddof=0)
    z = norm.ppf(1 - confidence)
    return -float(mean + z * std)


def _portfolio_weights(target: str, peers: Iterable[str]) -> pd.Series:
    peers_list = list(peers)
    total_peers = len(peers_list)
    peer_weight = 0.4 / total_peers if total_peers else 0.0
    weights = {target: 0.6}
    weights.update({peer: peer_weight for peer in peers_list})
    return pd.Series(weights)


def stress_test(
    prices: pd.DataFrame,
    weights: pd.Series,
    shock_pct: float,
    shocked_tickers: Iterable[str],
) -> Dict[str, float | dict]:
    """Apply a deterministic shock to selected tickers and measure portfolio loss."""
    latest_prices = prices.iloc[-1]
    shocked_prices = latest_prices.copy()
    ticker_impacts: Dict[str, float] = {}
    for ticker in shocked_tickers:
        if ticker in shocked_prices.index:
            shocked_prices[ticker] *= 1 + shock_pct
            ticker_impacts[ticker] = shock_pct
    price_change = (shocked_prices - latest_prices) / latest_prices
    aligned = price_change.reindex(weights.index).fillna(0.0)
    portfolio_loss = float((aligned * weights).sum())

    return {
        "shock_pct": shock_pct,
        "portfolio_loss": portfolio_loss,
        "ticker_impacts": ticker_impacts,
    }


@dataclass
class RiskResult:
    """Aggregate risk analysis outputs."""

    returns: pd.DataFrame
    portfolio_returns: pd.Series
    var_results: dict
    stress_results: dict
    var_path: Path
    stress_path: Path


def analyze_risk(
    ticker: str,
    settings: Settings | None = None,
    start: str = "2021-01-01",
    end: str = "2023-12-31",
) -> RiskResult:
    """Compute risk metrics, VaR, and stress scenarios."""
    if settings is None:
        settings = get_settings()

    peers = settings.risk_peer_tickers
    tickers = [ticker] + [p for p in peers if p != ticker]
    prices = _get_price_frame(tickers, start, end)

    returns = prices.pct_change().dropna(how="all")
    if len(returns) < 250:
        console.print(
            "[yellow]Warning[/yellow]: Insufficient return history; results may be noisy."
        )

    weights = _portfolio_weights(ticker, [p for p in peers if p != ticker])
    weights = weights.reindex(returns.columns).fillna(0.0)
    portfolio_returns = returns.dot(weights)

    historical_var = {
        "var_95": compute_var_historical(portfolio_returns, 0.95),
        "var_99": compute_var_historical(portfolio_returns, 0.99),
    }
    variance_var = {
        "var_95": compute_var_cov(portfolio_returns, 0.95),
        "var_99": compute_var_cov(portfolio_returns, 0.99),
    }

    stress_results = stress_test(
        prices=prices,
        weights=weights,
        shock_pct=settings.shock_pct,
        shocked_tickers=settings.supply_shock_tickers,
    )

    var_results = {"historical": historical_var, "variance_covariance": variance_var}

    var_path = settings.artifacts_dir / "var_results.json"
    stress_path = settings.artifacts_dir / "stress_results.json"
    ensure_directory(var_path.parent)

    with var_path.open("w", encoding="utf-8") as f:
        json.dump(var_results, f, indent=2)
    with stress_path.open("w", encoding="utf-8") as f:
        json.dump(stress_results, f, indent=2)

    return RiskResult(
        returns=returns,
        portfolio_returns=portfolio_returns,
        var_results=var_results,
        stress_results=stress_results,
        var_path=var_path,
        stress_path=stress_path,
    )


__all__ = [
    "RiskResult",
    "analyze_risk",
    "compute_var_cov",
    "compute_var_historical",
    "stress_test",
]
