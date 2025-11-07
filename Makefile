# Makefile for Strategic Alpha Suite
# Manages both backend (strategic_alpha) and dashboard (sal_dashboard)

.PHONY: help venv cli dashboard setup test test-backend test-dashboard fmt lint clean install-hooks run-hooks

# Default target
help:
	@echo "Strategic Alpha Suite - Development Commands"
	@echo ""
	@echo "Quick Start:"
	@echo "  make venv            - Create root virtual environment"
	@echo "  make cli             - Run CLI analysis for NVDA"
	@echo "  make dashboard       - Start Streamlit dashboard"
	@echo ""
	@echo "Setup:"
	@echo "  make setup           - Set up virtual environments for both projects"
	@echo "  make install-hooks   - Install pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run all tests with coverage"
	@echo "  make test-backend    - Run backend tests only"
	@echo "  make test-dashboard  - Run dashboard tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  make fmt             - Format code with black"
	@echo "  make lint            - Lint code with ruff"
	@echo "  make run-hooks       - Run pre-commit hooks on all files"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean           - Remove cache files and artifacts"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build    - Build Docker image"
	@echo "  make docker-run      - Run dashboard in Docker"

# Original quick start commands
venv:
	python3 -m venv .venv && ./.venv/bin/python -m ensurepip --upgrade

cli:
	./scripts/sal run --ticker NVDA

dashboard:
	cd sal_dashboard && PYTHONPATH=../strategic_alpha/src streamlit run app/streamlit_app.py

# Setup virtual environment and dependencies
setup:
	@echo "Setting up Strategic Alpha backend..."
	cd strategic_alpha && python3 -m venv venv && \
		./venv/bin/pip install --upgrade pip && \
		./venv/bin/pip install -r requirements.txt && \
		./venv/bin/pip install pytest pytest-cov pytest-mock && \
		./venv/bin/pip install -e .
	@echo "Setting up Dashboard..."
	cd sal_dashboard && python3 -m venv venv && \
		./venv/bin/pip install --upgrade pip && \
		./venv/bin/pip install -r requirements.txt && \
		./venv/bin/pip install pytest pytest-cov pytest-mock
	@echo "✓ Setup complete! Run 'make install-hooks' next."

# Install pre-commit hooks
install-hooks:
	@echo "Installing pre-commit hooks..."
	@command -v pre-commit >/dev/null 2>&1 || { \
		echo "Installing pre-commit..."; \
		pip3 install --user pre-commit || pip install pre-commit; \
	}
	pre-commit install
	@echo "✓ Pre-commit hooks installed!"
	@echo "Hooks will run automatically on 'git commit'"
	@echo "Run 'make run-hooks' to test them now"

# Run pre-commit hooks on all files
run-hooks:
	@echo "Running pre-commit hooks on all files..."
	pre-commit run --all-files

# Run all tests
test:
	@echo "Running backend tests..."
	@cd strategic_alpha && \
		(./venv/bin/pytest tests/ -v --cov=src --cov-report=term-missing 2>/dev/null || \
		 python3 -m pytest tests/ -v --cov=src --cov-report=term-missing)
	@echo ""
	@echo "Running dashboard tests..."
	@cd sal_dashboard && \
		(./venv/bin/pytest tests/ -v --cov=src --cov=app --cov-report=term-missing 2>/dev/null || \
		 python3 -m pytest tests/ -v --cov=src --cov=app --cov-report=term-missing)
	@echo ""
	@echo "✓ All tests complete!"

# Run backend tests only
test-backend:
	@echo "Running backend tests..."
	@cd strategic_alpha && \
		(./venv/bin/pytest tests/ -v --cov=src --cov-report=html 2>/dev/null || \
		 python3 -m pytest tests/ -v --cov=src --cov-report=html)
	@echo "Coverage report: strategic_alpha/htmlcov/index.html"

# Run dashboard tests only
test-dashboard:
	@echo "Running dashboard tests..."
	@cd sal_dashboard && \
		(./venv/bin/pytest tests/ -v --cov=src --cov=app --cov-report=html 2>/dev/null || \
		 python3 -m pytest tests/ -v --cov=src --cov=app --cov-report=html)
	@echo "Coverage report: sal_dashboard/htmlcov/index.html"

# Format code
fmt:
	@echo "Formatting backend..."
	@cd strategic_alpha && \
		(./venv/bin/black src tests 2>/dev/null || python3 -m black src tests)
	@echo "Formatting dashboard..."
	@cd sal_dashboard && \
		(./venv/bin/black src app tests 2>/dev/null || python3 -m black src app tests)
	@echo "✓ Code formatted!"

# Lint code
lint:
	@echo "Linting backend..."
	@cd strategic_alpha && \
		(./venv/bin/ruff check src tests 2>/dev/null || python3 -m ruff check src tests)
	@echo "Linting dashboard..."
	@cd sal_dashboard && \
		(./venv/bin/ruff check src app tests 2>/dev/null || python3 -m ruff check src app tests)
	@echo "✓ Linting complete!"

# Clean cache and artifacts
clean:
	@echo "Cleaning cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf strategic_alpha/artifacts/*.png strategic_alpha/artifacts/*.csv strategic_alpha/artifacts/*.json 2>/dev/null || true
	@rm -rf sal_dashboard/artifacts/*.png sal_dashboard/artifacts/*.csv sal_dashboard/artifacts/*.json 2>/dev/null || true
	@echo "✓ Cleaned!"

# Docker commands
docker-build:
	@echo "Building Docker image..."
	cd sal_dashboard && docker build -t strategic-alpha-dashboard .
	@echo "✓ Docker image built!"

docker-run:
	@echo "Starting dashboard in Docker..."
	cd sal_dashboard && docker-compose up
	@echo "Dashboard available at http://localhost:8501"

# Quick backend analysis
run-nvda:
	@echo "Running full analysis for NVDA..."
	cd strategic_alpha && \
		(./venv/bin/python -m src.analyze_company full --ticker NVDA 2>/dev/null || \
		 python3 -m src.analyze_company full --ticker NVDA)
