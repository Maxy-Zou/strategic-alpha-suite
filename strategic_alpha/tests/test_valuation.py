import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pandas as pd

from src.config import Settings
from src.valuation import DCFInputs, dcf_model, run_valuation


def test_dcf_model_outputs_consistent_values():
    inputs = DCFInputs(
        revenue=10_000_000_000,
        revenue_growth=0.1,
        ebit_margin=0.3,
        tax_rate=0.18,
        reinvestment_rate=0.2,
        wacc=0.08,
        terminal_growth=0.03,
        shares_outstanding=1_000_000_000,
        net_debt=500_000_000,
    )
    result = dcf_model(inputs)
    assert "equity_value_per_share" in result
    assert result["terminal_value"] > 0
    assert isinstance(result["sensitivity"], pd.DataFrame)


def test_run_valuation_monkeypatch(monkeypatch, tmp_path):
    fake_info = {
        "totalRevenue": 12_000_000_000,
        "revenueGrowth": 0.12,
        "ebitdaMargins": 0.35,
        "effectiveTaxRate": 0.16,
        "capitalSpendingGrowth": 0.25,
        "beta": 1.1,
        "yield": 0.04,
        "sharesOutstanding": 1_200_000_000,
        "totalDebt": 2_000_000_000,
        "totalCash": 1_000_000_000,
        "fiveYearAvgDividendYield": 0.03,
        "currentPrice": 100.0,
        "marketCap": 120_000_000_000,
        "ebitda": 4_000_000_000,
        "totalRevenue": 12_000_000_000,
        "trailingEps": 5.0,
    }

    def fake_download(tickers, start, end):
        dates = pd.date_range(start=start, end=end, freq="B")
        prices = pd.DataFrame(
            np.linspace(90, 110, len(dates)), index=dates, columns=[tickers[0]]
        )

        class DummyData:
            def __init__(self, prices):
                self.prices = prices
                self.info = {tickers[0]: fake_info}

        return DummyData(prices=prices)

    monkeypatch.setattr("src.valuation.safe_download_prices", fake_download)
    monkeypatch.setattr("src.valuation._safe_get_info", lambda ticker: fake_info)

    settings = Settings(
        artifacts_dir=tmp_path / "artifacts",
        reports_dir=tmp_path / "reports",
    )
    result = run_valuation("TEST", settings, "2022-01-01", "2022-12-31")
    assert result.dcf_sensitivity_path.exists()
    assert result.comps_path.exists()
    assert result.price_series.name == "TEST"
