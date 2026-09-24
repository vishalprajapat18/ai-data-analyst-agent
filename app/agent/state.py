"""The shared state that every node in the graph reads and writes."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


class AnalysisState(TypedDict):
    """One analysis run.

    Plain keys are replaced when a node returns them.
    Annotated keys are merged by the function next to them (a "reducer").
    """

    question: str
    messages: Annotated[list[AnyMessage], add_messages]   # merged by id
    queries: Annotated[list[str], operator.add]    
    #queries is a list of SQL strings, and every new list 
    # of queries should be appended to the existing list. 
    # reducers** operator.add is a reducer      # lists are joined
    final_answer: str                                     # replaced

    attempts: int                                         # how many times the analyst ran
    needs_more: bool   
    chart_spec: dict | None                               # which query to chart, and how
    chart: dict | None                                    # the finished Plotly figure                                   # evaluator's routing decision 