.PHONY: install test lint build demo stop clean

# Requires a Postgres reachable at POSTGRES_HOST:POSTGRES_PORT (default localhost:5432,
# user/password "postgres"); see tests/test_settings.py.
install:
	pip install -e .
	pip install -r tests/requirements.txt

test:
	cd tests && python manage.py makemigrations && python manage.py migrate && python manage.py test ajax_datatable

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
