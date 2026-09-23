"""Reviews the analyst's evidence and decides whether to send it back for more."""

from pydantic import BaseModel, Field

from app.agent.state import AnalysisState
from app.core.llm import get_llm

MAX_ATTEMPTS = 2


class EvidenceReview(BaseModel):
    """What the reviewer must return. No free text parsing."""

    sufficient: bool = Field(description="True if the queries actually support the answer.")
    gaps: str = Field(default="", description="If not sufficient, the ONE query that would fill the gap.")


REVIEW_PROMPT = """You are reviewing a data analyst's work. Judge the evidence, not the writing.

Question: {question}

SQL the analyst ran:
{queries}

The analyst's answer:
{answer}

Rules:
- A "why" or "explain" question needs a breakdown query, not just the headline number.
- If the answer names a cause, a query must show that cause.
- If something rose or fell, volume should be checked as well as value.
- A simple factual question needs only one query. Do not ask for more in that case.

If something important is missing, set sufficient=false and name ONE query that would fill the gap."""


def evaluate_node(state: AnalysisState) -> dict:
    reviewer = get_llm().with_structured_output(EvidenceReview)
    review = reviewer.invoke(REVIEW_PROMPT.format(
        question=state["question"],
        queries="\n".join(state["queries"]) or "(no queries were run)",
        answer=state["messages"][-1].content,
    ))

    attempts = state["attempts"] + 1
    if review.sufficient or attempts >= MAX_ATTEMPTS:
        return {"attempts": attempts, "needs_more": False}

    return {
        "attempts": attempts,
        "needs_more": True,
        "messages": [{"role": "user", "content":
                      f"A reviewer found the analysis incomplete: {review.gaps} "
                      f"Run that query, then give the full answer again."}],
    }


def route_after_review(state: AnalysisState) -> str:
    return "analyst" if state["needs_more"] else "respond"