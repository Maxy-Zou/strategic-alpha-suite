.PHONY: venv cli dashboard

venv:
	python3 -m venv .venv && ./.venv/bin/python -m ensurepip --upgrade

cli:
	./scripts/sal run --ticker NVDA

dashboard:
	cd sal_dashboard && PYTHONPATH=../strategic_alpha/src streamlit run app/streamlit_app.py
