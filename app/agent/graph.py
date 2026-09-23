"""The analysis workflow: START -> analyst -> respond -> END."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agent.analyst import build_analyst
from app.agent.state import AnalysisState
from app.agent.evaluator import evaluate_node, route_after_review

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


def respond_node(state: AnalysisState) -> dict:
    """Assemble the final answer. Deterministic: no model call here."""
    last_message = state["messages"][-1]
    return {"final_answer": (last_message.content or "").strip()}


def build_graph():
    """Wire the nodes together and compile the workflow."""
    builder = StateGraph(AnalysisState)

    builder.add_node("analyst", analyst_node)
    builder.add_node("evaluate", evaluate_node)
    builder.add_node("respond", respond_node)
    

    builder.add_edge(START, "analyst")
    builder.add_edge("analyst", "evaluate")
    builder.add_conditional_edges("evaluate",route_after_review,
                                {"analyst": "analyst", "respond": "respond"})
    builder.add_edge("respond", END)

    return builder.compile()