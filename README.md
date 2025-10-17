# Strategic Alpha Suite

This repository bundles two complementary projects for semiconductor-focused investment research:

1. **`strategic_alpha/`** – a Python 3.12 analytics backend that produces macro, supply-chain, valuation, and risk outputs (plots, CSV/JSON metrics, Markdown memo). It includes deterministic fallbacks so the toolkit works without live APIs.
2. **`sal_dashboard/`** – a Streamlit front end that consumes those analytics for interactive exploration across Overview, Macro, Supply Map, Valuation, Risk, and Report tabs.

![Overview](docs/overview.png)

## Quickstart (offline-friendly)

```bash
git clone https://github.com/Maxy-Zou/strategic-alpha-suite.git
cd strategic-alpha-suite

# Run CLI demo (no install required)
./scripts/sal run --ticker NVDA

# Launch Streamlit dashboard (requires streamlit in your env)
PYTHONPATH=strategic_alpha/src streamlit run sal_dashboard/app/streamlit_app.py
```

_The CLI currently prints a demo line; wire it into the macro/supply/valuation/risk modules next. The dashboard command should be executed from an environment where `streamlit` is installed._
