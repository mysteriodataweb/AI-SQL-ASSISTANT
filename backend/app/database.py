import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from app.config import get_settings

CUSTOMERS = 60
PRODUCTS = 45
ORDERS = 600

COUNTRIES = ["France", "Germany", "Spain", "Italy", "UK", "Belgium", "Netherlands", "Canada", "USA", "Portugal"]

FIRST_NAMES = [
    "Alice", "Benoit", "Chloé", "David", "Emma", "Farid", "Gabrielle", "Hugo", "Inès", "Julien",
    "Karim", "Louise", "Marcel", "Nadia", "Olivier", "Pauline", "Quentin", "Roxane", "Sofiane", "Thomas",
]
LAST_NAMES = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau",
    "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David", "Bertrand", "Roux", "Vincent", "Fournier",
]
CATEGORIES = [
    ("Electronics", 0.6),
    ("Home & Kitchen", 1.0),
    ("Sports", 1.2),
    ("Books", 0.3),
    ("Clothing", 0.8),
    ("Beauty", 0.7),
    ("Toys", 0.9),
    ("Garden", 1.1),
]
PRODUCT_SEEDS = {
    "Electronics": ["Smartphone X12", "Wireless Headphones", "4K Monitor", "Bluetooth Speaker", "Laptop Pro", "Smartwatch"],
    "Home & Kitchen": ["Espresso Machine", "Air Fryer", "Robot Vacuum", "Cast Iron Pan", "Cutlery Set"],
    "Sports": ["Yoga Mat", "Dumbbell Set", "Trekking Backpack", "Road Bike", "Tennis Racket"],
    "Books": ["Data Science Handbook", "The Great Gatsby", "Clean Code", "Dune", "Sapiens", "Atomic Habits"],
    "Clothing": ["Cotton T-Shirt", "Denim Jeans", "Running Shoes", "Winter Jacket", "Wool Scarf"],
    "Beauty": ["Face Serum", "Perfume 50ml", "Hair Dryer", "Moisturizer SPF50"],
    "Toys": ["Building Blocks", "Remote Car", "Board Game", "Plush Bear"],
    "Garden": ["Lawn Mower", "Hedge Trimmer", "Garden Furniture Set", "Plant Pots"],
}
ORDER_STATUSES = ["completed", "completed", "completed", "pending", "shipped", "shipped", "cancelled"]


def _rng() -> random.Random:
    return random.Random(42)


def create_database(force: bool = False) -> None:
    """Create (and seed) the SQLite database if missing."""
    settings = get_settings()
    path = settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and not force:
        return

    seed_database(path)


def seed_database(path: Path) -> None:
    rng = _rng()
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(path)
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            country TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL REFERENCES categories(id),
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            total REAL NOT NULL
        );
        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL
        );
        CREATE INDEX idx_orders_customer ON orders(customer_id);
        CREATE INDEX idx_orders_created ON orders(created_at);
        CREATE INDEX idx_items_order ON order_items(order_id);
        CREATE INDEX idx_products_category ON products(category_id);
        """
    )

    now = datetime.now()
    start = now - timedelta(days=365)

    for name, _ in CATEGORIES:
        cur.execute("INSERT INTO categories(name) VALUES (?)", (name,))

    cat_ids = {name: idx + 1 for idx, (name, _) in enumerate(CATEGORIES)}

    product_id = 0
    for cat_name, _ in CATEGORIES:
        price_base = {"Books": 25, "Beauty": 40, "Toys": 35}.get(cat_name, 60)
        for pname in PRODUCT_SEEDS[cat_name]:
            product_id += 1
            price = round(price_base * rng.uniform(0.6, 1.6), 2)
            stock = rng.randint(0, 250)
            cur.execute(
                "INSERT INTO products(name, category_id, price, stock) VALUES (?, ?, ?, ?)",
                (pname, cat_ids[cat_name], price, stock),
            )

    created_at_list: list[tuple[int, str]] = []
    for cid in range(1, CUSTOMERS + 1):
        first = rng.choice(FIRST_NAMES)
        last = rng.choice(LAST_NAMES)
        country = rng.choice(COUNTRIES)
        created = start + timedelta(days=rng.randint(0, 365))
        email = f"{first.lower()}.{last.lower()}{cid}@example.com"
        cur.execute(
            "INSERT INTO customers(first_name, last_name, email, country, created_at) VALUES (?, ?, ?, ?, ?)",
            (first, last, email, country, created.isoformat(sep=" ", timespec="seconds")),
        )
        created_at_list.append((cid, created))

    order_id = 0
    for _ in range(ORDERS):
        cid, created = created_at_list[rng.randrange(len(created_at_list))]
        status = rng.choice(ORDER_STATUSES)
        order_date = created + timedelta(days=rng.randint(0, 364))
        order_date = min(order_date, now)
        n_items = rng.randint(1, 5)
        total = 0.0
        order_id += 1
        picked = rng.sample(range(1, product_id + 1), n_items)
        for pid in picked:
            qty = rng.randint(1, 4)
            unit = round(rng.uniform(15, 220), 2)
            total += qty * unit
            cur.execute(
                "INSERT INTO order_items(order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (order_id, pid, qty, unit),
            )
        cur.execute(
            "INSERT INTO orders(id, customer_id, status, created_at, total) VALUES (?, ?, ?, ?, ?)",
            (order_id, cid, status, order_date.isoformat(sep=" ", timespec="seconds"), round(total, 2)),
        )

    conn.commit()
    conn.close()
