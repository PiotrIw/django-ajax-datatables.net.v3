.. :changelog:

History
=======

v1.1.0
------
* Added an opt-in `a11y_mode` flag to `AjaxDatatableViewUtils.initialize_table()`'s
  `extra_options` (consumed by the library, never forwarded to DataTables.net's own
  options) that remediates three accessibility issues in DataTables.net's own rendered
  markup: an undersized column-sort-control hit area (WCAG 2.5.8), invalid ARIA roles
  on the `scrollX: true` horizontal-scroll wrapper (WCAG 1.3.1/4.1.1 - axe-core's
  `aria-allowed-attr`/`aria-required-children`), and a search input left without a
  real accessible name (WCAG 3.3.2/4.1.2). With the flag false or omitted (the
  default), output is unchanged. See README.rst's "Accessibility (a11y_mode)" section

v1.0.0
------
* Forked from `PiotrIw/django-ajax-datatable <https://github.com/PiotrIw/django-ajax-datatable>`_
  @ v4.6.1 (upstream: `morlandi/django-ajax-datatable <https://github.com/morlandi/django-ajax-datatable>`_)
  and rewritten to target **datatables.net v3**, which dropped its jQuery dependency
* jQuery and Bootstrap dropped entirely, both from the library's own JS
  (`ajax_datatable/static/ajax_datatable/js/utils.js`) and from the demo app
* The server-side protocol (`AjaxDatatableView`, `column_defs`, app settings) is
  unchanged - it was already stable across DataTables 1.x/2.x/3.x. Breaking changes
  are confined to the client JS: `initialize_table()` now takes a CSS selector string
  or DOM node instead of a jQuery object, and table events (`rowCallback`, etc.) are
  now native `CustomEvent`\ s carrying their payload in `event.detail` instead of
  jQuery `.trigger()`/`.on()` extra arguments
* Fixed two DataTables-v3-specific incompatibilities surfaced by the migration:
  `searchCols` entries with a `null` search value (the server's existing wire format)
  now throw in DataTables v3's own handling unless coerced to `''` client-side; and
  DataTables v3's default (non-jQuery) styling wraps the table in `.dt-container`
  rather than the `.dataTables_wrapper` used by 1.x/2.x
  (`ajax_datatable/static/ajax_datatable/css/style.css` updated to match)
* Packaging modernized to `pyproject.toml`; Python floor raised to 3.10, Django floor
  to 5.2; distribution renamed to `django-ajax-datatables-net-v3` (the importable
  Python package stays `ajax_datatable`, unchanged)
* The two example apps (`example/`, `example_minimal/`) were merged into one
  dockerized `demo/` app (no Bootstrap, no jQuery, no npm/Node build step)
* See `MIGRATE_FROM_V4_TO_V1_CHECKLIST.rst <MIGRATE_FROM_V4_TO_V1_CHECKLIST.rst>`_ for
  the full migration guide
