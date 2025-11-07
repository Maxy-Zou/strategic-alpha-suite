import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config import Settings
from src.supply_mapping import analyze_supply_chain


def test_supply_analysis_creates_artifacts(tmp_path):
    settings = Settings(
        artifacts_dir=tmp_path / "artifacts",
        reports_dir=tmp_path / "reports",
    )
    result = analyze_supply_chain(settings)
    assert result.metrics_path.exists()
    assert result.graph_path.exists()
    assert len(result.chokepoints) == 5
    assert "betweenness" in result.metrics.columns
