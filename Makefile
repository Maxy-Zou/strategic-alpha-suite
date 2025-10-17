.PHONY: venv cli dashboard

venv:
	python3 -m venv .venv && ./.venv/bin/python -m ensurepip --upgrade

cli:
	./scripts/sal run --ticker NVDA

dashboard:
	PYTHONPATH=strategic_alpha/src streamlit run sal_dashboard/app/streamlit_app.py
