# business-rules

A Python library template with `src/` layout, pytest, ruff, and mypy.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### SQLAlchemy 2.x bridge

```bash
pip install "business-rules[sqlalchemy2]"
```

```python
import business_rules.bridges.sqlalchemy2  # requires the extra
```

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=business_rules --cov-report=term-missing

# Lint
ruff check src tests
ruff format --check src tests

# Type check
mypy src tests
```

## Project structure

```
business-rules/
├── pyproject.toml
├── README.md
├── src/
│   └── business_rules/
│       ├── __init__.py
│       ├── example.py
│       ├── py.typed
│       └── bridges/
│           ├── __init__.py
│           └── sqlalchemy2/
│               ├── __init__.py
│               └── py.typed
└── tests/
    ├── test_example.py
    └── sqlalchemy2/
        ├── test_import.py
        └── test_import_without_dependency.py
```
