TICKER ?= NVDA
START ?= 2021-01-01
END ?= $(shell date +%Y-%m-%d)

.PHONY: venv data run test fmt lint clean

venv:
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt

data:
	@echo "Sample datasets are pre-populated under data/. Nothing to download."

run:
	./venv/bin/python -m src.analyze_company full --ticker $(TICKER) --start $(START) --end $(END)

test:
	./venv/bin/pytest

fmt:
	./venv/bin/black src tests

lint:
	./venv/bin/ruff check src tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -f artifacts/*.png artifacts/*.csv artifacts/*.json
