"""
Reusable KPI card rendering helpers.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence

import streamlit as st


def render_kpi_cards(
    labels: Sequence[str],
    values: Sequence[str],
    deltas: Optional[Sequence[Optional[str]]] = None,
) -> None:
    """Render KPI cards in a single row."""
    deltas = deltas or [None] * len(labels)
    columns = st.columns(len(labels))
    for column, label, value, delta in zip(columns, labels, values, deltas):
        column.metric(label=label, value=value, delta=delta)


__all__ = ["render_kpi_cards"]
