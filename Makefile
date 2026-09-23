.PHONY: install test lint build demo stop clean

install:
	pip install -e .
	pip install -r tests/requirements.txt

# Runs against a Postgres service via docker compose, same as CI (see
# .github/workflows/main.yml and docker-compose.yml).
test:
	docker compose run --rm tests
	docker compose down

lint:
	flake8

build:
	python -m build

# Build and run the dockerized demo app; see demo/README.rst.
demo:
	$(MAKE) -C demo demo

stop:
	$(MAKE) -C demo stop

clean:
	rm -rf build dist *.egg-info
	find . -name '__pycache__' -not -path './node_modules/*' -exec rm -rf {} +
