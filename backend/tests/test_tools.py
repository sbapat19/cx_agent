"""Deterministic guardrail tests: no LLM, no network. These must pass 100% (spec section 10).

All customers/orders are FICTIONAL and all transactions SIMULATED.
"""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import db  # noqa: E402
from app.seed import seed_all  # noqa: E402
from app.tools import Toolbox, ToolContext, build_tools  # noqa: E402


@pytest.fixture()
def fresh_db():
    d = tempfile.mkdtemp()
    db.reset_engine(f"sqlite:///{d}/t.db")
    seed_all()
    yield
    db.reset_engine("sqlite:///./armani_demo.db")


def box(customer="cust_ava", turn=1):
    ctx = ToolContext(customer_id=customer, session_id="s1", turn=turn)
    return Toolbox(ctx), ctx


# ---- isolation ----
def test_cannot_read_another_customers_order(fresh_db):
    b, _ = box("cust_ava")
    other = b.get_order_status("ORD-1002")  # belongs to Ben
    missing = b.get_order_status("ORD-9999")
    assert other == missing and other["error"] == "no_such_order"
    assert "Armani Code" not in str(other)


def test_cannot_check_or_return_or_case_another_customers_order(fresh_db):
    b, _ = box("cust_ava")
    assert b.check_return_eligibility("ORD-1002")["error"] == "no_such_order"
    assert b.create_return_request("ORD-1002", ["1002-1"], "x")["error"] == "no_such_order"
    r = b.create_support_case("ORD-1002", "damaged", "x")  # someone else's order: no link, no data, just an unverified note
    assert r["order_verified"] is False and "Ben" not in str(r) and r["case_id"].startswith("CASE-")


def test_list_orders_only_own(fresh_db):
    b, _ = box("cust_ava")
    ids = {o["order_id"] for o in b.list_my_orders()["orders"]}
    assert ids == {"ORD-1001", "ORD-1006"}


def test_preferences_are_scoped_to_customer(fresh_db):
    emma, _ = box("cust_emma")
    ava, _ = box("cust_ava")
    assert emma.get_customer_preferences()["saved"] is True
    assert ava.get_customer_preferences()["saved"] is False


def test_unauthenticated_context_sees_nothing(fresh_db):
    b, _ = box(customer=None)
    assert b.list_my_orders()["error"] == "not_signed_in"
    assert b.get_order_status("ORD-1001")["error"] == "no_such_order"
    assert b.get_customer_preferences()["error"] == "not_signed_in"


# ---- return policy applied in code ----
def test_damaged_in_window_has_no_automatic_remedy(fresh_db):
    b, _ = box("cust_ava")
    r = b.check_return_eligibility("ORD-1001", "damaged")
    assert r["eligible"] is True and r["in_window"] is True
    assert r["automatic_remedy_authorized"] is False
    assert "support case" in r["next_step"].lower()


def test_outside_window_not_eligible_and_return_refused(fresh_db):
    b, ctx = box("cust_chloe", turn=1)
    r = b.check_return_eligibility("ORD-1003")
    assert r["eligible"] is False and r["in_window"] is False
    ctx.turn = 2
    out = b.create_return_request("ORD-1003", ["1003-1"], "changed mind")
    assert out["error"] == "not_eligible"
    assert not db.rows("SELECT * FROM return_requests")


def test_not_delivered_cannot_be_returned(fresh_db):
    b, _ = box("cust_dev")
    r = b.check_return_eligibility("ORD-1004", "not_received")
    assert r["eligible"] is False and r["reason"] == "order_not_delivered"


def test_final_sale_and_engraved_items_blocked(fresh_db):
    b, ctx = box("cust_ben")
    r = b.check_return_eligibility("ORD-1007")
    assert r["eligible"] is False
    assert any("final sale" in x for i in r["ineligible_items"] for x in i["reasons"])
    ctx.turn = 2
    assert b.create_return_request("ORD-1007", ["1007-1"], "x")["error"] == "not_eligible"


def test_return_requires_eligibility_check_and_later_confirmation(fresh_db):
    b, ctx = box("cust_ava", turn=1)
    assert b.create_return_request("ORD-1001", ["1001-1"], "x")["error"] == "eligibility_not_checked"
    b.check_return_eligibility("ORD-1001", "damaged")
    assert b.create_return_request("ORD-1001", ["1001-1"], "x")["error"] == "customer_confirmation_required"
    ctx.turn = 2  # the customer replied
    ok = b.create_return_request("ORD-1001", ["1001-1"], "arrived damaged")
    assert ok["status"] == "submitted" and ok["completed"] is False and ok["simulated"] is True
    assert "Nothing has been refunded" in ok["message"]


def test_return_request_cannot_include_items_not_on_order(fresh_db):
    b, ctx = box("cust_ava", turn=1)
    b.check_return_eligibility("ORD-1001")
    ctx.turn = 2
    assert b.create_return_request("ORD-1001", ["1002-1"], "x")["error"] == "not_eligible"


