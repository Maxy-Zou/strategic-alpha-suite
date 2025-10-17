# Strategic Alpha

Strategic Alpha is a Python 3.12 research wrapper that builds a fast, reproducible view of a semiconductor company and its strategic suppliers across macro, supply-chain, valuation, and risk dimensions. The CLI-first workflow produces artifacts, tabular summaries, and a Markdown memo for quick investment readouts.

## Project Layout
- `src/config.py` — Pydantic settings with `.env` support and default peer lists.
- `src/macro_analysis.py` — FRED-powered (or fallback) macro snapshot with charting.
- `src/supply_mapping.py` — networkx supply-map analytics, chokepoint ranking, future ingestion stub.
- `src/valuation.py` — DCF engine, comps table assembly, deterministic fallbacks.
- `src/risk_model.py` — 60/40 portfolio VaR (historical & variance-covariance) plus foundry stress.
- `src/report_generator.py` — Markdown memo assembly linking generated artifacts.
- `src/analyze_company.py` — Typer CLI orchestrator (`sal` entry point) exposing module subcommands.
- `data/` — offline-ready macro series, supply edges, and sample 10-K risk text.
- `artifacts/`, `reports/` — outputs persisted in run directories (git-kept with `.gitkeep`).

## Data Access & Fallbacks
- **Macro:** Uses `fredapi` when `FRED_API_KEY` is in `.env`; otherwise reads `data/macro/sample_macro.csv` (monthly CPI YoY, unemployment, Fed funds, industrial production).
- **Prices & Fundamentals:** Pulled through `yfinance`; failures trigger deterministic synthetic series so downstream analytics continue.
- **SEC 10-K Risk Text:** Optional; will read `data/financials/sample_10k_risk.txt` if `SEC_API_KEY` is absent.
- **Supply Chain:** Pre-seeded `data/supply_chain/sample_edges.csv` with >20 realistic supplier relationships; external ingestion stub included for future ImportYeti/Panjiva/EDGAR feeds.

All modules emit Rich console warnings when falling back to cached data.

## macOS Setup Notes
1. Install the Xcode Command Line Tools `xcode-select --install` if you have not already.
2. Ensure Python 3.12+ is available (`python3 --version`); use Homebrew (`brew install python@3.12`) if needed.
3. Clone or copy `strategic_alpha` into your workspace, then follow the runbook below to create an isolated virtualenv.

## Environment Variables
Copy `.env.example` to `.env` and populate as available:
- `FRED_API_KEY` — optional; enables live macro pulls.
- `SEC_API_KEY` — optional; enables 10-K risk factors via sec-api.com.
- `SHOCK_PCT` — override default -10% Taiwan fab stress.
- `RISK_PEER_TICKERS`, `SUPPLY_SHOCK_TICKERS` — comma-delimited overrides for peer baskets and stress targets.

## CLI Usage
The CLI is installed as `sal` (`python -m src.analyze_company` also works). Examples assume you created the venv in the project root.

```bash
./venv/bin/python -m src.analyze_company macro --ticker NVDA
./venv/bin/python -m src.analyze_company supply --ticker NVDA
./venv/bin/python -m src.analyze_company valuation --ticker NVDA --start 2021-01-01 --end 2023-12-31
./venv/bin/python -m src.analyze_company risk --ticker NVDA --shock-pct -0.12
./venv/bin/python -m src.analyze_company full --ticker NVDA
```

Running the `full` pipeline produces:
- Macro z-score chart (`artifacts/macro.png`)
- Supply graph (`artifacts/supply_graph.png`) and metrics CSV
- DCF sensitivity grid (`artifacts/dcf_sensitivity.csv`)
- Comps table (`artifacts/comps_table.csv`)
- VaR and stress JSON outputs
- Markdown memo (`reports/NVDA_memo.md`) referencing generated files

## Development Commands
- `make venv` — create the local virtualenv and install requirements.
- `make data` — confirm bundled sample data is ready.
- `make run TICKER=NVDA` — execute the full pipeline with defaults.
- `make test` — run `pytest` (tests monkeypatch yfinance to avoid live calls).
- `make lint` / `make fmt` — run Ruff linting and Black formatting via the venv.

## Testing Philosophy
Unit tests execute against sample data and deterministic synthetic series, ensuring offline reproducibility. They validate artifact creation, DCF math, and VaR calculations. Extend tests by stubbing additional data sources as integrations grow.

## Runbook
1. `python -m venv venv`
2. `./venv/bin/pip install --upgrade pip`
3. `./venv/bin/pip install -r requirements.txt`
4. `cp .env.example .env   # add keys if you have them`
5. `make run TICKER=NVDA`
6. `open reports/NVDA_memo.md`
