"""Reviews the analyst's evidence and decides whether to send it back for more."""

from pydantic import BaseModel, Field

from app.agent.state import AnalysisState
from app.core.llm import get_llm
from typing import Literal

MAX_ATTEMPTS = 2


class EvidenceReview(BaseModel):
    """What the reviewer must return. No free text parsing."""

    sufficient: bool = Field(description="True if the queries actually support the answer.")
    gaps: str = Field(default="", description="If not sufficient, the ONE query that would fill the gap.")
    chart_query: int = Field(default=-1, description="Number of the query worth charting, or -1 for no chart.")
    chart_type: Literal["bar", "line"] = Field(default="bar", description="line for dates in order, bar for categories.")
    chart_title: str = Field(default="", description="Short chart title.")

REVIEW_PROMPT = """You are reviewing a data analyst's work. Judge the evidence, not the writing.

Question: {question}

SQL the analyst ran (numbered):
{queries}

The analyst's answer:
{answer}

Rules:
- A "why" or "explain" question needs a breakdown query, not just the headline number.
- If the answer names a cause, a query must show that cause.
- If something rose or fell, volume should be checked as well as value.
- A simple factual question needs only one query. Do not ask for more in that case.

If something important is missing, set sufficient=false and name ONE query that would fill the gap.

Then choose a chart. Most analyses deserve one:
- If any query returned a label column plus a number column with 2 to 30 rows, chart it.
  Set chart_query to that query's number.
- line when the labels are months or dates in order, bar for comparing categories.
- Use chart_query = -1 only when every result is a single number."""

def evaluate_node(state: AnalysisState) -> dict:
    reviewer = get_llm().with_structured_output(EvidenceReview)
    review = reviewer.invoke(REVIEW_PROMPT.format(
        question=state["question"],
        queries="\n".join(f"{i}: {' '.join(q.split())}"
                          for i, q in enumerate(state["queries"])) or "(no queries were run)",
        answer=state["messages"][-1].content,
    ))

    attempts = state["attempts"] + 1
    if review.sufficient or attempts >= MAX_ATTEMPTS:
         chart_spec = None
         if 0 <= review.chart_query < len(state["queries"]):
            chart_spec = {"sql": state["queries"][review.chart_query],
                          "type": review.chart_type,
                          "title": review.chart_title}
         return {"attempts": attempts, "needs_more": False,"chart_spec": chart_spec}

    return {
        "attempts": attempts,
        "needs_more": True,
        "messages": [{"role": "user", "content":
                      f"A reviewer found the analysis incomplete: {review.gaps} "
                      f"Run that query, then give the full answer again."}],
    }

def route_after_review(state: AnalysisState) -> str:
    if state["needs_more"]:
        return "analyst"
    return "chart" if state["chart_spec"] else "respond"