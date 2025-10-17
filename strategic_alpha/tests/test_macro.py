import pandas as pd

from src.config import Settings
from src.macro_analysis import macro_snapshot


def test_macro_snapshot_uses_fallback(tmp_path, monkeypatch):
    settings = Settings(
        artifacts_dir=tmp_path / "artifacts",
        reports_dir=tmp_path / "reports",
    )
    result = macro_snapshot(settings=settings, start="2022-01-01", end="2023-12-31")
    assert isinstance(result.metrics, dict)
    assert set(result.metrics.keys()) == {
        "cpi_yoy",
        "unemployment_rate",
        "fed_funds_rate",
        "industrial_production_yoy",
    }
    assert result.plot_path.exists()
    assert isinstance(result.data, pd.DataFrame)
