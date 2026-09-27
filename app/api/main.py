"""HTTP API for the analyst agent. One graph, one endpoint, resumable threads."""

import uuid
from typing import Literal

from fastapi import FastAPI
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.agent.graph import build_graph

app = FastAPI(title="AI Data Analyst Agent", version="1.0")

# Built once when the server starts, not once per request.
graph = build_graph()


class AskRequest(BaseModel):
    message: str = Field(min_length=2,
                         description="A question, or the answer to one the agent asked.")
    thread_id: str | None = Field(default=None,
                                  description="Omit to start a new conversation.")


class AskResponse(BaseModel):
    status: Literal["answer", "needs_input"]
    thread_id: str
    answer: str = ""
    agent_question: str = ""
    queries: list[str] = []
    chart: dict | None = None


def new_run(question: str) -> dict:
    """The starting state for a fresh question. Same payload the CLI sends."""
    return {
        "question": question,
        "messages": [{"role": "user", "content": question}],
        "queries": None,
        "final_answer": "",
        "attempts": 0,
        "needs_more": False,
        "chart_spec": None,
        "chart": None,
    }


@app.get("/health")
def health() -> dict:
    """Is the server up? Docker checks this in Step 14."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """Ask a question, or answer one the agent asked on this thread."""
    thread_id = request.thread_id or uuid.uuid4().hex
    config = {"configurable": {"thread_id": thread_id}}

    # If this thread is paused on ask_user, the message is the answer to it.
    paused = bool(graph.get_state(config).next)
    payload = Command(resume=request.message) if paused else new_run(request.message)

    state = graph.invoke(payload, config)

    pending = state.get("__interrupt__")
    if pending:
        return AskResponse(status="needs_input", thread_id=thread_id,
                           agent_question=pending[0].value)

    return AskResponse(status="answer", thread_id=thread_id,
                       answer=state["final_answer"], queries=state["queries"],
                       chart=state["chart"])