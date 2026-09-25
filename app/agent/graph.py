"""The analysis workflow: START -> analyst -> evaluate -> (chart) -> respond -> END."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agent.analyst import build_analyst
from app.agent.charts import build_chart
from app.agent.evaluator import evaluate_node, route_after_review
from app.agent.state import AnalysisState
from langgraph.checkpoint.memory import InMemorySaver


LIMIT_NOTICES = ("Model call limits exceeded", "Tool call limit reached")


def analyst_node(state: AnalysisState) -> dict:
    """Run the LangChain agent and record what it did."""
    agent = build_analyst()
    result = agent.invoke({"messages": state["messages"]})

    # Keep only messages this run produced. Messages already in state have ids.
    known_ids = {message.id for message in state["messages"]}
    new_messages = [message for message in result["messages"] if message.id not in known_ids]

    queries = [
        call["args"]["query"]
        for message in new_messages
        for call in getattr(message, "tool_calls", None) or []
        if call["name"] == "run_sql"
    ]

    return {"messages": new_messages, "queries": queries}


def chart_node(state: AnalysisState) -> dict:
    """Draw the chart the evaluator asked for. Deterministic Python, no model call."""
    spec = state["chart_spec"]
    return {"chart": build_chart(spec["sql"], spec["type"], spec["title"])}


def respond_node(state: AnalysisState) -> dict:
    """Assemble the final answer. Deterministic: no model call here."""
    for message in reversed(state["messages"]):
        text = (message.content or "").strip()
        if text and not text.startswith(LIMIT_NOTICES):
            return {"final_answer": text}
    return {"final_answer": "The analysis stopped before producing an answer."}


def build_graph(checkpointer=None):
    """Wire the nodes together and compile the workflow.
    A checkpointer saves the state after every node, so a later question on the
    same thread_id continues the same conversation."""
    builder = StateGraph(AnalysisState)

    builder.add_node("analyst", analyst_node)
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("chart", chart_node)
    builder.add_node("respond", respond_node)

    builder.add_edge(START, "analyst")
    builder.add_edge("analyst", "evaluate")
    builder.add_conditional_edges("evaluate", route_after_review,
                                  {"analyst": "analyst", "chart": "chart", "respond": "respond"})
    builder.add_edge("chart", "respond")
    builder.add_edge("respond", END)

    return builder.compile(checkpointer=checkpointer or InMemorySaver())