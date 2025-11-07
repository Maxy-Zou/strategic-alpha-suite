"""Shared pytest fixtures for Strategic Alpha tests."""

import sys
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any


@pytest.fixture
def mock_yfinance_ticker_info() -> Dict[str, Any]:
    """Mock yfinance Ticker().info response."""
    return {
        'longName': 'NVIDIA Corporation',
        'symbol': 'NVDA',
        'currentPrice': 450.25,
        'marketCap': 1_110_000_000_000,
        'beta': 1.85,
        'trailingPE': 65.5,
        'forwardPE': 42.3,
        'priceToSalesTrailing12Months': 28.5,
        'enterpriseValue': 1_100_000_000_000,
        'enterpriseToEbitda': 55.2,
        'totalRevenue': 39_000_000_000,
        'revenueGrowth': 0.265,
        'ebitdaMargins': 0.52,
        'profitMargins': 0.45,
        'returnOnEquity': 0.85,
        'totalCash': 16_000_000_000,
        'totalDebt': 9_000_000_000,
        'freeCashflow': 18_000_000_000,
        'operatingCashflow': 22_000_000_000,
        'bookValue': 15.50,
        'sharesOutstanding': 2_460_000_000,
        'fiftyTwoWeekLow': 360.00,
        'fiftyTwoWeekHigh': 502.66,
        'industry': 'Semiconductors',
        'sector': 'Technology',
    }


@pytest.fixture
def mock_price_history() -> pd.DataFrame:
    """Mock historical price data."""
    dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
    np.random.seed(42)

    # Generate realistic price movement
    returns = np.random.normal(0.001, 0.025, len(dates))
    prices = 400 * np.exp(np.cumsum(returns))

    return pd.DataFrame({
        'Date': dates,
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.randint(20_000_000, 50_000_000, len(dates)),
        'Adj Close': prices,
    }).set_index('Date')


@pytest.fixture
def sample_macro_data() -> pd.DataFrame:
    """Sample macro economic data."""
    dates = pd.date_range('2022-01-31', periods=24, freq='ME')

    return pd.DataFrame({
        'date': dates,
        'cpi_yoy': [7.5, 7.9, 8.5, 8.3, 8.6, 9.1, 9.0, 8.5, 8.2, 7.7, 7.1, 6.5,
                    6.4, 6.0, 5.0, 4.9, 4.0, 3.7, 3.2, 3.1, 3.4, 3.5, 3.2, 2.9],
        'unemp': [4.0, 3.8, 3.6, 3.6, 3.6, 3.6, 3.5, 3.7, 3.5, 3.7, 3.7, 3.5,
                  3.4, 3.4, 3.4, 3.8, 3.8, 3.9, 3.9, 3.7, 3.8, 3.8, 3.9, 3.7],
        'ffr': [0.08, 0.08, 0.33, 0.83, 0.83, 1.58, 2.33, 2.33, 3.08, 3.83, 4.33, 4.33,
                4.58, 4.58, 4.83, 5.08, 5.08, 5.33, 5.33, 5.33, 5.33, 5.33, 5.33, 5.33],
        'ip': [105.3, 105.1, 105.5, 105.2, 105.8, 106.1, 106.3, 106.0, 106.2, 106.5,
               106.8, 106.4, 106.7, 106.9, 107.2, 107.1, 107.5, 107.8, 107.6, 107.9,
               108.2, 108.5, 108.3, 108.7],
    })


@pytest.fixture
def sample_supply_chain_edges() -> pd.DataFrame:
    """Sample supply chain relationships."""
    return pd.DataFrame({
        'supplier': ['TSMC', 'ASML', 'TSMC', 'Samsung', 'SK Hynix', 'Intel', 'AMD', 'TSMC'],
        'customer': ['NVDA', 'TSMC', 'AMD', 'NVDA', 'NVDA', 'NVDA', 'NVDA', 'Apple'],
        'relationship': ['Advanced Foundry', 'EUV Lithography', 'Foundry', 'Memory',
                        'HBM Memory', 'CPU Supply', 'GPU Supply', 'Foundry'],
        'country': ['Taiwan', 'Netherlands', 'Taiwan', 'South Korea', 'South Korea',
                   'US', 'US', 'Taiwan'],
        'weight': [0.95, 0.98, 0.85, 0.75, 0.90, 0.60, 0.50, 0.92],
    })


@pytest.fixture
def sample_peer_tickers() -> list[str]:
    """Sample peer company tickers."""
    return ['NVDA', 'AMD', 'INTC', 'TSM', 'AVGO', 'ASML']


