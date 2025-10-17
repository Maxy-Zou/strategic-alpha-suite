"""
Markdown report generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from .config import Settings
from .macro_analysis import MacroResult
from .risk_model import RiskResult
from .supply_mapping import SupplyResult
from .valuation import ValuationResult


def _format_percentage(value: float) -> str:
    return f"{value:.2%}"


def _format_number(value: float) -> str:
    if abs(value) >= 1_000_000_000:
        return f"{value/1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value/1_000:.1f}K"
    return f"{value:.2f}"


def _markdown_table(df: pd.DataFrame, columns: Iterable[str]) -> str:
    subset = df.loc[:, columns]
    header = " | ".join(columns)
    separator = " | ".join(["---"] * len(columns))
    rows = [" | ".join(str(value) for value in subset.loc[idx]) for idx in subset.index]
    return "\n".join([f"| {header} |", f"| {separator} |"] + [f"| {row} |" for row in rows])


def render_markdown_report(
    ticker: str,
    settings: Settings,
    macro: MacroResult,
    supply: SupplyResult,
    valuation: ValuationResult,
    risk: RiskResult,
) -> Path:
    """Compose and write a Markdown memo summarizing analysis outputs."""
    ensure = settings.reports_dir
    ensure.mkdir(parents=True, exist_ok=True)
    report_path = ensure / f"{ticker.upper()}_memo.md"

    price = valuation.price_series.iloc[-1]
    intrinsic = valuation.dcf_summary["equity_value_per_share"]
    macro_metrics = macro.metrics
    hist_var = risk.var_results["historical"]
    varcov_var = risk.var_results["variance_covariance"]
    stress = risk.stress_results

    chokepoint_table = supply.chokepoints.copy()
    chokepoint_table["betweenness"] = chokepoint_table["betweenness"].map(
        lambda x: f"{x:.4f}"
    )
    chokepoint_table["degree"] = chokepoint_table["degree"].map(lambda x: f"{x:.1f}")

    comps = valuation.comps.copy()
    comps[["pe", "ev_ebitda", "ps"]] = comps[["pe", "ev_ebitda", "ps"]].round(2)

    markdown = f"""# {ticker.upper()} Strategic Alpha Memo

## Macro Context
- CPI YoY: {_format_percentage(macro_metrics['cpi_yoy'] / 100)}
- Unemployment Rate: {macro_metrics['unemployment_rate']:.2f}%
- Fed Funds Rate: {macro_metrics['fed_funds_rate']:.2f}%
- Industrial Production YoY: {macro_metrics['industrial_production_yoy']:.2f}%

![Macro Indicators](../artifacts/{macro.plot_path.name})

## Supply Chain Structure
Top chokepoints by betweenness:

{_markdown_table(chokepoint_table, ['node', 'country', 'betweenness'])}

![Supply Graph](../artifacts/{supply.graph_path.name})

## Valuation Framework
- Market Price: ${price:.2f}
- DCF Intrinsic Value per Share: ${intrinsic:.2f}
- Enterprise Value: {_format_number(valuation.dcf_summary['enterprise_value'])}
- Equity Value: {_format_number(valuation.dcf_summary['equity_value'])}

DCF sensitivity grid saved at `../artifacts/{valuation.dcf_sensitivity_path.name}`.

Relative comps:

{_markdown_table(comps[['ticker', 'price', 'pe', 'ev_ebitda', 'ps']], ['ticker', 'price', 'pe', 'ev_ebitda', 'ps'])}

Comps table saved at `../artifacts/{valuation.comps_path.name}`.

## Risk Diagnostics
- Historical VaR 95%: {_format_number(hist_var['var_95'])}
- Historical VaR 99%: {_format_number(hist_var['var_99'])}
- Variance-Covariance VaR 95%: {_format_number(varcov_var['var_95'])}
- Variance-Covariance VaR 99%: {_format_number(varcov_var['var_99'])}

Stress test (Taiwan fab outage proxy):
- Shock applied: {stress['shock_pct']:.2%}
- Portfolio loss: {_format_percentage(stress['portfolio_loss'])}

Details stored in `../artifacts/{risk.var_path.name}` and `../artifacts/{risk.stress_path.name}`.

## What Matters
1. Macro momentum moderates; watch inflation trend vs. Fed path.
2. Supply chain chokepoints concentrate in a handful of foundry partners.
3. DCF upside hinges on sustaining high reinvestment efficiency.
4. Tail risk dominated by concentrated fab exposure; monitor geopolitical signals.
"""

    report_path.write_text(markdown, encoding="utf-8")
    return report_path


__all__ = ["render_markdown_report"]
