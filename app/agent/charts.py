"""Build a Plotly chart from a query result. The model never writes chart code."""

from __future__ import annotations

import json

import pandas as pd
import plotly.express as px

from app.database.connection import run_query

CHART_ROW_LIMIT = 100


def build_chart(sql: str, chart_type: str, title: str) -> dict | None:
    """Re-run the chosen query and draw it. Returns None if the data cannot be charted."""
    result = run_query(sql, max_rows=CHART_ROW_LIMIT)
    if not result.rows or len(result.columns) < 2:
        return None

    frame = pd.DataFrame(result.rows, columns=result.columns)

    # Postgres returns NUMERIC as Decimal, which pandas stores as plain objects.
    # Convert every column after the first and keep the first one that becomes numbers.
    label_column = frame.columns[0]
    value_column = None
    for column in frame.columns[1:]:
        numbers = pd.to_numeric(frame[column], errors="coerce")
        if numbers.notna().all():
            frame[column] = numbers
            value_column = column
            break

    if value_column is None:
        return None

    draw = px.line if chart_type == "line" else px.bar
    figure = draw(frame, x=label_column, y=value_column, title=title or "")
    return json.loads(figure.to_json())