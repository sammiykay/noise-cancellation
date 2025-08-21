.PHONY: setup install dev test clean run download-models

VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

setup: $(VENV)/bin/activate

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -r requirements.txt
	$(PIP) install -e .[dev]

install: setup
	@echo "Installation complete. Run 'make download-models' to get RNNoise models."

dev: setup
	$(PIP) install -e .[dev]

test:
	$(PYTHON) -m pytest tests/ -v

clean:
	rm -rf $(VENV)
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run: setup
	$(PYTHON) app.py

download-models:
	@echo "Downloading RNNoise models..."
	mkdir -p models
	curl -o models/bd.rnnn "https://github.com/xiph/rnnoise-models/raw/master/bd.rnnn"
	curl -o models/cb.rnnn "https://github.com/xiph/rnnoise-models/raw/master/cb.rnnn"
	curl -o models/mp.rnnn "https://github.com/xiph/rnnoise-models/raw/master/mp.rnnn"
	curl -o models/sh.rnnn "https://github.com/xiph/rnnoise-models/raw/master/sh.rnnn"
	@echo "RNNoise models downloaded successfully!"

lint:
	$(PYTHON) -m black .
	$(PYTHON) -m flake8 .

type-check:
	$(PYTHON) -m mypy .