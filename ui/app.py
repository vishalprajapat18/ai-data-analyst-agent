"""Chat frontend for the analyst agent. A thin client: it only talks to the API's /ask."""

import os

import httpx
import plotly.graph_objects as go
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
REPO_URL = "https://github.com/vishalprajapat18/ai-data-analyst-agent"
EXAMPLES = [
    "Which product category had the highest revenue in 2025?",
    "Show monthly revenue in 2026",
    "What was revenue in March?",
]

st.set_page_config(page_title="AI Data Analyst Agent", page_icon="📊")
st.title("AI Data Analyst Agent")
st.caption("Ask about an online store's sales, Jan 2024 – Aug 2026. All amounts are in "
           "US dollars. The agent writes read-only SQL, a reviewer checks the evidence, "
           "then it answers.")

if "messages" not in st.session_state:
    st.session_state.messages = []      # the chat so far, redrawn on every rerun
    st.session_state.thread_id = None   # given by the API; keeps one conversation together

with st.sidebar:
    if st.button("New conversation"):
        st.session_state.messages = []
        st.session_state.thread_id = None
        st.rerun()
    st.markdown("**How it works**\n"
                "1. An agent writes and runs read-only SQL.\n"
                "2. A reviewer node checks the answer against the results.\n"
                "3. Charts are drawn by plain Python, not by the model.")
    st.markdown(f"[Code on GitHub]({REPO_URL})")


def show(message: dict, index: int) -> None:
    """Draw one chat message: the text, then the SQL behind it, then the chart."""
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("queries"):
            with st.expander(f"SQL the agent ran ({len(message['queries'])})"):
                for query in message["queries"]:
                    st.code(query, language="sql")
        if message.get("chart"):
            st.plotly_chart(go.Figure(message["chart"]), key=f"chart-{index}")


def ask(text: str) -> dict:
    """Send one message to the API. The same thread_id continues the same conversation."""
    response = httpx.post(f"{API_URL}/ask", timeout=300,
                          json={"message": text, "thread_id": st.session_state.thread_id})
    response.raise_for_status()
    return response.json()


for index, message in enumerate(st.session_state.messages):
    show(message, index)

question = st.chat_input("Ask about revenue, products, customers or regions")

if not st.session_state.messages:
    st.write("Try one:")
    for column, example in zip(st.columns(len(EXAMPLES)), EXAMPLES):
        if column.button(example):
            question = example

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    show(st.session_state.messages[-1], len(st.session_state.messages) - 1)

    with st.spinner("Writing and checking SQL — usually 20–60 seconds..."):
        try:
            data = ask(question)
        except httpx.HTTPError:
            data = None

    if data is None:
        reply = {"role": "assistant",
                 "content": "The agent didn't answer this time. Please try again in a minute."}
    elif data["status"] == "needs_input":
        reply = {"role": "assistant", "content": f"**Quick question:** {data['agent_question']}"}
    else:
        reply = {"role": "assistant", "content": data["answer"],
                 "queries": data["queries"], "chart": data["chart"]}

    if data is not None:
        st.session_state.thread_id = data["thread_id"]
    st.session_state.messages.append(reply)
    st.rerun()