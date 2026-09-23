Howto migrate your Django project from django-ajax-datatable (v4.6.1) to django-ajax-datatables-net-v3 (v1.0.0)
-----------------------------------------------------------------------------------------------------------------

This covers moving from `github.com/PiotrIw/django-ajax-datatable.git@v4.6.1
<https://github.com/PiotrIw/django-ajax-datatable/tree/v4.6.1>`_ (or the equivalent
upstream `morlandi/django-ajax-datatable <https://github.com/morlandi/django-ajax-datatable>`_
release) to this package.

**Not changed** - no action needed for these:

- The Python import path: it's still ``ajax_datatable`` (``from ajax_datatable.views
  import AjaxDatatableView``, ``from ajax_datatable import Column, ...``). Only the
  install source changes.
- ``INSTALLED_APPS`` entry: still ``'ajax_datatable'``.
- All ``AJAX_DATATABLE_*`` settings.
- ``AjaxDatatableView`` itself: ``column_defs``, ``get_initial_queryset()``,
  ``customize_row()``, ``render_row_details()``, filtering, queryset optimization,
  everything Python-side. The server-side protocol was already stable across
  DataTables 1.x/2.x/3.x, so none of this needed to change.
- ``extra_data`` callables (e.g. ``from_year: function() { return ...; }``) - still
  auto-invoked on every draw, same as before; the new JS replicates this explicitly.

**Required changes:**

1. Update your install source/requirement:

   .. code:: bash

       pip install git+https://github.com/PiotrIw/django-ajax-datatables-net-v3.git

2. Raise your Python/Django versions if needed: this package requires **Python >= 3.10**
   and **Django >= 5.2**.

3. Swap your jQuery + Bootstrap + DataTables 1.x/2.x script/link tags for DataTables v3's
   (no jQuery required). See the "Pre-requisites" section in `README.rst <README.rst>`_
   for a full example. If you
   were using a Bootstrap-styled build (``datatables.net-bs4``, etc.), pick the matching
   Bootstrap 5 build from DataTables' own `download builder
   <https://datatables.net/download/>`_ instead - ``ajax_datatable``'s CSS/JS have no
   opinion on styling framework.

4. Update every ``AjaxDatatableViewUtils.initialize_table()`` call site: the ``element``
   argument now takes a **CSS selector string or a raw DOM node**, not a jQuery object.

   .. code:: diff

       - AjaxDatatableViewUtils.initialize_table($('#datatable'), url, ...);
       + AjaxDatatableViewUtils.initialize_table('#datatable', url, ...);

5. Update ``$(document).ready(...)`` wrappers to ``document.addEventListener('DOMContentLoaded', ...)``.

6. If you subscribe to table events (``initComplete``, ``drawCallback``, ``rowCallback``,
   ``footerCallback``), switch from jQuery's ``.on()``/extra-argument style to native
   ``addEventListener`` + ``event.detail``:

   .. code:: diff

       - $('#datatable').on('rowCallback', function(event, table, row, data) { ... });
       + document.querySelector('#datatable').addEventListener('rowCallback', function(event) {
       +     var table = event.detail.table, row = event.detail.row, data = event.detail.data;
       +     ...
       + });

   Note that ``table`` is now the DataTables **API instance** directly (what
   ``new DataTable(...)`` returns), not a jQuery-wrapped element.

7. If you provide a custom ``fn_daterange_widget_initialize`` override, its signature
   changed from ``(table, data)`` to ``(tableEl, data, api, extraFilterState)``. Replace
   any ``table.data('date_from', ...)`` calls with ``extraFilterState.date_from = ...``,
   and ``table.api().draw()`` with ``api.draw()``. See the "Filter by global date range"
   section in `README.rst <README.rst>`_ for a full example.

8. If your CSS targets DataTables' generated wrapper markup, update selectors: DataTables
   v3's default (non-jQuery) styling wraps the table in ``.dt-container``, not the
   ``.dataTables_wrapper`` used by 1.x/2.x. (Classes this library sets itself, like
   ``.dataTables_row-tools`` or ``.datatable-column-filter-row``, are unaffected.)

9. If you use ``detail_callback`` or a custom ``redraw_table(element)`` call, note that
   ``element`` may now be a CSS selector string as well as a DOM node, and any code
   receiving the row/table objects gets raw DOM nodes / the DataTables API instance,
   not jQuery-wrapped objects.

**Dropped, not carried forward:**

- The row-details expand animation (previously ``.show('slow')``) is now instant -
  jQuery's animated slide isn't available without jQuery. Minor UX change, not a bug.
- The demo app's CSV/PDF export buttons showcase (Buttons/JSZip/pdfmake) was dropped -
  it was decoration on the old ``example/`` app, not a feature of the library itself,
  and has no confirmed DataTables-v3-native, jQuery-free equivalent yet.
- The demo app's login/auth page was dropped - it wasn't wired to any actual
  permission-gated behaviour in the templates.

If you hit something not covered here, please open an issue.
