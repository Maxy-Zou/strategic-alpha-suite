"""
Valuation models including DCF and relative comps.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yfinance as yf

from .config import Settings
from .utils import ensure_directory, safe_download_prices


DEFAULT_PEERS = ["NVDA", "AMD", "AVGO", "TSM", "ASML", "INTC"]


@dataclass
class DCFInputs:
    """Parameters required for the DCF model."""

    revenue: float
    revenue_growth: float
    ebit_margin: float
    tax_rate: float
    reinvestment_rate: float
    wacc: float
    terminal_growth: float
    shares_outstanding: float
    net_debt: float


def get_prices(ticker: str, start: str, end: str) -> pd.Series:
    """Download or synthesize historical prices for a ticker."""
    price_data = safe_download_prices([ticker], start, end)
    if price_data and not price_data.prices.empty:
        series = price_data.prices
        if isinstance(series, pd.DataFrame):
            if ticker in series.columns:
                return series[ticker].dropna()
            # Single column without ticker name
            return series.iloc[:, 0].rename(ticker).dropna()
        return series.squeeze().rename(ticker).dropna()

    # Fallback: deterministic synthetic price path
    dates = pd.date_range(start=start, end=end, freq="B")
    if len(dates) == 0:
        dates = pd.date_range(end=end, periods=252, freq="B")
    values = np.linspace(100.0, 150.0, len(dates))
    return pd.Series(values, index=dates, name=ticker)


def _safe_get_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:  # pragma: no cover - defensive
        return {}


def basic_fundamentals(ticker: str, price_series: pd.Series) -> DCFInputs:
    """Derive baseline DCF inputs from yfinance metadata."""
    info = _safe_get_info(ticker)
    revenue = float(info.get("totalRevenue") or 30_000_000_000)
    revenue_growth = float(info.get("revenueGrowth") or 0.12)
    ebit_margin = float(info.get("ebitdaMargins") or 0.35)
    tax_rate = float(info.get("effectiveTaxRate") or 0.15)
    reinvestment_rate = float(info.get("capitalSpendingGrowth") or 0.25)
    beta = float(info.get("beta") or 1.2)
    cost_of_debt = float(info.get("yield") or info.get("costToRevenue") or 0.045)
    shares_outstanding = float(info.get("sharesOutstanding") or 2_470_000_000)
    total_debt = float(info.get("totalDebt") or 0.0)
    cash = float(info.get("totalCash") or 0.0)
    net_debt = total_debt - cash
    price = float(price_series.iloc[-1])
    market_cap = price * shares_outstanding

    risk_free_rate = 0.04
    market_return = 0.09
    cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)

    enterprise_value = market_cap + net_debt
    debt_share = max(total_debt, 0.0)
    equity_share = max(market_cap, 1.0)
    total_capital = debt_share + equity_share

    if total_capital == 0:
        wacc = cost_of_equity
    else:
        wacc = (
            cost_of_equity * (equity_share / total_capital)
            + cost_of_debt * (1 - tax_rate) * (debt_share / total_capital)
        )

    terminal_growth = float(info.get("fiveYearAvgDividendYield") or 0.03)

    return DCFInputs(
        revenue=revenue,
        revenue_growth=revenue_growth,
        ebit_margin=ebit_margin,
        tax_rate=tax_rate,
        reinvestment_rate=reinvestment_rate,
        wacc=wacc,
        terminal_growth=terminal_growth,
        shares_outstanding=shares_outstanding,
        net_debt=net_debt,
    )


def dcf_model(inputs: DCFInputs, years: int = 5) -> dict:
    """Run a simplified FCFF DCF."""
    revenue = inputs.revenue
    fcff = []
    pv_factors = []
    for year in range(1, years + 1):
        revenue *= 1 + inputs.revenue_growth
        ebit = revenue * inputs.ebit_margin
        tax = ebit * inputs.tax_rate
        nopat = ebit - tax
        reinvestment = revenue * inputs.reinvestment_rate
        free_cash_flow = nopat - reinvestment
        fcff.append(free_cash_flow)
        pv_factors.append(1 / ((1 + inputs.wacc) ** year))

    fcff_series = pd.Series(fcff, index=[f"Year {i}" for i in range(1, years + 1)])
    pv_series = fcff_series * pv_factors
    terminal_cash_flow = fcff_series.iloc[-1] * (1 + inputs.terminal_growth)
    terminal_value = terminal_cash_flow / (inputs.wacc - inputs.terminal_growth)
    terminal_pv = terminal_value / ((1 + inputs.wacc) ** years)

    enterprise_value = pv_series.sum() + terminal_pv
    equity_value = enterprise_value - inputs.net_debt
    intrinsic_value_per_share = equity_value / max(inputs.shares_outstanding, 1.0)

    wacc_values = np.array(
        [
            max(inputs.wacc - 0.02, 0.01),
            inputs.wacc,
            inputs.wacc + 0.02,
        ]
    )
    growth_values = np.array(
        [
            inputs.terminal_growth - 0.01,
            inputs.terminal_growth,
            inputs.terminal_growth + 0.01,
        ]
    )

    sensitivity = pd.DataFrame(
        index=[f"WACC {wacc:.2%}" for wacc in wacc_values],
        columns=[f"g {growth:.2%}" for growth in growth_values],
        dtype=float,
    )

    for wacc in wacc_values:
        for g in growth_values:
            if wacc <= g:
                value = math.nan
            else:
                tv = (fcff_series.iloc[-1] * (1 + g)) / (wacc - g)
                pv = sum(fcff_series / ((1 + wacc) ** np.arange(1, years + 1)))
                value = (pv + tv / ((1 + wacc) ** years) - inputs.net_debt) / max(
                    inputs.shares_outstanding, 1.0
                )
            sensitivity.loc[f"WACC {wacc:.2%}", f"g {g:.2%}"] = value

    return {
        "fcff": fcff_series.to_dict(),
        "present_value": pv_series.to_dict(),
        "terminal_value": float(terminal_value),
        "enterprise_value": float(enterprise_value),
        "equity_value": float(equity_value),
        "equity_value_per_share": float(intrinsic_value_per_share),
        "sensitivity": sensitivity,
    }


def comps_table(
    target_ticker: str,
    peer_tickers: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Construct a relative valuation comps table."""
    tickers = list(dict.fromkeys([target_ticker] + list(peer_tickers or DEFAULT_PEERS)))
    records = []

    for ticker in tickers:
        info = _safe_get_info(ticker)
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if price is None:
            try:
                price = yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1]
            except Exception:  # pragma: no cover - defensive
                price = np.nan

        shares = info.get("sharesOutstanding") or np.nan
        market_cap = info.get("marketCap") or (price * shares if price and shares else np.nan)
        total_debt = info.get("totalDebt") or 0.0
        cash = info.get("totalCash") or 0.0
        net_debt = total_debt - cash
        ev = market_cap + net_debt if not np.isnan(market_cap) else np.nan
        ebitda = info.get("ebitda") or np.nan
        revenue = info.get("totalRevenue") or np.nan
        eps = info.get("trailingEps") or np.nan

        record = {
            "ticker": ticker,
            "price": price,
            "market_cap": market_cap,
            "net_debt": net_debt,
            "enterprise_value": ev,
            "pe": price / eps if eps and eps > 0 else np.nan,
            "ev_ebitda": ev / ebitda if ev and ebitda and ebitda != 0 else np.nan,
            "ps": price / (revenue / shares) if price and revenue and shares else np.nan,
        }
        records.append(record)

    df = pd.DataFrame(records)
    return df


