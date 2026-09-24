"""The three things the analyst agent is allowed to do."""

from langchain.tools import tool
from sqlalchemy import inspect as sqlalchemy_inspect

from app.database.connection import QueryResult, analyst_engine, run_query
from app.database.safety import UnsafeQueryError


@tool
def list_tables() -> str:
    """List the tables in the analytics database. Call this first."""
    return ", ".join(sqlalchemy_inspect(analyst_engine).get_table_names())

def schema_summary() -> str:
    """Every table and column, plus the period the data covers."""
    inspector = sqlalchemy_inspect(analyst_engine)
    lines = []
    for table in inspector.get_table_names():
        columns = ", ".join(c["name"] for c in inspector.get_columns(table))
        lines.append(f"{table}({columns})")

    span = run_query("SELECT MIN(order_date), MAX(order_date) FROM orders").rows[0]
    lines.append(f"Orders run from {span[0]} to {span[1]}. There is no data outside that period.")
    return "\n".join(lines)

@tool
def describe_tables(table_names: str) -> str:
    """Show the columns, types, notes and foreign keys of one or more tables.

    Pass a comma-separated list, for example: orders, order_items
    """
    inspector = sqlalchemy_inspect(analyst_engine)
    existing = set(inspector.get_table_names())
    lines: list[str] = []

    for name in [part.strip() for part in table_names.split(",") if part.strip()]:
        if name not in existing:
            lines.append(f"No table called '{name}'. Available: {', '.join(sorted(existing))}")
            continue

        lines.append(f"TABLE {name}")
        for column in inspector.get_columns(name):
            note = f"   -- {column['comment']}" if column.get("comment") else ""
            lines.append(f"  {column['name']} ({column['type']}){note}")
        for key in inspector.get_foreign_keys(name):
            lines.append(
                f"  FK {', '.join(key['constrained_columns'])} -> "
                f"{key['referred_table']}.{', '.join(key['referred_columns'])}"
            )
        lines.append("")

    return "\n".join(lines)


def format_result(result: QueryResult, max_rows: int = 20) -> str:
    """Turn rows into a small text table the model can read."""
    if not result.rows:
        return "The query ran but returned no rows."

    shown = result.rows[:max_rows]
    lines = [" | ".join(result.columns)]
    lines += [" | ".join("NULL" if v is None else str(v) for v in row) for row in shown]
    lines.append(f"({len(shown)} of {len(result.rows)} rows shown{', more were cut off' if result.truncated else ''})")
    return "\n".join(lines)


@tool
def run_sql(query: str) -> str:
    """Run ONE read-only PostgreSQL SELECT and return the rows.

    Writes are rejected. If the query fails, read the error and try a corrected query.
    """
    try:
        return format_result(run_query(query))
    except UnsafeQueryError as error:
        return f"Query rejected: {error}"
    except Exception as error:
        # The database error text goes back to the agent so it can fix its SQL.
        return f"SQL error: {error.__class__.__name__}: {error}"