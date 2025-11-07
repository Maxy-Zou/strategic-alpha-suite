# Testing Guide

## Setup

To run tests, you'll need to set up a virtual environment first:

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r strategic_alpha/requirements.txt
pip install -r sal_dashboard/requirements.txt
pip install pytest pytest-cov pytest-mock
```

## Running Tests

### Backend Tests (strategic_alpha)

```bash
cd strategic_alpha
pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html
```

This will:
- Run all backend tests
- Show coverage percentage for each module
- Generate an HTML coverage report in `htmlcov/`

### Dashboard Tests (sal_dashboard)

```bash
cd sal_dashboard
pytest tests/ -v --cov=src --cov=app --cov-report=term-missing --cov-report=html
```

### Run All Tests

From the project root:

```bash
pytest strategic_alpha/tests/ sal_dashboard/tests/ -v
```

## Test Structure

### Backend Tests (`strategic_alpha/tests/`)
- `conftest.py` - Shared fixtures (mock data, API responses)
- `test_valuation.py` - DCF and peer comps tests
- `test_macro.py` - Macro analysis tests
- `test_supply.py` - Supply chain network tests
- `test_risk.py` - Risk metrics (VaR, stress tests)

### Dashboard Tests (`sal_dashboard/tests/`)
- `test_database.py` - Database operations (SQLite CRUD)
- `test_rate_limiter.py` - API rate limiting logic
- `test_health.py` - Health check system

## Coverage Goals

- **Target**: 80%+ coverage
- **Critical modules**: valuation, database, rate_limiter should have 90%+
- **Lower priority**: CLI interfaces, visualization code

## Continuous Integration

Tests are automatically run on every push via GitHub Actions. See `.github/workflows/ci.yml`.

To run tests locally before pushing:

```bash
make test  # If you have make installed
# or
pytest strategic_alpha/tests/ sal_dashboard/tests/
```

## Writing New Tests

### Use the fixtures from conftest.py:

```python
def test_my_feature(mock_yfinance_ticker_info, sample_macro_data):
    # Use the fixtures
    result = my_function(mock_yfinance_ticker_info)
    assert result.ticker == 'NVDA'
```

### Test naming conventions:
- `test_<feature>_success` - Happy path
- `test_<feature>_failure` - Error handling
- `test_<feature>_edge_case` - Edge cases

### Mock external APIs:

```python
def test_api_call(monkeypatch):
    def mock_download(*args, **kwargs):
        return pd.DataFrame({'Close': [100, 101, 102]})

    monkeypatch.setattr('yfinance.download', mock_download)
    # Now test your function
```

## Troubleshooting

### Import errors
Make sure you're running tests from the correct directory and your virtual environment is activated.

### Database tests failing
Check that `sal_dashboard/data/database/` directory doesn't have permission issues.

### Coverage not showing
Ensure pytest-cov is installed: `pip install pytest-cov`

## Next Steps

- [ ] Add integration tests (full end-to-end workflows)
- [ ] Add performance tests (DCF calculation speed)
- [ ] Add frontend tests using Streamlit's testing framework
- [ ] Set up test data snapshots for regression testing
