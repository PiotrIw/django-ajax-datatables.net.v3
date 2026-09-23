# Build context is the repository root, e.g.:
#   docker build -f demo/Dockerfile -t ajax-datatable-demo .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install the library itself (editable, so it's easy to hack on) from the repo root.
COPY pyproject.toml README.rst CHANGELOG.rst LICENSE /app/
COPY ajax_datatable /app/ajax_datatable
RUN pip install --no-cache-dir -e /app

# Install the demo's own (minimal) requirements.
COPY demo/requirements.txt /app/demo/requirements.txt
RUN pip install --no-cache-dir -r /app/demo/requirements.txt

COPY demo /app/demo
WORKDIR /app/demo

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
