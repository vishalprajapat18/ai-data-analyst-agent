"""route_after_review is the graph's traffic light. It is a plain function, so test it directly."""

from app.agent.evaluator import route_after_review


def test_incomplete_evidence_goes_back_to_the_analyst():
    assert route_after_review({"needs_more": True, "chart_spec": None}) == "analyst"


def test_a_chart_spec_sends_the_run_through_the_chart_node():
    assert route_after_review({"needs_more": False,
                               "chart_spec": {"sql": "SELECT 1", "type": "bar", "title": "x"}}) == "chart"


def test_no_chart_goes_straight_to_the_answer():
    assert route_after_review({"needs_more": False, "chart_spec": None}) == "respond"