@dataclass
class ValuationResult:
    """Aggregate valuation outputs."""

    price_series: pd.Series
    dcf_summary: dict
    comps: pd.DataFrame
    dcf_sensitivity_path: Path
    comps_path: Path


def run_valuation(
    ticker: str,
    settings: Settings,
    start: str,
    end: str,
    peers: Iterable[str] | None = None,
) -> ValuationResult:
    """Execute valuation workflow and persist artifacts."""
    prices = get_prices(ticker, start, end)
    inputs = basic_fundamentals(ticker, prices)
    dcf_summary = dcf_model(inputs)

    comps_df = comps_table(ticker, peers or settings.risk_peer_tickers)

    dcf_sens_path = settings.artifacts_dir / "dcf_sensitivity.csv"
    comps_path = settings.artifacts_dir / "comps_table.csv"

    ensure_directory(dcf_sens_path.parent)
    dcf_summary["sensitivity"].to_csv(dcf_sens_path)
    comps_df.to_csv(comps_path, index=False)

    return ValuationResult(
        price_series=prices,
        dcf_summary=dcf_summary,
        comps=comps_df,
        dcf_sensitivity_path=dcf_sens_path,
        comps_path=comps_path,
    )


__all__ = [
    "DEFAULT_PEERS",
    "DCFInputs",
    "ValuationResult",
    "basic_fundamentals",
    "comps_table",
    "dcf_model",
    "get_prices",
    "run_valuation",
]
