"""Find the best order by checking every possible one. No LLM here.

With 3 in-stock SKUs there are only 5 x 7 x 11 = 385 combinations,
so trying them all is instant and guarantees a correct answer.
"""

from itertools import product

from .catalogue import CATALOGUE, SKU_ORDER, in_stock_skus
from .rules import RULES, Order, total


def candidates() -> list[Order]:
    """Every combination of 0..stock cases for each in-stock SKU."""
    skus = in_stock_skus()
    ranges = [range(CATALOGUE[sku]["stock"] + 1) for sku in skus]
    orders = []
    for quantities in product(*ranges):
        orders.append({sku: qty for sku, qty in zip(skus, quantities) if qty > 0})
    return orders


def score(order: Order, intent) -> tuple:
    """Higher is better. Compared item by item, left to right."""
    quantities = list(order.values()) or [0]
    return (
        total(order),                              # 1. use as much budget as possible
        len(order),                                # 2. prefer a mix of drinks
        -(max(quantities) - min(quantities)),      # 3. prefer balanced quantities
        sum(quantities),                           # 4. prefer more cases for the money
        tuple(order.get(sku, 0) for sku in SKU_ORDER),  # 5. final tie-break: SKU order
    )


def is_valid(order: Order, intent) -> bool:
    return all(rule(order, intent)[0] for rule in RULES)


def solve(intent) -> Order | None:
    valid = [order for order in candidates() if is_valid(order, intent)]
    if not valid:
        return None
    return max(valid, key=lambda order: score(order, intent))


def explain_failure(intent) -> str:
    """Say in plain words why no valid order exists."""
    budget = intent.budget

    for qty_rule in (intent.min_qty, intent.exact_qty):
        for sku, qty in qty_rule.items():
            if qty > CATALOGUE[sku]["stock"]:
                return (f"You asked for {qty} cases of {CATALOGUE[sku]['name'].lower()}, "
                        f"but we only have {CATALOGUE[sku]['stock']} in stock.")

    for sku in intent.include:
        if sku in intent.exclude:
            return f"You both asked for and excluded {CATALOGUE[sku]['name'].lower()}."

    allowed = [sku for sku in in_stock_skus()
               if sku not in intent.exclude and (intent.only is None or sku in intent.only)]
    if not allowed:
        return "None of the drinks you would accept are in stock."

    # The cheapest cost of the cases the customer insists on.
    must_have = {sku: 1 for sku in intent.include}
    must_have.update(intent.min_qty)
    must_have.update(intent.exact_qty)
    must_cost = sum(CATALOGUE[sku]["price"] * qty for sku, qty in must_have.items())
    if must_cost > budget:
        return (f"The drinks you asked for cost at least ₹{must_cost}, "
                f"which is more than your ₹{budget} budget.")

    cheapest = min(CATALOGUE[sku]["price"] for sku in allowed)
    if cheapest > budget:
        return (f"The cheapest drink you would accept costs ₹{cheapest} a case, "
                f"which is more than your ₹{budget} budget.")

    return "No order fits all of your conditions together."
