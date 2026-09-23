"""Ask the analyst a question:  python ask.py "why did revenue drop in March 2026?" """

import sys

from app.agent.graph import build_graph


def main() -> None:
    question = " ".join(sys.argv[1:]) or input("Question: ")
    graph = build_graph()

    state = graph.invoke({
        "question": question,
        "messages": [{"role": "user", "content": question}],
        "queries": [],
        "final_answer": "",
    })

    for query in state["queries"]:
        print(f"[sql] {' '.join(query.split())[:150]}")
    print(f"\n{len(state['queries'])} queries ran")

    print("\n=== ANSWER ===\n")
    print(state["final_answer"])


if __name__ == "__main__":
    main()