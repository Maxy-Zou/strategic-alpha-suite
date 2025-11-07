"""
CLI orchestrator for strategic alpha analysis.
"""

from __future__ import annotations

from datetime import datetime, timezone

import typer
from rich.console import Console
from rich.table import Table
from tabulate import tabulate

from .config import Settings, get_settings
from .macro_analysis import macro_snapshot
from .report_generator import render_markdown_report
from .risk_model import analyze_risk
from .supply_mapping import analyze_supply_chain
from .valuation import run_valuation

app = typer.Typer(add_completion=False, help="Strategic Alpha research CLI.")
console = Console()


def _clone_settings(settings: Settings, **updates) -> Settings:
    if hasattr(settings, "model_dump"):
        payload = settings.model_dump()
    else:  # pragma: no cover - compatibility with Pydantic v1
        payload = settings.dict()  # type: ignore[attr-defined]
    payload.update({k: v for k, v in updates.items() if v is not None})
    return Settings(**payload)


@app.command()
def macro(
    ticker: str = typer.Option(
        "NVDA", "--ticker", "-t", help="Target ticker (unused, for symmetry)."),
    start: str = typer.Option("2015-01-01", "--start",
                              help="Start date for macro series."),
    end: str = typer.Option(
        datetime.now(timezone.utc).strftime("%Y-%m-%d"), "--end", help="End date."
    ),
) -> None:
    """Run macro snapshot."""
    settings = get_settings()
    result = macro_snapshot(settings=settings, start=start, end=end)
    table = Table(title="Macro Snapshot")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("CPI YoY", f"{result.metrics['cpi_yoy']:.2f}%")
    table.add_row("Unemployment Rate",
                  f"{result.metrics['unemployment_rate']:.2f}%")
    table.add_row("Fed Funds Rate", f"{result.metrics['fed_funds_rate']:.2f}%")
    table.add_row(
        "Industrial Production YoY",
        f"{result.metrics['industrial_production_yoy']:.2f}%",
    )
    console.print(table)
    console.print(f"Macro chart saved to: {result.plot_path}")


@app.command()
def supply(
    ticker: str = typer.Option(
        "NVDA", "--ticker", "-t", help="Target ticker."),
) -> None:
    """Analyze supply chain network."""
    settings = get_settings()
    result = analyze_supply_chain(settings)
    console.print("Top chokepoints (betweenness):")
    console.print(result.chokepoints[["node", "country", "betweenness"]])
    console.print(f"Supply graph saved to: {result.graph_path}")
    console.print(f"Supply metrics saved to: {result.metrics_path}")


@app.command()
def valuation(
    ticker: str = typer.Option(
        "NVDA", "--ticker", "-t", help="Target ticker."),
    start: str = typer.Option("2021-01-01", "--start",
                              help="Start date for price history."),
    end: str = typer.Option(
        datetime.now(timezone.utc).strftime("%Y-%m-%d"), "--end", help="End date."
    ),
) -> None:
    """Run valuation analysis."""
    settings = get_settings()
    result = run_valuation(
        ticker=ticker, settings=settings, start=start, end=end)
    dcf_value = result.dcf_summary["equity_value_per_share"]
    price = result.price_series.iloc[-1]
    console.print(f"DCF intrinsic value per share: ${dcf_value:.2f}")
    console.print(f"Spot price: ${price:.2f}")
    console.print(f"DCF sensitivity saved to: {result.dcf_sensitivity_path}")
    console.print(f"Relative comps saved to: {result.comps_path}")


@app.command()
def risk(
    ticker: str = typer.Option(
        "NVDA", "--ticker", "-t", help="Target ticker."),
    start: str = typer.Option("2021-01-01", "--start",
                              help="Start date for returns."),
    end: str = typer.Option(
        datetime.now(timezone.utc).strftime("%Y-%m-%d"), "--end", help="End date."
    ),
    shock_pct: float = typer.Option(
        None, "--shock-pct", help="Override shock percentage (e.g. -0.1)."),
) -> None:
    """Compute risk metrics and stress tests."""
    settings = get_settings()
    settings = _clone_settings(settings, shock_pct=shock_pct)
    result = analyze_risk(
        ticker=ticker, settings=settings, start=start, end=end)
    console.print("Historical VaR:", result.var_results["historical"])
    console.print("Variance-Covariance VaR:",
                  result.var_results["variance_covariance"])
    console.print("Stress test:", result.stress_results)
    console.print(f"VaR saved to: {result.var_path}")
    console.print(f"Stress results saved to: {result.stress_path}")


@app.command(name="run")
def run(
    ticker: str = typer.Option(
        "NVDA", "--ticker", "-t", help="Target ticker."),
    start: str = typer.Option("2021-01-01", "--start",
                              help="Start date for analysis."),
    end: str = typer.Option(
        datetime.now(timezone.utc).strftime("%Y-%m-%d"), "--end", help="End date."
    ),
    shock_pct: float = typer.Option(
        None, "--shock-pct", help="Override supply shock."),
) -> None:
    """Run the full strategic alpha pipeline (alias for 'full')."""
    full(ticker=ticker, start=start, end=end, shock_pct=shock_pct)


@app.command()
def full(
    ticker: str = typer.Option(
        "NVDA", "--ticker", "-t", help="Target ticker."),
    start: str = typer.Option("2021-01-01", "--start",
                              help="Start date for analysis."),
    end: str = typer.Option(
        datetime.now(timezone.utc).strftime("%Y-%m-%d"), "--end", help="End date."
    ),
    shock_pct: float = typer.Option(
        None, "--shock-pct", help="Override supply shock."),
) -> None:
    """Run the full strategic alpha pipeline."""
    settings = get_settings()
    settings = _clone_settings(settings, shock_pct=shock_pct)

    macro_result = macro_snapshot(
        settings=settings, start="2015-01-01", end=end)
    supply_result = analyze_supply_chain(settings)
    valuation_result = run_valuation(
        ticker=ticker, settings=settings, start=start, end=end
    )
    risk_result = analyze_risk(
        ticker=ticker, settings=settings, start=start, end=end)

    report_path = render_markdown_report(
        ticker=ticker,
        settings=settings,
        macro=macro_result,
        supply=supply_result,
        valuation=valuation_result,
        risk=risk_result,
    )

    summary_rows = [
        ["Metric", "Value"],
        ["Market Price", f"${valuation_result.price_series.iloc[-1]:.2f}"],
        [
            "DCF Value",
            f"${valuation_result.dcf_summary['equity_value_per_share']:.2f}",
        ],
        [
            "VaR 95%",
            f"{risk_result.var_results['historical']['var_95']:.4f}",
        ],
        [
            "VaR 99%",
            f"{risk_result.var_results['historical']['var_99']:.4f}",
        ],
        [
            "Top Chokepoint",
            supply_result.chokepoints.iloc[0]["node"],
        ],
    ]
    console.print(
        tabulate(summary_rows[1:], headers=summary_rows[0], tablefmt="github"))
    console.print(f"Report generated at: {report_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
