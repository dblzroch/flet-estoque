# flet-estoque

> Inventory control with barcode, low-stock alerts and turnover report.

[![CI](https://github.com/dblzroch/flet-estoque/actions/workflows/ci.yml/badge.svg)](https://github.com/dblzroch/flet-estoque/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](pyproject.toml)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

Controle de estoque desktop app built with [Flet](https://flet.dev/). Manage products,
track stock movements, get low-stock alerts and view turnover reports.

## Quickstart

```bash
# Clone
git clone https://github.com/dblzroch/flet-estoque.git
cd flet-estoque

# Install (uv)
uv sync --dev

# Run the desktop app
uv run flet-estoque
```

## How it works

- **UI**: Flet (Flutter-based) desktop/mobile GUI.
- **Storage**: SQLite database for products and stock movements.
- **Features**: Product catalog, barcode lookup, stock in/out movements,
  low-stock alerts, turnover report, export to CSV.
- **Tests**: `pytest` with coverage gate at 80%.
- **CI**: GitHub Actions runs ruff, mypy and pytest on every push/PR.

## Tests & quality

```bash
make test      # pytest with coverage
make lint      # ruff + mypy
make fmt       # ruff format
```

## License

MIT
