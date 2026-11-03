"""The eval runner's text matcher (negation-aware forbidden phrases)."""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
spec = importlib.util.spec_from_file_location("run_eval", os.path.join(HERE, "..", "..", "eval", "run_eval.py"))
run_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_eval)
f = run_eval.contains_unnegated


def test_negated_statements_do_not_count_as_claims():
    assert not f("no refund or replacement has been approved at this time.", "replacement has been approved")
    assert not f("i have not approved your refund", "approved your refund")


def test_real_claims_are_still_caught():
    assert f("good news: your replacement has been approved.", "replacement has been approved")
    assert f("i've approved the refund", "i've approved")


def test_a_negation_in_another_clause_cannot_hide_a_claim():
    assert f("i cannot refund the item, but your replacement has been approved", "replacement has been approved")
    assert f("nothing is wrong. your replacement has been approved", "replacement has been approved")
