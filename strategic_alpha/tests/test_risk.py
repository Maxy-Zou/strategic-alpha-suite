import sys
from pathlib import Path

# Add project root to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

from src.config import Settings
from src.risk_model import analyze_risk, compute_var_cov, compute_var_historical
from src.utils import PriceData


def test_var_functions_consistent():
    returns = pd.Series(np.linspace(-0.02, 0.02, 100))
    var_hist = compute_var_historical(returns, 0.95)
    var_cov = compute_var_cov(returns, 0.95)
    assert var_hist >= 0
    assert isinstance(var_cov, float)


def test_analyze_risk_synthetic_data(monkeypatch, tmp_path):
    dates = pd.date_range("2022-01-01", periods=252, freq="B")
    data = pd.DataFrame(
        {
            "TEST": np.linspace(100, 130, len(dates)),
            "PEER": np.linspace(90, 105, len(dates)),
        },
        index=dates,
    )

    def fake_download(tickers, start, end):
        return PriceData(prices=data[tickers], info={ticker: {} for ticker in tickers})

    monkeypatch.setattr("src.risk_model.safe_download_prices", fake_download)

    settings = Settings(
        artifacts_dir=tmp_path / "artifacts",
        reports_dir=tmp_path / "reports",
        risk_peer_tickers=["PEER"],
        supply_shock_tickers=["PEER"],
        shock_pct=-0.1,
    )
    result = analyze_risk(
        ticker="TEST", settings=settings, start="2022-01-01", end="2022-12-31"
    )
    assert result.var_path.exists()
    assert result.stress_path.exists()
    assert "historical" in result.var_results
