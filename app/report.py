"""
Shapes a raw Oracle result (columns/rows) into a report the frontend can render.
Deterministic, no LLM call — the numbers must match what Oracle returned exactly.
"""


def shape_result(result: dict) -> dict:
    columns = result["columns"]
    rows = result["rows"]

    numeric_cols = _numeric_column_indexes(columns, rows)
    view = "table"
    if len(rows) == 1 and len(columns) <= 2:
        view = "summary"
    elif len(rows) > 1 and len(numeric_cols) >= 1 and len(columns) - len(numeric_cols) == 1:
        view = "chart"

    return {
        "view": view,
        "columns": columns,
        "rows": rows,
        "row_count": result["row_count"],
    }


def _numeric_column_indexes(columns: list[str], rows: list[list]) -> list[int]:
    if not rows:
        return []
    sample = rows[0]
    return [i for i, value in enumerate(sample) if isinstance(value, (int, float))]
