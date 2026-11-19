"""Database layer for flet-estoque."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Self

from py_flet_estoque.models import Movement, Product


class Database:
    """SQLite storage for products and stock movements."""

    def __init__(self: Self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self: Self) -> None:
        """Create tables if they don't exist."""
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT NOT NULL UNIQUE,
                barcode TEXT,
                quantity INTEGER NOT NULL DEFAULT 0,
                min_stock INTEGER NOT NULL DEFAULT 0,
                unit_price REAL NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_movements_product
            ON movements(product_id, created_at);
        """
        )
        self.conn.commit()

    def _now(self: Self) -> str:
        return datetime.now().isoformat()

    # --- Products ---

    def add_product(self: Self, product: Product) -> int:
        """Insert a product and return its new id."""
        cur = self.conn.execute(
            """
            INSERT INTO products (name, sku, barcode, quantity, min_stock, unit_price)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                product.name,
                product.sku,
                product.barcode,
                product.quantity,
                product.min_stock,
                product.unit_price,
            ),
        )
        self.conn.commit()
        last_id = cur.lastrowid
        assert last_id is not None
        return int(last_id)

    def get_product(self: Self, product_id: int) -> Product | None:
        """Return a product by id, or None if not found."""
        row = self.conn.execute(
            """
            SELECT id, name, sku, barcode, quantity, min_stock, unit_price
            FROM products WHERE id = ?
            """,
            (product_id,),
        ).fetchone()
        if row is None:
            return None
        return Product(
            id=row["id"],
            name=row["name"],
            sku=row["sku"],
            barcode=row["barcode"] or "",
            quantity=row["quantity"],
            min_stock=row["min_stock"],
            unit_price=row["unit_price"],
        )

    def get_products(self: Self) -> list[Product]:
        """Return all products ordered by name."""
        rows = self.conn.execute(
            """
            SELECT id, name, sku, barcode, quantity, min_stock, unit_price
            FROM products
            ORDER BY name
            """
        ).fetchall()
        return [
            Product(
                id=r["id"],
                name=r["name"],
                sku=r["sku"],
                barcode=r["barcode"] or "",
                quantity=r["quantity"],
                min_stock=r["min_stock"],
                unit_price=r["unit_price"],
            )
            for r in rows
        ]

    def get_low_stock(self: Self) -> list[Product]:
        """Return products below their min_stock threshold."""
        rows = self.conn.execute(
            """
            SELECT id, name, sku, barcode, quantity, min_stock, unit_price
            FROM products
            WHERE quantity <= min_stock AND min_stock > 0
            ORDER BY name
            """
        ).fetchall()
        return [
            Product(
                id=r["id"],
                name=r["name"],
                sku=r["sku"],
                barcode=r["barcode"] or "",
                quantity=r["quantity"],
                min_stock=r["min_stock"],
                unit_price=r["unit_price"],
            )
            for r in rows
        ]

    def update_product(self: Self, product: Product) -> bool:
        """Update a product. Returns True if a row was updated."""
        assert product.id is not None
        cur = self.conn.execute(
            """
            UPDATE products
            SET name = ?, sku = ?, barcode = ?, quantity = ?, min_stock = ?,
                  unit_price = ?
            WHERE id = ?
            """,
            (
                product.name,
                product.sku,
                product.barcode,
                product.quantity,
                product.min_stock,
                product.unit_price,
                product.id,
            ),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def delete_product(self: Self, product_id: int) -> bool:
        """Delete a product and its movements. Returns True if a row was deleted."""
        cur = self.conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def update_stock(self: Self, product_id: int, new_quantity: int) -> bool:
        """Update the stock quantity of a product."""
        assert product_id > 0
        cur = self.conn.execute(
            "UPDATE products SET quantity = ? WHERE id = ?",
            (new_quantity, product_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    # --- Movements ---

    def add_movement(self: Self, movement: Movement) -> int:
        """Insert a stock movement and return its new id."""
        cur = self.conn.execute(
            """
            INSERT INTO movements (product_id, type, quantity, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                movement.product_id,
                movement.type,
                movement.quantity,
                movement.created_at or self._now(),
            ),
        )
        self.conn.commit()
        last_id = cur.lastrowid
        assert last_id is not None
        return int(last_id)

    def get_movements(self: Self, product_id: int | None = None) -> list[Movement]:
        """Return all movements, optionally filtered by product."""
        if product_id is not None:
            rows = self.conn.execute(
                """
                SELECT id, product_id, type, quantity, created_at
                FROM movements
                WHERE product_id = ?
                ORDER BY created_at DESC
                """,
                (product_id,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT id, product_id, type, quantity, created_at
                FROM movements
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [
            Movement(
                id=r["id"],
                product_id=r["product_id"],
                type=r["type"],
                quantity=r["quantity"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    # --- Reports ---

    def turnover_report(self: Self) -> list[tuple[str, int, int]]:
        """Return (product_name, total_in, total_out) for all products."""
        rows = self.conn.execute(
            """
            SELECT p.name as name,
                   COALESCE(SUM(CASE WHEN m.type = 'in' THEN m.quantity ELSE 0 END), 0)
                   as total_in,
                   COALESCE(SUM(CASE WHEN m.type = 'out' THEN m.quantity ELSE 0 END), 0)
                   as total_out
            FROM products p
            LEFT JOIN movements m ON p.id = m.product_id
            GROUP BY p.id, p.name
            ORDER BY p.name
            """
        ).fetchall()
        return [(r["name"], int(r["total_in"]), int(r["total_out"])) for r in rows]

    def close(self: Self) -> None:
        """Close the database connection."""
        self.conn.close()
