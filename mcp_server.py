"""An MCP server: exposes the safe database layer to any MCP client."""

from mcp.server import MCPServer

from app.agent.tools import format_result, schema_summary
from app.database.connection import run_query
from app.database.safety import UnsafeQueryError

mcp = MCPServer("analyst-db")


@mcp.tool()
def describe_database() -> str:
    """List every table and column, and the period the order data covers."""
    return schema_summary()


@mcp.tool()
def query_database(sql: str) -> str:
    """Run ONE read-only PostgreSQL SELECT and return the rows as a text table.

    Writes are rejected before the query reaches the database.
    """
    try:
        return format_result(run_query(sql))
    except UnsafeQueryError as error:
        return f"Query rejected: {error}"
    except Exception as error:
        return f"SQL error: {error.__class__.__name__}: {error}"


if __name__ == "__main__":
    mcp.run(transport="stdio")