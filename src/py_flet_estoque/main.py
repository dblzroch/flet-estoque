"""Flet UI for flet-estoque.  # pragma: no cover"""

from pathlib import Path

import flet as ft

from py_flet_estoque.database import Database
from py_flet_estoque.models import Product


def app_main(page: ft.Page) -> None:  # pragma: no cover
    """Build the Flet UI."""
    page.title = "py-estoque"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 550  # type: ignore[attr-defined]
    page.window_height = 650  # type: ignore[attr-defined]

    db = Database(Path.home() / ".local" / "share" / "flet-estoque" / "estoque.db")

    # --- UI state ---
    name_field = ft.TextField(label="Nome do produto", width=250)
    sku_field = ft.TextField(label="SKU", width=150)
    barcode_field = ft.TextField(label="Código de barras", width=150)
    qty_field = ft.TextField(
        label="Quantidade", width=100, keyboard_type=ft.KeyboardType.NUMBER
    )
    min_stock_field = ft.TextField(
        label="Estoque mínimo", width=100, keyboard_type=ft.KeyboardType.NUMBER
    )
    price_field = ft.TextField(
        label="Preço unitário", width=100, keyboard_type=ft.KeyboardType.NUMBER
    )

    products_list = ft.ListView(expand=True, spacing=8, padding=20)
    alert_text = ft.Text(size=14, color=ft.colors.RED)
    stats_text = ft.Text(size=14)

    def refresh() -> None:
        """Refresh the UI from the database."""
        products = db.get_products()
        products_list.controls.clear()

        low_stock = db.get_low_stock()
        if low_stock:
            names = ", ".join(p.name for p in low_stock)
            alert_text.value = f"Alerta de estoque baixo: {names}"
            alert_text.color = ft.colors.RED
        else:
            alert_text.value = "Sem alertas de estoque baixo"
            alert_text.color = ft.colors.GREEN

        for p in products:
            is_low = p.min_stock > 0 and p.quantity <= p.min_stock
            row_color = ft.colors.ORANGE_100 if is_low else None
            products_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(p.name, weight=ft.FontWeight.W_500, width=150),
                            ft.Text(f"Qtd: {p.quantity}", width=80),
                            ft.Text(f"Mín: {p.min_stock}", width=80),
                            ft.Text(f"R$ {p.unit_price:.2f}", width=90),
                            ft.Text(p.sku, width=90),
                        ],
                    ),
                    bgcolor=row_color,
                    padding=10,
                    border_radius=6,
                    on_click=lambda e, pid=p.id: edit_product(pid),
                )
            )

        report = db.turnover_report()
        total_in = sum(r[1] for r in report)
        total_out = sum(r[2] for r in report)
        stats_text.value = f"Entradas: {total_in} | Saídas: {total_out}"

        page.update()

    def add_product(e: ft.ControlEvent) -> None:
        """Add a new product from the form."""
        if not name_field.value or not sku_field.value:
            page.snack_bar = ft.SnackBar(ft.Text("Informe nome e SKU"))  # type: ignore[attr-defined]
            page.snack_bar.open = True  # type: ignore[attr-defined]
            page.update()
            return

        try:
            qty = int(qty_field.value or 0)
            min_qty = int(min_stock_field.value or 0)
            price = float(price_field.value or 0)
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Valores numéricos inválidos"))  # type: ignore[attr-defined]
            page.snack_bar.open = True  # type: ignore[attr-defined]
            page.update()
            return

        product = Product(
            name=name_field.value,
            sku=sku_field.value,
            barcode=barcode_field.value or "",
            quantity=qty,
            min_stock=min_qty,
            unit_price=price,
        )
        db.add_product(product)

        name_field.value = ""
        sku_field.value = ""
        barcode_field.value = ""
        qty_field.value = "0"
        min_stock_field.value = "0"
        price_field.value = "0"

        refresh()

    def edit_product(product_id: int) -> None:
        """Show a dialog to edit a product."""
        product = db.get_product(product_id)
        if product is None:
            return

        edit_name = ft.TextField(label="Nome", value=product.name, width=300)
        edit_qty = ft.TextField(
            label="Quantidade",
            value=str(product.quantity),
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        edit_min = ft.TextField(
            label="Mínimo",
            value=str(product.min_stock),
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        edit_price = ft.TextField(
            label="Preço",
            value=str(product.unit_price),
            width=120,
            keyboard_type=ft.KeyboardType.NUMBER,
        )

        def save(e: ft.ControlEvent) -> None:
            if not edit_name.value:
                return
            try:
                assert product.id is not None
                db.update_product(
                    Product(
                        id=product.id,
                        name=edit_name.value,
                        sku=product.sku,
                        barcode=product.barcode,
                        quantity=int(edit_qty.value or 0),
                        min_stock=int(edit_min.value or 0),
                        unit_price=float(edit_price.value or 0),
                    )
                )
            except ValueError:
                return
            dialog.open = False  # type: ignore[has-type]
            page.update()
            refresh()

        dialog = ft.AlertDialog(
            title=ft.Text("Editar produto"),
            content=ft.Column([edit_name, edit_qty, edit_min, edit_price], tight=True),
            actions=[
                ft.TextButton(
                    "Cancelar",
                    on_click=lambda e: setattr(dialog, "open", False),  # type: ignore[has-type]
                ),
                ft.ElevatedButton("Salvar", on_click=save),
            ],
        )
        page.dialog = dialog  # type: ignore[attr-defined]
        dialog.open = True
        page.update()

    def export_csv(e: ft.ControlEvent) -> None:
        """Export all products as CSV text."""
        products = db.get_products()
        lines = ["id,name,sku,barcode,quantity,min_stock,unit_price"]
        for p in products:
            lines.append(
                f"{p.id},{p.name},{p.sku},{p.barcode},{p.quantity},"
                f"{p.min_stock},{p.unit_price}"
            )
        page.snack_bar = ft.SnackBar(ft.Text("\n".join(lines)[:400]))  # type: ignore[attr-defined]
        page.snack_bar.open = True  # type: ignore[attr-defined]
        page.update()

    # --- Layout ---
    page.add(
        ft.Text("Estoque", size=24, weight=ft.FontWeight.BOLD),
        ft.Divider(),
        ft.Row(
            [name_field, sku_field, barcode_field],
            wrap=True,
        ),
        ft.Row(
            [
                qty_field,
                min_stock_field,
                price_field,
                ft.ElevatedButton("Adicionar", on_click=add_product),
            ],
            wrap=True,
        ),
        alert_text,
        stats_text,
        ft.Divider(),
        ft.Text("Produtos", size=18, weight=ft.FontWeight.BOLD),
        products_list,
        ft.ElevatedButton("Exportar CSV", on_click=export_csv),
    )

    refresh()