@pytest.fixture
def sample_dcf_inputs() -> Dict[str, float]:
    """Sample DCF model inputs."""
    return {
        'revenue': 39_000_000_000,
        'revenue_growth': 0.25,
        'ebit_margin': 0.52,
        'tax_rate': 0.15,
        'reinvestment_rate': 0.25,
        'terminal_growth': 0.03,
        'risk_free_rate': 0.04,
        'market_return': 0.09,
        'beta': 1.85,
        'debt': 9_000_000_000,
        'cash': 16_000_000_000,
        'shares_outstanding': 2_460_000_000,
    }


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create temporary data directory structure."""
    data_dir = tmp_path / "data"
    (data_dir / "macro").mkdir(parents=True)
    (data_dir / "supply_chain").mkdir(parents=True)
    (data_dir / "financials").mkdir(parents=True)
    return data_dir


@pytest.fixture
def temp_artifacts_dir(tmp_path: Path) -> Path:
    """Create temporary artifacts directory."""
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    return artifacts_dir


@pytest.fixture
def mock_fred_api_response() -> Dict[str, pd.Series]:
    """Mock FRED API responses for economic indicators."""
    dates = pd.date_range('2022-01-31', periods=24, freq='ME')

    return {
        'CPIAUCSL': pd.Series([280, 283, 287, 289, 291, 296, 296, 295, 296, 298, 298, 296,
                               297, 298, 299, 301, 304, 305, 306, 307, 308, 309, 308, 307],
                              index=dates),
        'UNRATE': pd.Series([4.0, 3.8, 3.6, 3.6, 3.6, 3.6, 3.5, 3.7, 3.5, 3.7, 3.7, 3.5,
                            3.4, 3.4, 3.4, 3.8, 3.8, 3.9, 3.9, 3.7, 3.8, 3.8, 3.9, 3.7],
                           index=dates),
        'DFF': pd.Series([0.08, 0.08, 0.33, 0.83, 0.83, 1.58, 2.33, 2.33, 3.08, 3.83, 4.33, 4.33,
                         4.58, 4.58, 4.83, 5.08, 5.08, 5.33, 5.33, 5.33, 5.33, 5.33, 5.33, 5.33],
                        index=dates),
        'INDPRO': pd.Series([105.3, 105.1, 105.5, 105.2, 105.8, 106.1, 106.3, 106.0, 106.2, 106.5,
                            106.8, 106.4, 106.7, 106.9, 107.2, 107.1, 107.5, 107.8, 107.6, 107.9,
                            108.2, 108.5, 108.3, 108.7],
                           index=dates),
    }


@pytest.fixture
def mock_sec_risk_factors() -> str:
    """Mock SEC 10-K risk factors text."""
    return """
    Item 1A. Risk Factors

    Our business is subject to a number of risks, including:

    Supply Chain Risks:
    We rely heavily on Taiwan Semiconductor Manufacturing Company (TSMC) for manufacturing our GPUs.
    Any disruption to TSMC's operations, including from natural disasters, geopolitical tensions,
    or other factors, could severely impact our ability to meet customer demand.

    Competitive Risks:
    The semiconductor industry is highly competitive. We face competition from AMD, Intel, and other
    companies. If we fail to innovate or lose market share, our financial results could be materially impacted.

    Regulatory Risks:
    Export controls and trade restrictions, particularly related to sales to China, could limit our
    addressable market and impact revenue growth.

    Demand Risks:
    Demand for our products is driven by AI, gaming, and data center markets. Any slowdown in these
    markets could reduce demand for our products and adversely affect our financial performance.
    """


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv('FRED_API_KEY', 'test_fred_key_123')
    monkeypatch.setenv('SEC_API_KEY', 'test_sec_key_456')
    monkeypatch.setenv('SHOCK_PCT', '-0.10')
    monkeypatch.setenv('RISK_PEER_TICKERS', 'AMD,AVGO,TSM,ASML,INTC')


@pytest.fixture
def sample_error_log_entry() -> Dict[str, Any]:
    """Sample error log entry for database testing."""
    return {
        'error_type': 'APIError',
        'error_message': 'yfinance API rate limit exceeded',
        'stack_trace': 'Traceback (most recent call last)...',
        'context': 'Fetching NVDA quote',
        'ticker': 'NVDA',
        'timestamp': datetime.now().isoformat(),
    }


@pytest.fixture
def sample_valuation_result() -> Dict[str, Any]:
    """Sample valuation computation result."""
    return {
        'ticker': 'NVDA',
        'start_date': '2023-01-01',
        'end_date': '2024-01-01',
        'peers': ['AMD', 'INTC'],
        'dcf_value': 127_500_000_000,
        'equity_value': 134_500_000_000,
        'equity_value_per_share': 54.67,
        'current_price': 450.25,
        'upside_pct': -87.9,  # Significantly overvalued in this example
        'user_inputs': {
            'revenue_growth': 0.25,
            'terminal_growth': 0.03,
            'wacc': 0.095,
        },
    }
