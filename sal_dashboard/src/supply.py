"""
Supply chain adapters built on top of the strategic_alpha backend.
"""

from __future__ import annotations

from typing import Any, Optional

import networkx as nx
import pandas as pd
import plotly.graph_objects as go

from .config import get_backend_module, get_settings

supply_module = get_backend_module("supply_mapping")


def load_supply_analysis(settings: Optional[Any] = None) -> Any:
    """Run supply chain analysis via backend module."""
    settings = settings or get_settings()
    return supply_module.analyze_supply_chain(settings)


def supply_metrics(result: Any) -> pd.DataFrame:
    """Return full metrics DataFrame."""
    return result.metrics.copy()


def chokepoints_table(result: Any, top_n: int = 5) -> pd.DataFrame:
    """Return top chokepoints by betweenness centrality."""
    return result.chokepoints.head(top_n).copy()


def supply_graph_figure(result: Any) -> go.Figure:
    """Create a Plotly representation of the supply network."""
    graph: nx.DiGraph = result.graph
    if graph.number_of_nodes() == 0:
        return go.Figure()

    pos = nx.spring_layout(graph, seed=42, weight="weight")

    edge_x, edge_y = [], []
    for source, target in graph.edges():
        x0, y0 = pos[source]
        x1, y1 = pos[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5),
        hoverinfo="none",
        mode="lines",
    )

    node_x, node_y, text = [], [], []
    for node, data in graph.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        text.append(f"{node} ({data.get('country', 'Unknown')})")

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        text=text,
        hoverinfo="text",
        mode="markers+text",
        textposition="top center",
        marker=dict(size=12),
    )

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=10),
        title="Supply Chain Network",
    )
    return fig


def metrics_csv_bytes(metrics_df: pd.DataFrame) -> bytes:
    """Convert metrics DataFrame to CSV bytes for download."""
    return metrics_df.to_csv(index=False).encode("utf-8")


__all__ = [
    "load_supply_analysis",
    "supply_metrics",
    "chokepoints_table",
    "supply_graph_figure",
    "metrics_csv_bytes",
]
