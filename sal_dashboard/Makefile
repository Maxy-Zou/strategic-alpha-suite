APP=app/streamlit_app.py

# Check for venv in current directory, otherwise use parent directory venv
VENV_PYTHON=$(shell if [ -f ./venv/bin/python ]; then echo ./venv/bin/python; elif [ -f ../venv/bin/python ]; then echo ../venv/bin/python; else echo python; fi)

.PHONY: venv run fmt lint

venv:
	python -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

run:
	$(VENV_PYTHON) -m streamlit run $(APP)

fmt:
	$(VENV_PYTHON) -m black app src

lint:
	$(VENV_PYTHON) -m ruff check app src