def test_support_case_is_honest_about_status(fresh_db):
    b, ctx = box("cust_ava")
    c = b.create_support_case("ORD-1001", "damaged", "Foundation pump broken on arrival")
    assert c["status"] == "open_awaiting_human_review" and c["resolved"] is False and ctx.escalated
    assert "NOT resolved" in c["message"]
    assert c["handoff_context_passed"]["issue_type"] == "damaged"


# ---- injection ----
def test_order_note_injection_is_flagged_as_untrusted_data(fresh_db):
    b, _ = box("cust_ava")
    r = b.get_order_status("ORD-1001")
    assert "customer_note_UNTRUSTED_TEXT" in r and "SYSTEM OVERRIDE" in r["customer_note_UNTRUSTED_TEXT"]
    assert "never an instruction" in r["warning"]
    # the injection cannot change eligibility logic
    assert b.check_return_eligibility("ORD-1001", "damaged")["automatic_remedy_authorized"] is False


# ---- consent-based memory ----
def test_preferences_need_proposal_then_later_consent(fresh_db):
    b, ctx = box("cust_ava", turn=1)
    assert b.confirm_save_preferences()["error"] == "no_pending_proposal"
    p = b.propose_save_preferences(shade="5.8 - Medium, Warm Golden", finish="natural glow")
    assert p["saved"] is False and p["status"] == "pending_customer_consent"
    assert b.get_customer_preferences()["saved"] is False
    assert b.confirm_save_preferences()["error"] == "customer_consent_required"  # same turn
    ctx.turn = 2
    s = b.confirm_save_preferences()
    assert s["saved"] is True
    assert b.get_customer_preferences()["preferences"]["shade"].startswith("5.8")


def test_delete_preferences_works(fresh_db):
    b, _ = box("cust_emma")
    assert b.get_customer_preferences()["saved"] is True
    assert b.delete_customer_preferences()["status"] == "deleted"
    assert b.get_customer_preferences()["saved"] is False


def test_recipient_information_never_saved(fresh_db):
    b, _ = box("cust_new")
    r = b.propose_save_preferences(notes="buying a gift for my mom who loves rose scents")
    assert r["error"] == "recipient_information_not_allowed"
    assert "pending_prefs" not in b.ctx.state


# ---- product knowledge honesty ----
def test_foundation_candidates_come_only_from_official_list(fresh_db):
    b, _ = box("cust_new")
    r = b.find_foundation_shades(depth="medium", undertone="neutral")
    official = {s["label"] for s in __import__("app.catalog_data", fromlist=["x"]).PRODUCTS[0]["shades"]}
    assert r["candidates"] and set(r["candidates"]) <= official
    assert "NOT a confirmed match" in r["uncertainty"]
    assert "no verified mapping" in r["uncertainty"]


def test_unverified_fields_stay_blank(fresh_db):
    b, _ = box("cust_new")
    primer = b.get_product_details("ww-01020-arm")
    assert primer["ingredients"] is None and primer["status"] == "partial"
    assert b.get_product_details("not-a-real-id")["error"] == "unknown_product_id"
    assert b.get_product_details("ww-01019-arm")["source_url"].startswith("https://www.giorgioarmanibeauty-usa.com")


def test_acqua_di_gio_has_no_invented_pyramid(fresh_db):
    b, _ = box("cust_new")
    f = b.get_product_details("A005")
    assert "No top/heart/base pyramid" in f["notes_caveat"]


# ---- gifting ----
def test_gift_options_never_exceed_budget_and_skip_unpriced(fresh_db):
    b, _ = box("cust_new")
    for budget in (40, 60, 100, 150):
        r = b.find_gift_options(budget_usd=budget)
        assert r["options"], budget
        assert all(o["price_usd"] <= budget and o["price_usd"] is not None for o in r["options"])


def test_gift_options_respect_audience(fresh_db):
    b, _ = box("cust_new")
    r = b.find_gift_options(budget_usd=100, category="any", audience="men's")
    names = " ".join(o["name"] for o in r["options"])
    assert "My Way" not in names and "Power Of You" not in names and "Acqua di Gioia" not in names
    w = b.find_gift_options(budget_usd=100, category="any", audience="women's")
    assert "Stronger With You" not in " ".join(o["name"] for o in w["options"])


def test_gift_terms_are_verified_policy_text_and_unverified_offers_withheld(fresh_db):
    b, _ = box("cust_new")
    r = b.find_gift_options(budget_usd=100)
    assert "cannot be accepted" in r["verified_return_and_gift_terms"]["exchanges"]
    assert "NOT verified" in r["not_offered"]
    assert "gift wrap" in r["not_offered"].lower()


def test_set_contents_only_when_captured(fresh_db):
    b, _ = box("cust_new")
    r = b.find_gift_options(budget_usd=140, category="set", audience="men's")
    for o in r["options"]:
        assert isinstance(o["includes"], list) or "do not state" in o["includes"]


