from shelfhelp.models import Intent
from shelfhelp.rules import total
from shelfhelp.solver import explain_failure, solve


def make_intent(**changes) -> Intent:
    fields = dict(budget=900, budget_unclear=False, include=[], exclude=[], only=None,
                  min_qty={}, exact_qty={}, no_substitutes=False,
                  unknown_products=[], manipulation=False)
    fields.update(changes)
    return Intent(**fields)


def test_900_no_preferences_uses_full_budget_with_a_mix():
    order = solve(make_intent())
    assert total(order) == 900
    assert len(order) >= 2
    assert order == {"MANGO": 1, "LIME": 2, "WATER": 2}


def test_900_with_mango_and_lime():
    order = solve(make_intent(include=["MANGO", "LIME"]))
    assert order["MANGO"] >= 1 and order["LIME"] >= 1
    assert total(order) <= 900


def test_budget_too_small():
    intent = make_intent(budget=50)
    assert solve(intent) is None
    assert "₹100" in explain_failure(intent)


def test_only_berry_is_impossible():
    assert solve(make_intent(only=["BERRY"])) is None


def test_excluding_everything_in_stock():
    assert solve(make_intent(exclude=["MANGO", "LIME", "WATER"])) is None


def test_min_qty_above_stock():
    intent = make_intent(min_qty={"MANGO": 5}, budget=5000)
    assert solve(intent) is None
    assert "only have 4" in explain_failure(intent)


def test_exact_qty_is_respected():
    order = solve(make_intent(exact_qty={"LIME": 2}))
    assert order["LIME"] == 2
    assert total(order) <= 900


def test_solver_is_deterministic():
    assert solve(make_intent(budget=1300)) == solve(make_intent(budget=1300))
