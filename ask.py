"""Chat with the analyst:  python ask.py "why did revenue drop in March 2026?"

Follow-up questions in the same session remember what came before.
"""

import sys

from langgraph.types import Command

from app.agent.graph import build_graph

THREAD = {"configurable": {"thread_id": "cli"}}


def ask(graph, question: str) -> None:
    payload = {
        "question": question,
        "messages": [{"role": "user", "content": question}],
        "queries": None,        # None clears last turn's queries
        "final_answer": "",
        "attempts": 0,
        "needs_more": False,
        "chart_spec": None,
        "chart": None,
    }

    while True:
        state = graph.invoke(payload, THREAD)
        pending = state.get("__interrupt__")
        if not pending:
            break
        payload = Command(resume=input(f"\n[the analyst asks] {pending[0].value}\n> ").strip())

    for query in state["queries"]:
        print(f"[sql] {' '.join(query.split())[:150]}")
    print(f"\n{len(state['queries'])} queries, {state['attempts']} analyst pass(es)")

    if state["chart"]:
        import plotly.graph_objects as go
        go.Figure(state["chart"]).write_html("chart.html")
        print("chart saved to chart.html")

    print("\n=== ANSWER ===\n")
    print(state["final_answer"])


def main() -> None:
    graph = build_graph()
    question = " ".join(sys.argv[1:])

    while True:
        if not question:
            question = input("\nQuestion (blank to quit): ").strip()
        if not question:
            break
        ask(graph, question)
        question = ""


if __name__ == "__main__":
    main()