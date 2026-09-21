"""Create the analytics schema and fill it with realistic business data.

Run with:  python -m app.database.seed

The data is generated from a fixed random seed, so every run produces exactly
the same database. A few patterns are planted on purpose so that analytical
questions have real answers to find.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.config import ADMIN_DATABASE_URL

RANDOM_SEED = 42
START_DATE = date(2024, 1, 1)
END_DATE = date(2026, 8, 31)

N_CUSTOMERS = 800
N_PRODUCTS = 120
BASE_ORDERS_PER_MONTH = 320
MONTHLY_GROWTH = 0.012

# Planted pattern: March 2026 is a bad month, mostly because of Electronics.
SHOCK_MONTH = (2026, 3)
SHOCK_ORDER_FACTOR = 0.93
SHOCK_ELECTRONICS_FACTOR = 0.50
SHOCK_CANCEL_RATE = 0.12
NORMAL_CANCEL_RATE = 0.07
REFUND_RATE = 0.03

SEASONALITY = {
    1: 0.88, 2: 0.85, 3: 1.00, 4: 0.98, 5: 1.02, 6: 1.00,
    7: 1.03, 8: 1.05, 9: 1.00, 10: 1.08, 11: 1.28, 12: 1.35,
}

# category_name -> (min price, max price, base popularity)
CATEGORIES = {
    "Electronics": (120, 900, 0.14),
    "Home & Kitchen": (25, 400, 0.15),
    "Fashion": (15, 200, 0.18),
    "Sports & Outdoors": (20, 500, 0.10),
    "Beauty": (8, 120, 0.12),
    "Books": (5, 45, 0.10),
    "Toys": (10, 150, 0.08),
    "Grocery": (3, 60, 0.07),
}

PRODUCT_WORDS = {
    "Electronics": (["Aurex", "Novik", "Zentro", "Kaito"], ["Laptop", "Smartphone", "Headphones", "Monitor", "Tablet", "Smartwatch", "Camera"]),
    "Home & Kitchen": (["Hearth", "Vireo", "Casalux"], ["Blender", "Cookware Set", "Air Fryer", "Coffee Maker", "Vacuum", "Lamp"]),
    "Fashion": (["Verda", "Larkin", "Mondo"], ["Jacket", "Sneakers", "Jeans", "Dress", "Backpack", "Sunglasses"]),
    "Sports & Outdoors": (["Trailix", "Summit", "Peakline"], ["Tent", "Running Shoes", "Yoga Mat", "Bicycle Helmet", "Dumbbell Set"]),
    "Beauty": (["Lumea", "Sable", "Fleur"], ["Serum", "Shampoo", "Lipstick", "Face Cream", "Perfume"]),
    "Books": (["Quill", "Paperline"], ["Novel", "Cookbook", "Biography", "Guide", "Workbook"]),
    "Toys": (["Blocktop", "Jollio"], ["Building Blocks", "Puzzle", "Board Game", "Action Figure", "Plush Toy"]),
    "Grocery": (["Fieldco", "Pantri"], ["Olive Oil", "Coffee Beans", "Tea Box", "Pasta Pack", "Snack Box"]),
}

REGIONS = ["North", "South", "East", "West"]
REGION_WEIGHTS = [0.28, 0.26, 0.24, 0.22]

FIRST_NAMES = ["Aarav", "Diya", "Rohan", "Meera", "Kabir", "Sara", "Arjun", "Nisha", "Vikram", "Priya",
               "Liam", "Emma", "Noah", "Olivia", "Ethan", "Ava", "Lucas", "Mia", "Leo", "Zoe",
               "Hana", "Yuki", "Omar", "Layla", "Pablo", "Ines", "Tomas", "Clara", "Iva", "Nils"]
LAST_NAMES = ["Sharma", "Patel", "Iyer", "Nair", "Chawla", "Bose", "Mehta", "Rao",
              "Smith", "Johnson", "Brown", "Garcia", "Muller", "Rossi", "Dubois", "Novak",
              "Kim", "Tanaka", "Haddad", "Silva", "Olsen", "Walsh", "Costa", "Fischer"]


def month_range(start: date, end: date) -> list[tuple[int, int]]:
    """Every (year, month) pair from start to end, inclusive."""
    months: list[tuple[int, int]] = []
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        months.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def days_in_month(year: int, month: int) -> int:
    first_next = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return (first_next - date(year, month, 1)).days


def generate_categories() -> list[dict]:
    return [{"category_id": i, "category_name": name} for i, name in enumerate(CATEGORIES, start=1)]


def generate_products(rng: random.Random, categories: list[dict]) -> list[dict]:
    products: list[dict] = []
    product_id = 1
    per_category = N_PRODUCTS // len(categories)
    for category in categories:
        name = category["category_name"]
        low, high, _ = CATEGORIES[name]
        brands, items = PRODUCT_WORDS[name]
        for _ in range(per_category):
            price = round(rng.uniform(low, high), 2)
            products.append({
                "product_id": product_id,
                "product_name": f"{rng.choice(brands)} {rng.choice(items)} {rng.randint(100, 999)}",
                "category_id": category["category_id"],
                "unit_price": price,
            })
            product_id += 1
    return products


def generate_customers(rng: random.Random) -> list[dict]:
    customers: list[dict] = []
    for customer_id in range(1, N_CUSTOMERS + 1):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        signup = START_DATE - timedelta(days=rng.randint(0, 730)) + timedelta(days=rng.randint(0, 600))
        customers.append({
            "customer_id": customer_id,
            "customer_name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}{customer_id}@example.com",
            "region": rng.choices(REGIONS, weights=REGION_WEIGHTS, k=1)[0],
            "signup_date": min(signup, END_DATE),
        })
    return customers


def category_weights(region: str, year: int, month: int) -> dict[str, float]:
    """Popularity of each category for one order."""
    weights = {name: cfg[2] for name, cfg in CATEGORIES.items()}
    if region == "West":
        # Planted pattern: the West buys more expensive things, so its AOV is highest.
        weights["Electronics"] *= 1.9
        weights["Sports & Outdoors"] *= 1.6
        weights["Grocery"] *= 0.4
    if (year, month) == SHOCK_MONTH:
        weights["Electronics"] *= SHOCK_ELECTRONICS_FACTOR
    return weights


def generate_orders_and_items(rng: random.Random, customers: list[dict], products: list[dict]):
    products_by_category: dict[int, list[dict]] = {}
    for product in products:
        products_by_category.setdefault(product["category_id"], []).append(product)

    category_id_by_name = {name: index for index, name in enumerate(CATEGORIES, start=1)}
    customers_by_id = {c["customer_id"]: c for c in customers}
    customer_ids = list(customers_by_id)

    # Planted pattern: eight customers spend far more in 2026 than in 2025.
    growth_customers = set(rng.sample(customer_ids, 8))

    orders: list[dict] = []
    items: list[dict] = []
    order_id = 1
    item_id = 1

    for index, (year, month) in enumerate(month_range(START_DATE, END_DATE)):
        expected = BASE_ORDERS_PER_MONTH * ((1 + MONTHLY_GROWTH) ** index) * SEASONALITY[month]
        if (year, month) == SHOCK_MONTH:
            expected *= SHOCK_ORDER_FACTOR
        n_orders = max(1, int(rng.gauss(expected, expected * 0.05)))

        weights = [12 if (year >= 2026 and cid in growth_customers) else 1 for cid in customer_ids]
        cancel_rate = SHOCK_CANCEL_RATE if (year, month) == SHOCK_MONTH else NORMAL_CANCEL_RATE

        for _ in range(n_orders):
            customer_id = rng.choices(customer_ids, weights=weights, k=1)[0]
            region = customers_by_id[customer_id]["region"]
            order_day = rng.randint(1, days_in_month(year, month))

            roll = rng.random()
            status = "cancelled" if roll < cancel_rate else "refunded" if roll < cancel_rate + REFUND_RATE else "completed"

            orders.append({
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": date(year, month, order_day),
                "status": status,
            })

            weights_by_category = category_weights(region, year, month)
            n_items = rng.choices([1, 2, 3, 4], weights=[0.45, 0.30, 0.17, 0.08], k=1)[0]
            if region == "West":
                n_items = min(4, n_items + rng.choices([0, 1], weights=[0.7, 0.3], k=1)[0])

            for _ in range(n_items):
                category_name = rng.choices(list(weights_by_category), weights=list(weights_by_category.values()), k=1)[0]
                product = rng.choice(products_by_category[category_id_by_name[category_name]])
                items.append({
                    "order_item_id": item_id,
                    "order_id": order_id,
                    "product_id": product["product_id"],
                    "quantity": rng.choices([1, 2, 3, 4], weights=[0.62, 0.24, 0.09, 0.05], k=1)[0],
                    "unit_price": round(float(product["unit_price"]) * rng.uniform(0.95, 1.05), 2),
                    "discount_pct": rng.choices([0.0, 0.05, 0.10], weights=[0.60, 0.25, 0.15], k=1)[0],
                })
                item_id += 1
            order_id += 1

    return orders, items


def insert_rows(connection, table: str, rows: list[dict]) -> None:
    """Insert many rows in one statement (psycopg batches them for us)."""
    if not rows:
        return
    columns = list(rows[0])
    statement = text(
        f"INSERT INTO {table} ({', '.join(columns)}) "
        f"VALUES ({', '.join(':' + column for column in columns)})"
    )
    connection.execute(statement, rows)


def reset_sequences(connection) -> None:
    """We supplied the IDs ourselves, so the SERIAL counters must be moved forward."""
    for table, column in [
        ("categories", "category_id"), ("products", "product_id"), ("customers", "customer_id"),
        ("orders", "order_id"), ("order_items", "order_item_id"),
    ]:
        connection.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{table}', '{column}'), "
            f"COALESCE((SELECT MAX({column}) FROM {table}), 1))"
        ))


def summarize(connection) -> None:
    counts = connection.execute(text("""
        SELECT (SELECT COUNT(*) FROM customers)   AS customers,
               (SELECT COUNT(*) FROM categories)  AS categories,
               (SELECT COUNT(*) FROM products)    AS products,
               (SELECT COUNT(*) FROM orders)      AS orders,
               (SELECT COUNT(*) FROM order_items) AS order_items
    """)).mappings().one()
    print("\nRows loaded:")
    for name, value in counts.items():
        print(f"  {name:<12} {value:,}")

    print("\nMonthly revenue in 2026 (completed orders):")
    rows = connection.execute(text("""
        SELECT to_char(o.order_date, 'YYYY-MM') AS month,
               ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct))) AS revenue
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.status = 'completed' AND o.order_date >= DATE '2026-01-01'
        GROUP BY 1 ORDER BY 1
    """)).all()
    for month, revenue in rows:
        print(f"  {month}  {revenue:>12,.0f}")

    print("\nMarch 2026 vs March 2025 by category:")
    rows = connection.execute(text("""
        SELECT c.category_name,
               ROUND(SUM(CASE WHEN o.order_date < DATE '2026-01-01' THEN oi.quantity * oi.unit_price * (1 - oi.discount_pct) END)) AS march_2025,
               ROUND(SUM(CASE WHEN o.order_date >= DATE '2026-01-01' THEN oi.quantity * oi.unit_price * (1 - oi.discount_pct) END)) AS march_2026
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.order_id
        JOIN products p ON p.product_id = oi.product_id
        JOIN categories c ON c.category_id = p.category_id
        WHERE o.status = 'completed'
          AND (o.order_date BETWEEN DATE '2025-03-01' AND DATE '2025-03-31'
            OR o.order_date BETWEEN DATE '2026-03-01' AND DATE '2026-03-31')
        GROUP BY 1 ORDER BY 1
    """)).all()
    for name, march_2025, march_2026 in rows:
        change = (float(march_2026) / float(march_2025) - 1) * 100
        print(f"  {name:<20} {march_2025:>10,.0f} -> {march_2026:>10,.0f}  ({change:+.1f}%)")

    print("\nAverage order value by region (completed orders):")
    rows = connection.execute(text("""
        SELECT cu.region,
               ROUND(AVG(order_total), 2) AS avg_order_value
        FROM (
            SELECT o.order_id, o.customer_id,
                   SUM(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) AS order_total
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.order_id
            WHERE o.status = 'completed'
            GROUP BY o.order_id, o.customer_id
        ) totals
        JOIN customers cu ON cu.customer_id = totals.customer_id
        GROUP BY 1 ORDER BY 2 DESC
    """)).all()
    for region, aov in rows:
        print(f"  {region:<8} {aov:>10,.2f}")


def main() -> None:
    rng = random.Random(RANDOM_SEED)
    engine = create_engine(ADMIN_DATABASE_URL)

    print("Generating data...")
    categories = generate_categories()
    products = generate_products(rng, categories)
    customers = generate_customers(rng)
    orders, items = generate_orders_and_items(rng, customers, products)

    schema_sql = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")

    with engine.begin() as connection:
        print("Creating schema...")
        connection.execute(text(schema_sql))
        print(f"Inserting {len(customers):,} customers, {len(products):,} products, "
              f"{len(orders):,} orders, {len(items):,} order items...")
        insert_rows(connection, "categories", categories)
        insert_rows(connection, "products", products)
        insert_rows(connection, "customers", customers)
        insert_rows(connection, "orders", orders)
        insert_rows(connection, "order_items", items)
        reset_sequences(connection)

    with engine.connect() as connection:
        summarize(connection)

    print("\nDatabase ready.")


if __name__ == "__main__":
    main()