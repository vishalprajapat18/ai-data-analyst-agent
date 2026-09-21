"""Reject any SQL that is not a single read-only SELECT."""

import sqlglot
from sqlglot import exp


class UnsafeQueryError(ValueError):
    """The query tried to do something other than read."""


WRITES = (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop,
          exp.Alter, exp.TruncateTable, exp.Grant, exp.Command)


def validate_sql(sql: str) -> str:
    statements = sqlglot.parse(sql, dialect="postgres")

    if len(statements) != 1:
        raise UnsafeQueryError("Send exactly one SELECT statement.")

    statement = statements[0]
    if not isinstance(statement, (exp.Select, exp.Union)):
        raise UnsafeQueryError("Only SELECT queries are allowed.")

    # A write can hide inside a CTE, so check every node in the parsed query.
    if any(isinstance(node, WRITES) for node in statement.walk()):
        raise UnsafeQueryError("Writes are not allowed, including inside a CTE.")

    return sql