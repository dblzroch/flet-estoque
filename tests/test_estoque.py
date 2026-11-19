"""Tests for flet-estoque database and models."""

import pytest

from py_flet_estoque.database import Database
from py_flet_estoque.models import Movement, Product


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------
def test_product_defaults():
    p = Product(name="Mouse", sku="MSE-001", quantity=10, min_stock=2, unit_price=45.0)
    assert p.name == "Mouse"
    assert p.sku == "MSE-001"
    assert p.quantity == 10
    assert p.min_stock == 2
    assert p.unit_price == 45.0
    assert p.id is None


def test_movement_defaults():
    m = Movement(product_id=1, type="in", quantity=5)
    assert m.product_id == 1
    assert m.type == "in"
    assert m.quantity == 5
    assert m.id is None


# ------------------------------------------------------------------
# Database: products CRUD
# ------------------------------------------------------------------
def test_add_and_get_product(tmp_path):
    db = Database(tmp_path / "test.db")
    rid = db.add_product(
        Product(name="Mouse", sku="MSE-001", quantity=10, min_stock=2, unit_price=45.0)
    )
    assert rid == 1

    p = db.get_product(1)
    assert p is not None
    assert p.name == "Mouse"
    assert p.sku == "MSE-001"
    assert p.quantity == 10


def test_get_product_not_found(tmp_path):
    db = Database(tmp_path / "test.db")
    assert db.get_product(999) is None


def test_get_products_ordered(tmp_path):
    db = Database(tmp_path / "test.db")
    db.add_product(Product(name="Z", sku="Z-001"))
    db.add_product(Product(name="A", sku="A-001"))

    products = db.get_products()
    assert len(products) == 2
    assert products[0].name == "A"


def test_sku_unique(tmp_path):
    import sqlite3

    db = Database(tmp_path / "test.db")
    db.add_product(Product(name="A", sku="DUP-001"))
    with pytest.raises(sqlite3.IntegrityError):
        db.add_product(Product(name="B", sku="DUP-001"))


def test_update_product(tmp_path):
    db = Database(tmp_path / "test.db")
    rid = db.add_product(Product(name="Velho", sku="V-001", quantity=5))
    product_update = Product(id=rid, name="Novo", sku="V-001", quantity=20)
    assert db.update_product(product_update) is True
    p = db.get_product(rid)
    assert p is not None
    assert p.name == "Novo"
    assert p.quantity == 20


def test_delete_product(tmp_path):
    db = Database(tmp_path / "test.db")
    rid = db.add_product(Product(name="Temp", sku="T-001"))
    assert db.delete_product(rid) is True
    assert db.get_products() == []


def test_delete_product_cascades_to_movements(tmp_path):
    db = Database(tmp_path / "test.db")
    pid = db.add_product(Product(name="Item", sku="I-001"))
    db.add_movement(Movement(product_id=pid, type="in", quantity=5))
    db.add_movement(Movement(product_id=pid, type="out", quantity=2))

    assert db.delete_product(pid) is True
    assert db.get_movements() == []


# ------------------------------------------------------------------
# Database: low stock
# ------------------------------------------------------------------
def test_low_stock(tmp_path):
    db = Database(tmp_path / "test.db")
    pid1 = db.add_product(Product(name="Baixo", sku="LOW-001", quantity=1, min_stock=5))
    db.add_product(Product(name="Ok", sku="OK-001", quantity=10, min_stock=5))
    db.add_product(Product(name="Sem min", sku="NOMIN-001", quantity=0))

    low = db.get_low_stock()
    assert len(low) == 1
    assert low[0].id == pid1


# ------------------------------------------------------------------
# Database: movements
# ------------------------------------------------------------------
def test_add_and_get_movement(tmp_path):
    db = Database(tmp_path / "test.db")
    pid = db.add_product(Product(name="Item", sku="I-001"))
    rid = db.add_movement(Movement(product_id=pid, type="in", quantity=5))
    assert rid == 1

    movements = db.get_movements(pid)
    assert len(movements) == 1
    assert movements[0].type == "in"
    assert movements[0].quantity == 5


# ------------------------------------------------------------------
# Database: turnover report
# ------------------------------------------------------------------
def test_turnover_report(tmp_path):
    db = Database(tmp_path / "test.db")
    pid = db.add_product(Product(name="Produto X", sku="PX-001"))
    db.add_movement(Movement(product_id=pid, type="in", quantity=10))
    db.add_movement(Movement(product_id=pid, type="out", quantity=3))

    report = db.turnover_report()
    assert len(report) == 1
    assert report[0][0] == "Produto X"
    assert report[0][1] == 10  # total_in
    assert report[0][2] == 3  # total_out


# ------------------------------------------------------------------
# Database: update_stock
# ------------------------------------------------------------------
def test_update_stock(tmp_path):
    db = Database(tmp_path / "test.db")
    pid = db.add_product(Product(name="Item", sku="I-001", quantity=10))
    assert db.update_stock(pid, 25) is True
    p = db.get_product(pid)
    assert p is not None
    assert p.quantity == 25


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------
def test_cli_main(monkeypatch):
    """Test that cli.main calls ft.app with the right target."""
    import py_flet_estoque.cli as cli_mod

    called = {}

    def fake_app(target):
        called["target"] = target

    monkeypatch.setattr(cli_mod, "ft_app", fake_app)
    cli_mod.main()
    assert callable(called.get("target"))
