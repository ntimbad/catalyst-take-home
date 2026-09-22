.PHONY: help venv install run dev clean reset lint

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
STREAMLIT := $(VENV)/bin/streamlit

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

venv:  ## Create virtual environment
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV); \
		echo "Virtual environment created at $(VENV)"; \
	else \
		echo "Virtual environment already exists"; \
	fi

install: venv  ## Install dependencies
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Dependencies installed successfully"

run: install  ## Run the Streamlit app
	@echo "Starting Catalyst..."
	$(STREAMLIT) run app.py --server.headless true

dev: install  ## Run in development mode with auto-reload
	@echo "Starting Catalyst in development mode..."
	$(STREAMLIT) run app.py --server.headless true --server.runOnSave true

setup: install  ## Setup project (install deps + copy env file)
	@if [ ! -f ".env" ]; then \
		echo "Creating .env file from .env.example..."; \
		cp .env.example .env; \
		echo "Please edit .env with your API keys"; \
	else \
		echo ".env file already exists"; \
	fi

clean:  ## Remove cache files
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cache cleaned"

reset: clean  ## Remove virtual environment and cache
	@echo "Removing virtual environment..."
	rm -rf $(VENV)
	@echo "Reset complete. Run 'make install' to reinstall."

lint: install  ## Run linting (if ruff is installed)
	@if $(PIP) show ruff > /dev/null 2>&1; then \
		$(VENV)/bin/ruff check .; \
	else \
		echo "Installing ruff..."; \
		$(PIP) install ruff; \
		$(VENV)/bin/ruff check .; \
	fi

test: install  ## Run tests (if pytest is installed)
	@if $(PIP) show pytest > /dev/null 2>&1; then \
		$(VENV)/bin/pytest; \
	else \
		echo "Installing pytest..."; \
		$(PIP) install pytest; \
		$(VENV)/bin/pytest; \
	fi

# Default target
.DEFAULT_GOAL := help
