"""
Risk adapters leveraging the strategic_alpha backend risk model.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from .config import clone_settings, get_backend_module, get_settings

risk_module = get_backend_module("risk_model")


def load_risk_result(
    ticker: str,
    start: str,
    end: str,
    shock_pct: float,
    settings: Optional[Any] = None,
) -> Any:
    """Run backend risk analysis with optional shock override."""
    base_settings = settings or get_settings()
    combined_settings = clone_settings(base_settings, shock_pct=shock_pct)
    return risk_module.analyze_risk(
        ticker=ticker, settings=combined_settings, start=start, end=end
    )


def portfolio_returns(result: Any) -> pd.Series:
    """Return portfolio returns series."""
    return result.portfolio_returns.copy()


def risk_summary(result: Any) -> dict:
    """Return dictionary summarising VaR and stress outputs."""
    return {
        "historical": result.var_results["historical"],
        "variance_covariance": result.var_results["variance_covariance"],
        "stress": result.stress_results,
    }


__all__ = ["load_risk_result", "portfolio_returns", "risk_summary"]
