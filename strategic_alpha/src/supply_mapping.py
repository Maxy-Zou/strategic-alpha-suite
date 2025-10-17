"""
Supply chain network analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from .config import Settings
from .utils import load_csv, save_plot


@dataclass
class SupplyResult:
    """Container for supply chain outputs."""

    graph: nx.DiGraph
    metrics: pd.DataFrame
    chokepoints: pd.DataFrame
    graph_path: Path
    metrics_path: Path


def build_graph_from_csv(csv_path: Path) -> nx.DiGraph:
    """Build a directed graph from a CSV file."""
    df = load_csv(csv_path)
    graph = nx.DiGraph()

    for _, row in df.iterrows():
        supplier = row["supplier"]
        customer = row["customer"]
        relationship = row.get("relationship", "")
        country = row.get("country", "Unknown")
        weight = float(row.get("weight", 1.0))

        graph.add_node(
            supplier,
            country=country,
            role="supplier",
        )
        customer_country = (
            graph.nodes[customer].get("country", "Unknown") if customer in graph else "Unknown"
        )
        graph.add_node(
            customer,
            country=customer_country,
            role="customer",
        )
        graph.add_edge(
            supplier,
            customer,
            relationship=relationship,
            weight=weight,
            country=country,
        )
    return graph


def compute_centrality(graph: nx.DiGraph) -> pd.DataFrame:
    """Compute centrality metrics for the graph."""
    betweenness = nx.betweenness_centrality(graph, weight="weight", normalized=True)
    in_degrees = dict(graph.in_degree(weight="weight"))
    out_degrees = dict(graph.out_degree(weight="weight"))

    rows = []
    for node in graph.nodes:
        attrs = graph.nodes[node]
        rows.append(
            {
                "node": node,
                "country": attrs.get("country", "Unknown"),
                "role": attrs.get("role", "unknown"),
                "degree": graph.degree(node, weight="weight"),
                "in_degree": in_degrees.get(node, 0.0),
                "out_degree": out_degrees.get(node, 0.0),
                "betweenness": betweenness.get(node, 0.0),
            }
        )
    df = pd.DataFrame(rows).sort_values(by="betweenness", ascending=False)
    return df


def plot_supply_graph(graph: nx.DiGraph, path: Path) -> Path:
    """Create a spring layout diagram of the supply graph."""
    np.random.seed(42)
    pos = nx.spring_layout(graph, seed=42, weight="weight")
    fig, ax = plt.subplots(figsize=(10, 7))
    nx.draw_networkx(
        graph,
        pos=pos,
        with_labels=True,
        node_size=500,
        font_size=8,
        ax=ax,
    )
    ax.set_title("Strategic Supply Chain Network")
    ax.axis("off")
    return save_plot(fig, path)


def analyze_supply_chain(settings: Settings) -> SupplyResult:
    """Run supply chain analysis and persist artifacts."""
    csv_path = settings.data_dir / "supply_chain" / "sample_edges.csv"
    graph = build_graph_from_csv(csv_path)
    metrics = compute_centrality(graph)
    chokepoints = metrics.head(5).reset_index(drop=True)

    graph_path = settings.artifacts_dir / "supply_graph.png"
    metrics_path = settings.artifacts_dir / "supply_metrics.csv"

    plot_supply_graph(graph, graph_path)
    metrics.to_csv(metrics_path, index=False)

    return SupplyResult(
        graph=graph,
        metrics=metrics,
        chokepoints=chokepoints,
        graph_path=graph_path,
        metrics_path=metrics_path,
    )


def ingest_external_supply_data(source: str) -> pd.DataFrame:
    """
    Placeholder for future integrations with third-party supply chain datasets.

    Args:
        source: Data provider identifier (e.g., ImportYeti, Panjiva, EDGAR).
    """
    raise NotImplementedError(
        f"External supply data ingestion for {source} is not yet implemented."
    )


__all__ = [
    "SupplyResult",
    "analyze_supply_chain",
    "build_graph_from_csv",
    "compute_centrality",
    "ingest_external_supply_data",
]
