"""merge_queries is the reducer that keeps one turn's queries separate from the next."""

from app.agent.state import merge_queries


def test_new_queries_are_added_to_the_existing_ones():
    assert merge_queries(["a"], ["b"]) == ["a", "b"]


def test_none_clears_the_list_for_a_new_turn():
    assert merge_queries(["a", "b"], None) == []


def test_an_empty_update_changes_nothing():
    assert merge_queries(["a"], []) == ["a"]