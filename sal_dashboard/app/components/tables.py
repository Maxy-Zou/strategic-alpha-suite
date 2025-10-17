"""
Tabular formatting helpers for dashboard display.
"""

from __future__ import annotations

import pandas as pd


def format_chokepoints(df: pd.DataFrame) -> pd.DataFrame:
    """Round values for display."""
    table = df.copy()
    if "betweenness" in table.columns:
        table["betweenness"] = table["betweenness"].round(4)
    if "degree" in table.columns:
        table["degree"] = table["degree"].round(2)
    if "in_degree" in table.columns:
        table["in_degree"] = table["in_degree"].round(2)
    if "out_degree" in table.columns:
        table["out_degree"] = table["out_degree"].round(2)
    return table


def format_comps(df: pd.DataFrame) -> pd.DataFrame:
    """Format comparables table values."""
    table = df.copy()
    for column in ["price", "market_cap", "enterprise_value"]:
        if column in table.columns:
            table[column] = table[column].map(
                lambda x: f"{x:,.0f}" if pd.notna(x) else "NA"
            )
    for column in ["pe", "ev_ebitda", "ps"]:
        if column in table.columns:
            table[column] = table[column].map(
                lambda x: f"{x:.2f}" if pd.notna(x) else "NA"
            )
    return table


__all__ = ["format_chokepoints", "format_comps"]
