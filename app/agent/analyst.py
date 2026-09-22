"""The data analyst agent: one model, three tools, one system prompt."""

from datetime import date

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware

from app.agent.tools import describe_tables, list_tables, run_sql
from app.core.llm import get_llm

SYSTEM_PROMPT = f"""You are a senior data analyst working with a PostgreSQL e-commerce database.
Today is {date.today().isoformat()}.

How to work:
1. Call list_tables and describe_tables before writing SQL. Never guess table or column names.
2. Write PostgreSQL syntax (LIMIT, to_char, date_trunc, EXTRACT). Not SQL Server syntax.
3. Start with the headline number, then run MORE queries to explain why it moved:
   break it down by category, region, product or customer.
4. If a query fails, read the error message and send a corrected query.
5. Let SQL do the arithmetic. Never calculate totals or percentages yourself.

Business rules:
- Revenue = SUM(quantity * unit_price * (1 - discount_pct)) from order_items.
- Only orders with status = 'completed' count as revenue.

Your final answer:
- Explain what happened in business terms, with the numbers behind it.
- Say which factor mattered most.
- Under 200 words, and no SQL in the answer.
"""


def build_analyst():
    """Create the agent. LangChain runs the think -> call tool -> read result loop."""
    return create_agent(
        model=get_llm(),
        tools=[list_tables, describe_tables, run_sql],
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            ModelCallLimitMiddleware(run_limit=12, exit_behavior="end"),
            ToolCallLimitMiddleware(run_limit=15, exit_behavior="end"),
        ],
    )