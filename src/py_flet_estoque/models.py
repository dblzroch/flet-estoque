"""Domain models for flet-estoque."""

from dataclasses import dataclass


@dataclass
class Product:
    """A product in inventory."""

    id: int | None = None
    name: str = ""
    sku: str = ""
    barcode: str = ""
    quantity: int = 0
    min_stock: int = 0
    unit_price: float = 0.0


@dataclass
class Movement:
    """A stock movement (in or out)."""

    id: int | None = None
    product_id: int = 0
    type: str = ""  # "in" or "out"
    quantity: int = 0
    created_at: str = ""  # ISO format
