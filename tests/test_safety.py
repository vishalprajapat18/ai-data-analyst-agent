import pytest
from sqlalchemy.exc import DatabaseError

from app.database.connection import analyst_engine, run_query
from app.database.safety import UnsafeQueryError, validate_sql


@pytest.mark.parametrize("sql", [
    "DELETE FROM orders",
    "DROP TABLE orders",
    "SELECT 1; DROP TABLE orders",
    "WITH x AS (DELETE FROM orders RETURNING *) SELECT * FROM x",
])
def test_validator_blocks_writes(sql):
    with pytest.raises(UnsafeQueryError):
        validate_sql(sql)


def test_database_blocks_writes_even_if_the_validator_is_bypassed():
    with pytest.raises(DatabaseError) as error:
        with analyst_engine.connect() as connection:
            connection.exec_driver_sql("DELETE FROM orders")
    assert "read-only" in str(error.value).lower()


def test_a_real_query_works():
    result = run_query("SELECT COUNT(*) AS n FROM orders WHERE status = 'completed'")
    assert result.columns == ["n"]
    assert result.rows[0][0] > 0