#!/bin/sh
set -e

python manage.py migrate --noinput

# Seed demo data on first run; harmless no-op (aside from a logged warning) on later runs
# against an already-seeded database.
python manage.py loaddata backend/fixtures/tracks.json.gz || true

exec python manage.py runserver 0.0.0.0:8000
