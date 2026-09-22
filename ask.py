"""Ask the analyst a question:  python ask.py "why did revenue drop in March 2026?" """

import sys

from app.agent.analyst import build_analyst


def main() -> None:
    question = " ".join(sys.argv[1:]) or input("Question: ")
    agent = build_analyst()

    result = agent.invoke({"messages": [{"role": "user", "content": question}]})

    for message in result["messages"]:
        for call in getattr(message, "tool_calls", None) or []:
            print(f"[tool] {call['name']}: {str(call['args'])[:150]}")

    print("\n=== ANSWER ===\n")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()