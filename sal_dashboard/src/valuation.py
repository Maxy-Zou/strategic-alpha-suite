"""
Valuation helpers wrapping the strategic_alpha backend valuation module.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple

import pandas as pd

from .config import get_backend_module, get_settings

valuation_module = get_backend_module("valuation")


def load_valuation_result(
    ticker: str,
    start: str,
    end: str,
    peers: Optional[Iterable[str]] = None,
    settings: Optional[Any] = None,
) -> Any:
    """Execute backend valuation workflow."""
    settings = settings or get_settings()
    peers = list(peers or settings.risk_peer_tickers)
    return valuation_module.run_valuation(
        ticker=ticker, settings=settings, start=start, end=end, peers=peers
    )


def base_dcf_inputs(
    ticker: str,
    start: str,
    end: str,
) -> Tuple[pd.Series, Any]:
    """Return price series and baseline DCF inputs from backend fundamentals."""
    price_series = valuation_module.get_prices(ticker, start, end)
    inputs = valuation_module.basic_fundamentals(ticker, price_series)
    return price_series, inputs


def override_dcf_inputs(base_inputs: Any, overrides: Dict[str, float]) -> Any:
    """Apply user-specified overrides to DCF inputs."""
    params = {field: getattr(base_inputs, field) for field in base_inputs.__dataclass_fields__}
    params.update(overrides)
    return valuation_module.DCFInputs(**params)


def run_dcf_model(inputs: Any) -> Dict[str, Any]:
    """Run backend DCF model with provided inputs."""
    result = valuation_module.dcf_model(inputs)
    return result


def comps_dataframe(ticker: str, peers: Iterable[str]) -> pd.DataFrame:
    """Retrieve comparable multiples table."""
    df = valuation_module.comps_table(target_ticker=ticker, peer_tickers=peers)
    return df


def peer_percentiles(df: pd.DataFrame, ticker: str) -> Dict[str, Optional[float]]:
    """Compute percentile positioning of the target within peer set."""
    if df.empty:
        return {"pe": None, "ev_ebitda": None, "ps": None}

    target_row = df[df["ticker"] == ticker]
    if target_row.empty:
        return {"pe": None, "ev_ebitda": None, "ps": None}

    target_series = target_row.iloc[0]
    percentiles: Dict[str, Optional[float]] = {}
    for column in ["pe", "ev_ebitda", "ps"]:
        series = df[column].dropna()
        value = target_series[column]
        if series.empty or pd.isna(value):
            percentiles[column] = None
        else:
            # Append value to align index if missing due to duplicates
            rank = series.rank(pct=True)
            try:
                percentiles[column] = float(rank.loc[target_row.index[0]])
            except KeyError:
                percentiles[column] = None
    return percentiles


__all__ = [
    "load_valuation_result",
    "base_dcf_inputs",
    "override_dcf_inputs",
    "run_dcf_model",
    "comps_dataframe",
    "peer_percentiles",
]
