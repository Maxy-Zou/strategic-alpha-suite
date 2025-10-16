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

eof
