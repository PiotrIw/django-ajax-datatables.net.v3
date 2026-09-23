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

Layout
------

::

    demo/
    ├── manage.py
    ├── requirements.txt
    ├── Dockerfile
    ├── entrypoint.sh              # migrate + loaddata + runserver, used by the Docker image
    ├── demo_project/              # Django project settings
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── backend/                   # models: Tag, Tag2, Artist, Album, Track, CustomPk
    │   ├── models.py
    │   ├── admin.py
    │   ├── migrations/
    │   └── fixtures/tracks.json.gz    # seed data (~4700 rows)
    └── frontend/                  # views + templates that exercise the library
        ├── ajax_datatable_views.py    # AjaxDatatableView subclasses (one per page/table)
        ├── views.py
        ├── urls.py
        ├── query_debugger.py
        ├── static/frontend/css/frontend.css
        └── templates/
            ├── base.html           # loads DataTables v3 from its CDN, ajax_datatable's JS/CSS
            ├── navbar.html
            └── frontend/
                ├── track/list.html     # "/" - Track/Album/Artist tables
                ├── minimal.html        # "/minimal/" - Permission model
                ├── custompk/list.html  # "/custompks/" - non-"id" primary key
                └── side_filters.html   # "/side_filters/" - extra_data + date-range widget

Run with Docker
----------------

From the **repository root** (the build needs both ``ajax_datatable/`` and
``demo/`` in its context)::

    docker build -f demo/Dockerfile -t ajax-datatable-demo .
    docker run --rm --name ajax-datatable-demo -p 8000:8000 ajax-datatable-demo

Or, from inside ``demo/``: ``make demo`` (runs both steps above; ``make stop`` to stop it).

Then open http://localhost:8000/

The container runs migrations and loads the bundled fixture (``backend/fixtures/tracks.json.gz``,
~4700 rows across Tag/Artist/Album/Track/CustomPk) on every start; SQLite lives
inside the container, so data resets when the container is removed. That's
intentional - this is a demo, not a persistent deployment.

Optional: create a superuser to browse ``/admin/``, via the running container::

    docker exec -it ajax-datatable-demo python manage.py createsuperuser
