# SAL Dashboard

`sal_dashboard` is a Streamlit front-end for the `strategic_alpha` analytics engine. It wraps the macro, supply-chain, valuation, and risk modules from the backend repository (expected at `../strategic_alpha/`) to deliver an interactive, analyst-friendly interface with reporting.

## Prerequisites
- Python 3.12
- Backend repo from Prompt A located at `../strategic_alpha/`
- macOS users should ensure Command Line Tools are installed: `xcode-select --install`

## Setup
Clone or copy this directory alongside the backend repo, then run the following commands from the project root:

```
python -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m streamlit run app/streamlit_app.py
```

The app automatically loads environment variables from `.env` (copy `.env.example`) to pick up optional API keys:

- `FRED_API_KEY` for live macro pulls (falls back to `data/macro/sample_macro.csv` if missing).
- `SEC_API_KEY` for SEC data (fallback text in `data/financials/sample_10k_risk.txt`).
- `SHOCK_PCT`, `RISK_PEER_TICKERS`, `SUPPLY_SHOCK_TICKERS` allow overrides of default risk settings.

## Make Targets
- `make venv` – create the virtual environment and install dependencies.
- `make run` – launch the Streamlit application.
- `make fmt` – format `app/` and `src/` using Black.
- `make lint` – lint the code with Ruff.

## Features
- **Overview**: KPI cards for market cap, enterprise value, valuation multiples, plus trailing 12-month price chart.
- **Macro Context**: Line charts for CPI YoY, unemployment, Fed funds, and industrial production. Commentary summarizes implications.
- **Supply Map**: Network visualization and chokepoint table built on the backend supply analysis; download metrics as CSV.
- **Valuation**: Editable DCF assumptions with sensitivity heatmap, peer comparables table, and percentile context.
- **Risk**: Historical and variance-covariance VaR, configurable shock stress test, and histogram of daily returns.
- **Report**: Generate and download a Markdown memo summarizing all insights (`reports/<ticker>_dashboard_memo.md`).

## Data & Fallbacks
Bundled sample datasets under `data/` enable offline usage. When API keys are absent or live calls fail, the backend modules emit warnings and switch to the provided CSV/text files, keeping the UI responsive.

## Repository Layout
- `app/` – Streamlit entrypoint & UI components.
- `src/` – Thin wrappers around backend modules plus configuration helpers.
- `data/` – Sample macro series, supply edges, and risk-factor text.
- `artifacts/`, `reports/` – Output directories (kept in git via `.gitkeep`).
- `Makefile`, `requirements.txt`, `.env.example`, `README.md` – Developer ergonomics.
