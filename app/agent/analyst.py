"""The data analyst agent: one model, three tools, one system prompt."""

from datetime import date

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware

from app.agent.tools import describe_tables, list_tables, run_sql, schema_summary
from app.core.llm import get_llm



PROMPT_TEMPLATE = """You are a senior data analyst working with a PostgreSQL e-commerce database.
Today is {today}.

The database:
{schema}

How to work:
1. The schema above is complete. Only call describe_tables if you need column notes or exact types.
2. Write PostgreSQL syntax (LIMIT, to_char, date_trunc, EXTRACT). Not SQL Server syntax.
3. A question asking WHY something changed needs at least two queries: the headline number,
   then a breakdown by category, region, product or customer. Check order COUNT as well as revenue.
4. A simple factual question needs ONE query. Answer it and stop.
5. Never run the same query twice. If a query fails, read the error and fix it; if it fails
   again, write a simpler one.
6. Use at most 5 queries in total, then answer with what you have.
7. Let SQL do the arithmetic. Never calculate totals or percentages yourself.
8. Never report a period outside the data range as zero. Say the data ends there instead.

Business rules:
- Revenue = SUM(quantity * unit_price * (1 - discount_pct)) from order_items.
- Only orders with status = 'completed' count as revenue.

Your final answer:
- Explain what happened in business terms, with the numbers behind it.
- Say which factor mattered most.
- Under 200 words, and no SQL in the answer.
"""
def system_prompt() -> str:
    """Built when the agent is created, not at import, so tests can import this module."""
    return PROMPT_TEMPLATE.format(today=date.today().isoformat(), schema=schema_summary())

def build_analyst():
    """Create the agent. LangChain runs the think -> call tool -> read result loop."""
    return create_agent(
        model=get_llm(),
        tools=[list_tables, describe_tables, run_sql, ],
        system_prompt=system_prompt(),
        middleware=[
            # Model calls must stay above tool calls: every tool call needs one.
            ModelCallLimitMiddleware(run_limit=16, exit_behavior="end"),
            ToolCallLimitMiddleware(run_limit=8, exit_behavior="end"),
        ],
    )