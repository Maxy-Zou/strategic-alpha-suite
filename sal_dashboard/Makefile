APP=app/streamlit_app.py

.PHONY: venv run fmt lint

venv:
	python -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

run:
	./venv/bin/python -m streamlit run $(APP)

fmt:
	./venv/bin/python -m black app src

lint:
	./venv/bin/python -m ruff check app src
