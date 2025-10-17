"""
Chart factories for Streamlit visuals.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def price_chart(prices: pd.Series) -> go.Figure:
    """Create a price history line chart."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=prices.index, y=prices.values, mode="lines", name="Price"))
    fig.update_layout(
        title="Price History",
        xaxis_title="Date",
        yaxis_title="Price",
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )
    return fig


def macro_chart(data: pd.DataFrame) -> go.Figure:
    """Create macro indicator chart."""
    fig = go.Figure()
    for column in data.columns:
        fig.add_trace(
            go.Scatter(x=data.index, y=data[column], mode="lines", name=column)
        )
    fig.update_layout(
        title="Macro Indicators",
        xaxis_title="Date",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def dcf_heatmap(sensitivity: pd.DataFrame) -> go.Figure:
    """Render a simple heatmap for DCF sensitivity."""
    fig = go.Figure(
        data=go.Heatmap(
            z=sensitivity.values,
            x=list(sensitivity.columns),
            y=list(sensitivity.index),
            colorbar=dict(title="Value/Share"),
        )
    )
    fig.update_layout(
        title="DCF Sensitivity",
        xaxis_title="Terminal Growth",
        yaxis_title="WACC",
        margin=dict(l=60, r=40, t=40, b=40),
    )
    return fig


def risk_histogram(returns: pd.Series) -> go.Figure:
    """Histogram of daily returns."""
    fig = go.Figure(
        data=go.Histogram(x=returns.values, nbinsx=40)
    )
    fig.update_layout(
        title="Portfolio Daily Returns Distribution",
        xaxis_title="Daily Return",
        yaxis_title="Frequency",
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


__all__ = ["price_chart", "macro_chart", "dcf_heatmap", "risk_histogram"]
