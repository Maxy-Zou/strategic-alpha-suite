# Strategic Alpha Suite

This repository bundles two complementary projects for semiconductor-focused investment research:

1. **`strategic_alpha/`** – a Python 3.12 analytics backend that produces macro, supply-chain, valuation, and risk outputs (plots, CSV/JSON metrics, Markdown memo). It includes a Typer CLI (`sal`) and pytest coverage.
2. **`sal_dashboard/`** – a Streamlit front end that imports the backend modules to deliver an interactive analyst dashboard with tabs for Overview, Macro Context, Supply Map, Valuation, Risk, and Report export.

Both subprojects ship with Makefiles, requirements, sample datasets, and deterministic fallbacks so the tooling works even without API keys.

## Quick Start

```bash
git clone https://github.com/Maxy-Zou/strategic-alpha-suite.git
cd strategic-alpha-suite

# Backend pipeline
cd strategic_alpha
python -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m src.analyze_company full --ticker NVDA
```

```bash
# Streamlit dashboard
cd ../sal_dashboard
python -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m streamlit run app/streamlit_app.py
```

## Repo Hygiene

- `.env` files stay local; copy `.env.example` and set keys as needed.
- Generated outputs in `artifacts/` and `reports/` are ignored except for `.gitkeep`.
- Local virtualenvs (`venv/`) are excluded; recreate them per project when needed.

## Contributing

1. Create a branch: `git checkout -b feature/my-improvement`
2. Apply changes in the relevant subproject.
3. Run the provided `make fmt`, `make lint`, and `make test` targets where available.
4. Commit and open a pull request.

Ideas for extensions—alternate data sources, backtests, hosted deployments—are welcome!

## Quickstart

```bash
git clone https://github.com/Maxy-Zou/strategic-alpha-suite.git
cd strategic-alpha-suite

# Run CLI from source (no install required)
./scripts/sal run --ticker NVDA

# Launch dashboard (Streamlit must already be installed)
PYTHONPATH=strategic_alpha/src streamlit run sal_dashboard/app/streamlit_app.py
```

