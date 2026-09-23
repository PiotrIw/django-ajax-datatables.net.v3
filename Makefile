.PHONY: test lint build demo stop clean

# Runs against a Postgres service via docker compose, same as CI (see
# .github/workflows/main.yml and docker-compose.yml).
test:
	docker compose run --rm tests
	docker compose down

lint:
	docker compose run --rm lint

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
