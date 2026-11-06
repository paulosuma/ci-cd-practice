.PHONY: install lint test run docker check
install:
	uv venv .venv && uv pip install -p .venv -r requirements-dev.txt
lint:
	.venv/bin/ruff check . && .venv/bin/ruff format --check .
test:
	.venv/bin/pytest
check: lint test   ## run exactly what CI runs
run:
	.venv/bin/python -m app.main
docker:
	docker build -t cicd-practice . 
