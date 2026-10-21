from shelfhelp.decide import decide
from shelfhelp.message import build_message
from shelfhelp.validate import fallback_response, problems

from test_solver import make_intent


def rec(items, total, status="recommendation"):
    return {"status": status, "items": [{"sku": s, "quantity": q} for s, q in items],
            "total": total, "message": "x"}


def test_good_recommendation_passes():
    assert problems(rec([("MANGO", 1), ("LIME", 2), ("WATER", 2)], 900), make_intent()) == []


def test_wrong_total_fails():
    assert problems(rec([("MANGO", 1)], 100), make_intent())


def test_over_budget_fails():
    assert problems(rec([("MANGO", 4)], 1200), make_intent())


def test_over_stock_fails():
    assert problems(rec([("MANGO", 5)], 1500), make_intent(budget=5000))


def test_out_of_stock_sku_fails():
    assert problems(rec([("BERRY", 1)], 400), make_intent())


def test_unknown_sku_fails():
    assert problems(rec([("COLA", 1)], 50), make_intent())


def test_duplicate_sku_fails():
    assert problems(rec([("LIME", 1), ("LIME", 1)], 400), make_intent())


def test_ignoring_an_exclusion_fails():
    assert problems(rec([("WATER", 2)], 200), make_intent(exclude=["WATER"]))


def test_clarification_with_items_fails():
    assert problems(rec([("WATER", 1)], 100, status="clarification"), None)


def test_bad_schema_fails():
    assert problems({"status": "maybe", "items": [], "total": 0, "message": ""}, None)


def test_fallback_is_valid():
    assert problems(fallback_response(), None) == []


def test_message_uses_code_numbers():
    decision = decide(make_intent())
    assert build_message(decision) == ("I suggest 1 case of mango drink, 2 cases of lime soda "
                                       "and 2 cases of drinking water. Total ₹900, "
                                       "within your ₹900 budget.")
