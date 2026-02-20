.PHONY: venv install install-dev install-api test scan serve

venv:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -U pip

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install-api:
	pip install -e ".[api]"

test:
	pytest -q

scan:
	masat scan $(TARGET) --smart --verbose

serve:
	masat serve --reload
