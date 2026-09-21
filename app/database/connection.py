"""Run validated queries as the read-only role and return rows with column names."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import create_engine

from app.core.config import ANALYST_DATABASE_URL, MAX_RESULT_ROWS
from app.database.safety import validate_sql

analyst_engine = create_engine(ANALYST_DATABASE_URL, pool_pre_ping=True)


@dataclass
class QueryResult:
    sql: str
    columns: list[str]
    rows: list[tuple[Any, ...]]
    truncated: bool


def run_query(sql: str, max_rows: int = MAX_RESULT_ROWS) -> QueryResult:
    validate_sql(sql)
    with analyst_engine.connect() as connection:
        # The raw driver cursor is used because SQLAlchemy's text() reads ':'
        # inside JSON as a parameter and exec_driver_sql reads '%' in LIKE as
        # a placeholder. Both break valid generated SQL.
        with connection.connection.cursor() as cursor:
            cursor.execute(sql)
            columns = [column.name for column in cursor.description or []]
            fetched = cursor.fetchmany(max_rows + 1)  # one extra tells us if it was cut off
    return QueryResult(sql, columns, [tuple(r) for r in fetched[:max_rows]], len(fetched) > max_rows)