"""Score the agent against questions whose answers were checked against the database.

Run:  python evaluate_agent.py
"""

from uuid import uuid4

from langsmith import Client

from app.agent.graph import build_graph

DATASET_NAME = "analyst-agent-v1"

# Every expected value was verified by querying PostgreSQL directly.
# "|" means any one of these spellings counts as correct.
EXAMPLES = [
    {"inputs": {"question": "What was the total revenue in 2025?"},
     "outputs": {"expected": ["2315167"]}},
    {"inputs": {"question": "How many customers are in the database?"},
     "outputs": {"expected": ["800"]}},
    {"inputs": {"question": "Which product category generated the most revenue in 2025?"},
     "outputs": {"expected": ["electronics"]}},
    {"inputs": {"question": "How many units were sold in total across completed orders?"},
     "outputs": {"expected": ["34342"]}},
    {"inputs": {"question": "What was the total revenue in February 2024?"},
     "outputs": {"expected": ["129929"]}},
    {"inputs": {"question": "Compare total revenue in 2024 with 2025."},
     "outputs": {"expected": ["2045164", "2315167"]}},
    {"inputs": {"question": "What was the revenue in November 2026?"},
     "outputs": {"expected": ["2026-08-31|august 2026|no data"]}},
]

graph = build_graph()


def run_agent(inputs: dict) -> dict:
    """One question in, the agent's answer out. New thread each time, so no memory carry-over."""
    state = graph.invoke(
        {"question": inputs["question"],
         "messages": [{"role": "user", "content": inputs["question"]}],
         "queries": None, "final_answer": "", "attempts": 0,
         "needs_more": False, "chart_spec": None, "chart": None},
        {"configurable": {"thread_id": uuid4().hex}},
    )
    if state.get("__interrupt__"):     # nobody is here to answer a clarifying question
        return {"answer": "", "queries": state["queries"]}
    return {"answer": state["final_answer"], "queries": state["queries"]}


def matches(outputs: dict, reference_outputs: dict) -> bool:
    """Every expected fact must appear in the answer. '|' means any spelling counts."""
    text = outputs["answer"].lower().replace(",", "").replace("$", "")
    return all(any(alt in text for alt in fact.split("|"))
               for fact in reference_outputs["expected"])


def within_query_budget(outputs: dict) -> bool:
    """The prompt allows 5 queries. Did it stay inside its budget?"""
    return len(outputs["queries"]) <= 5


def main() -> None:
    client = Client()

    try:
        client.read_dataset(dataset_name=DATASET_NAME)
    except Exception:          # first run: the dataset doesn't exist yet
        dataset = client.create_dataset(dataset_name=DATASET_NAME)
        client.create_examples(dataset_id=dataset.id, examples=EXAMPLES)
        print(f"Created dataset {DATASET_NAME} with {len(EXAMPLES)} questions.")

    results = client.evaluate(
        run_agent,
        data=DATASET_NAME,
        evaluators=[matches, within_query_budget],
        experiment_prefix="analyst",
        max_concurrency=1,   # one at a time: the free Groq tier is 8,000 tokens per minute
    )
    print(results)


if __name__ == "__main__":
    main()