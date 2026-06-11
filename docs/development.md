# Development

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
