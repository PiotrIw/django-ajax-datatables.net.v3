Demo
====

A small Django project demonstrating ``django-ajax-datatables-net-v3`` against a
handful of related models (``Track`` / ``Album`` / ``Artist``, plus a custom-PK
model and Django's own ``Permission`` model). No jQuery, no Bootstrap, no npm/Node
build step - the frontend is plain JS plus datatables.net v3, loaded from its CDN.

Pages:

* ``/`` - three related tables (Track / Album / Artist), row-details expand,
  per-column filters, autofilter choices on foreign/M2M fields.
* ``/minimal/`` - the smallest possible setup, against ``django.contrib.auth``'s
  ``Permission`` model.
* ``/custompks/`` - a model whose primary key is not called ``id``.
* ``/side_filters/`` - a sidebar of plain HTML inputs driving the queryset via
  ``extra_data`` callables, plus the default date-range toolbar widget.

Run with Docker
----------------

From the **repository root** (the build needs both ``ajax_datatable/`` and
``demo/`` in its context)::

    docker build -f demo/Dockerfile -t ajax-datatable-demo .
    docker run --rm -p 8000:8000 ajax-datatable-demo

Then open http://localhost:8000/

The container runs migrations and loads the bundled fixture (``backend/fixtures/tracks.json.gz``,
~4700 rows across Tag/Artist/Album/Track/CustomPk) on every start; SQLite lives
inside the container, so data resets when the container is removed. That's
intentional - this is a demo, not a persistent deployment.

Run without Docker
-------------------

::

    pip install -e ..
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py loaddata backend/fixtures/tracks.json.gz
    python manage.py runserver

Optional: create a superuser (``python manage.py createsuperuser``) to browse
``/admin/``.
