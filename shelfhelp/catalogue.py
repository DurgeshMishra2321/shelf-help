"""The single source of truth for products, prices and stock.

Money is always whole rupees (int). No price or stock number may appear
anywhere else in the code.
"""

CATALOGUE = {
    "MANGO": {"name": "Mango drink",    "price": 300, "stock": 4},
    "LIME":  {"name": "Lime soda",      "price": 200, "stock": 6},
    "WATER": {"name": "Drinking water", "price": 100, "stock": 10},
    "BERRY": {"name": "Berry fizz",     "price": 400, "stock": 0},
}

# The fixed SKU order. Used wherever we need a stable, repeatable order.
SKU_ORDER = list(CATALOGUE)


def in_stock_skus() -> list[str]:
    return [sku for sku in SKU_ORDER if CATALOGUE[sku]["stock"] > 0]