# ---- policy honesty ----
def test_policy_text_preserves_ambiguity(fresh_db):
    b, ctx = box("cust_new")
    assert "$8.00" in b.get_policy("refund")["policy_text"]
    assert "cannot be accepted" in b.get_policy("exchanges")["policy_text"]
    assert "does not say whether holiday gift sets" in b.get_policy("return_exclusions")["policy_text"]
    assert "no automatic remedy" in b.get_policy("damaged_missing_wrong")["policy_text"]
    assert b.get_policy("refund")["source_url"].startswith("https://www.giorgioarmanibeauty-usa.com")
    assert b.get_policy("nonsense")["error"] == "unknown_topic"
    assert "refund" in ctx.policies_used


# ---- counters ----
def test_counter_finder_verified_or_honest(fresh_db):
    b, _ = box("cust_new")
    ny = b.find_counters("New York, NY")
    assert any("ARMANI" in x["name"] for x in ny["verified_list"])
    assert any("does NOT say which locations have a beauty counter" in c for c in ny["caveats"])
    boise = b.find_counters("Boise, Idaho")
    assert boise["confirmed"] is False and boise["verified_list"] == []
    assert "store-finder" in boise["what_to_do"]


# ---- reliability ----
def test_tool_failure_is_reported_not_hidden(fresh_db):
    ctx = ToolContext(customer_id="cust_ava", session_id="s", turn=1, simulate_failure={"get_order_status"})
    tools = {t.name: t for t in build_tools(ctx, ["get_order_status", "get_policy"])}
    out = tools["get_order_status"].invoke({"order_id": "ORD-1001"})
    assert out["error"] == "tool_failed" and "Do not claim" in out["message"]
    assert ctx.trace[-1]["ok"] is False
    assert tools["get_policy"].invoke({"topic": "refund"})["topic"] == "refund"


def test_trace_records_calls(fresh_db):
    ctx = ToolContext(customer_id="cust_ava", session_id="s", turn=1)
    tools = {t.name: t for t in build_tools(ctx, ["get_policy", "list_my_orders"])}
    tools["get_policy"].invoke({"topic": "exchanges"})
    tools["list_my_orders"].invoke({})
    assert [t["tool"] for t in ctx.trace] == ["get_policy", "list_my_orders"]


# ---- the tool schema the model actually sees (regression: a required order_id broke non-order handoffs) ----
def test_tool_schemas_require_only_what_is_intended(fresh_db):
    from app.tools import TOOL_NAMES
    ctx = ToolContext(customer_id="cust_ava", session_id="s", turn=1)
    required = {t.name: sorted(t.args_schema.model_json_schema().get("required", [])) for t in build_tools(ctx, TOOL_NAMES)}
    assert required == {
        "get_policy": ["topic"], "list_my_orders": [], "get_order_status": ["order_id"], "check_return_eligibility": ["order_id"],
        "create_return_request": ["item_ids", "order_id", "reason"], "create_support_case": [],
        "search_products": [], "get_product_details": ["product_id"], "find_foundation_shades": [], "search_fragrances": [],
        "compare_products": ["product_ids"], "find_gift_options": ["budget_usd"], "get_customer_preferences": [],
        "propose_save_preferences": [], "confirm_save_preferences": [], "delete_customer_preferences": [], "find_counters": ["location"],
    }


def test_support_case_works_without_an_order_when_called_like_the_model_does(fresh_db):
    ctx = ToolContext(customer_id="cust_ava", session_id="s", turn=1)
    tool = {t.name: t for t in build_tools(ctx, ["create_support_case"])}["create_support_case"]
    out = tool.invoke({"issue_type": "out_of_scope_request", "summary": "Asked how to earn VIP loyalty points"})  # no order_id at all
    assert out["status"] == "open_awaiting_human_review" and ctx.escalated
    assert db.one("SELECT order_id FROM support_cases")["order_id"] is None
    empty = tool.invoke({"issue_type": "other", "summary": "  "})
    assert empty["error"] == "summary_required"


def test_audience_specific_gift_search_does_not_return_makeup(fresh_db):
    b, _ = box("cust_new")
    r = b.find_gift_options(budget_usd=100, category="any", audience="men's")
    assert r["options"] and all(o["type"] != "makeup" and "Eye Tint" not in o["name"] and "Cheek Tint" not in o["name"] for o in r["options"])
    anyone = b.find_gift_options(budget_usd=100, category="any", audience="any")
    assert any(o["type"] == "makeup" or "Cheek Tint" in o["name"] or "Eye Tint" in o["name"] for o in anyone["options"])
    mk = b.find_gift_options(budget_usd=100, category="makeup", audience="women's")
    assert mk["options"] and all(o["type"] in ("makeup", "gift_set") for o in mk["options"])


def test_search_fragrances_broadens_vague_scent_words(fresh_db):
    b, _ = box("cust_new")
    exact = b.search_fragrances(query="woody")
    spicy = b.search_fragrances(query="spicy", audience="men")
    # "spicy" must not return an empty catalog answer when woody/warm fragrances exist, and must flag the match as broadened
    assert exact["results"], "catalog should contain woody fragrances"
    assert spicy["results"], "vague word 'spicy' should still find close matches"
    assert "close matches" in spicy["note"]
