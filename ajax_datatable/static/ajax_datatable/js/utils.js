'use strict';

window.AjaxDatatableViewUtils = (function() {

    var _options = {};

    function init(options) {
        /*
            Example:

            AjaxDatatableViewUtils.init({
                search_icon_html: '<i class="fa fa-search"></i>',
                language: {
                },
                fn_daterange_widget_initialize: function(tableEl, data, api, extraFilterState) {
                    var wrapper = tableEl.closest('.dt-container');
                    var toolbar = wrapper.querySelector('.toolbar');
                    toolbar.innerHTML =
                        '<div class="daterange" style="float: left; margin-right: 6px;">' +
                        'From: <input type="date" class="date_from">' +
                        '&nbsp;&nbsp;' +
                        'To: <input type="date" class="date_to">' +
                        '</div>';
                    toolbar.querySelectorAll('.date_from, .date_to').forEach(function(el) {
                        el.addEventListener('change', function(event) {
                            // Annotate table with values retrieved from date widgets
                            extraFilterState.date_from = toolbar.querySelector('.date_from').value;
                            extraFilterState.date_to = toolbar.querySelector('.date_to').value;
                            // Redraw table
                            api.draw();
                        });
                    });
                }
            });


            then:

                <div class="table-responsive">
                    <table id="datatable" width="100%" class="table table-striped table-bordered dataTables-log">
                    </table>
                </div>

                <script language="javascript">
                    document.addEventListener('DOMContentLoaded', function() {

                        // Subscribe "rowCallback" event
                        document.querySelector('#datatable').addEventListener('rowCallback', function(event) {
                            var table = event.detail.table, row = event.detail.row, data = event.detail.data;
                            console.log('rowCallback(): table=%o', table);
                            console.log('rowCallback(): row=%o', row);
                            console.log('rowCallback(): data=%o', data);
                        });

                        // Initialize table
                        AjaxDatatableViewUtils.initialize_table(
                            '#datatable',
                            "{% url 'frontend:object-datatable' model|app_label model|model_name %}"
                        );
                    });
                </script>

        */
        _options = options || {};

        if (!('language' in _options)) {
            _options.language = {};
        }
    }


    function escapeHtml(value) {
        // DataTables' own choice/select markup used to be built via jQuery's .text()/.attr(),
        // which HTML-escape implicitly. Building HTML via string concatenation loses that,
        // so choice values/labels (which may come straight from DB data) must be escaped here.
        if (value === null || value === undefined) {
            return '';
        }
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }


    function resolveExtraData(data) {
        // jQuery's $.param() (used internally by $.ajax) auto-invokes any function-valued
        // property when serializing a data object - this is how "extra_data" callables (see
        // the Side Filters example) get re-evaluated fresh on every draw, with nothing visibly
        // "calling" them. fetch()/URLSearchParams have no such behavior, so it must be done
        // explicitly here, applied at every place extra_data is merged into a request.
        var resolved = {};
        if (data) {
            Object.keys(data).forEach(function(key) {
                var value = data[key];
                resolved[key] = (typeof value === 'function') ? value() : value;
            });
        }
        return resolved;
    }


    function serializeParams(data) {
        // Replicates jQuery's default (non-"traditional") $.param() serialization: nested
        // objects/arrays become bracket-notation keys (columns[0][data], order[0][dir], ...).
        // This is required because DataTables hands the ajax callback a *nested* JS object,
        // and the server's read_parameters() expects exactly this bracket-notation wire format.
        var params = new URLSearchParams();

        function addParam(key, value) {
            if (value === null || value === undefined) {
                params.append(key, '');
            }
            else if (Array.isArray(value)) {
                value.forEach(function(item, index) {
                    addParam(key + '[' + index + ']', item);
                });
            }
            else if (typeof value === 'object') {
                Object.keys(value).forEach(function(subKey) {
                    addParam(key + '[' + subKey + ']', value[subKey]);
                });
            }
            else {
                params.append(key, value);
            }
        }

        Object.keys(data).forEach(function(key) {
            addParam(key, data[key]);
        });

        return params;
    }


    function normalizeSearchCols(searchCols) {
        // The server sends {search: null} for columns with no initial search value (this is
        // the wire format views.py has always produced). DataTables 3's searchCols handling
        // calls .toString() on the search value internally and throws on null (DT 1.x/2.x
        // tolerated it), so it must be coerced to an empty string here.
        if (!searchCols) {
            return searchCols;
        }
        return searchCols.map(function(col) {
            if (col && col.search === null) {
                return Object.assign({}, col, {search: ''});
            }
            return col;
        });
    }


    function fetchJSON(url, options) {
        return fetch(url, options).then(function(response) {
            if (!response.ok) {
                throw new Error('HTTP ' + response.status + ' ' + response.statusText);
            }
            return response.json();
        });
    }


    function _handle_column_filter(api, target) {
        var index = parseInt(target.dataset.index, 10);
        var value = target.value;

        var column = api.column(index);
        var old_value = column.search();
        console.log('Request to search value %o in column %o (current value: %o)', value, index, old_value);
        if (value != old_value) {
            console.log('searching ...');
            column.search(value).draw();
        }
        else {
            console.log('skipped');
        }
    }


    function getCookie(name) {
        var cookieValue = null;
        var value = '; ' + document.cookie,
            parts = value.split('; ' + name + '=');
        if (parts.length == 2) cookieValue = parts.pop().split(';').shift();
        return cookieValue;
    }

    function getCSRFToken() {
        var csrftoken = getCookie('csrftoken');
        if (csrftoken == null) {
            var input = document.querySelector('input[name=csrfmiddlewaretoken]');
            csrftoken = input ? input.value : null;
        }
        return csrftoken;
    }

    function _setup_column_filters(tableEl, api, data) {

        if (data.show_column_filters) {

            var filter_row = '<tr class="datatable-column-filter-row">';
            data.columns.forEach(function(item, index) {
                if (item.visible) {
                    if (item.searchable) {
                        var html = '';
                        if ('choices' in item && item.choices) {

                            // See: https://www.datatables.net/examples/api/multi_filter_select.html
                            var options_html = '<option value=""></option>';
                            item.choices.forEach(function(choice) {
                                var selected = (choice[0] === item.initialSearchValue) ? ' selected="selected"' : '';
                                options_html += '<option value="' + escapeHtml(choice[0]) + '"' + selected + '>' +
                                    escapeHtml(choice[1]) + '</option>';
                            });
                            html = '<select data-index="' + index.toString() + '">' + options_html + '</select>';
                        }
                        else {
                            html = '<input type="text" data-index="' + index + '" placeholder="..." value="' +
                                escapeHtml(item.initialSearchValue ? item.initialSearchValue : '') + '">';
                        }
                        if (item.className) {
                            filter_row += '<th class="' + item.className + '">' + html + '</th>';
                        }
                        else {
                            filter_row += '<th>' + html + '</th>';
                        }
                    }
                    else {
                        if (index == 0) {
                            var search_icon_html = _options.search_icon_html === undefined ? '' : _options.search_icon_html;
                            filter_row += '<th>' + search_icon_html + '</th>';
                        }
                        else {
                            filter_row += '<th></i>&nbsp;</th>';
                        }
                    }
                }
            });
            filter_row += '</tr>';

            // DataTables 3's default (non-jQuery) styling wraps the table in .dt-container,
            // not the .dataTables_wrapper used by 1.x/2.x's jQuery-based styling.
            var wrapper = tableEl.closest('.dt-container');
            wrapper.querySelector('thead').insertAdjacentHTML('beforeend', filter_row);

            var column_filter_row = wrapper.querySelector('.datatable-column-filter-row');
            column_filter_row.querySelectorAll('input,select').forEach(function(el) {
                ['keyup', 'change'].forEach(function(evt) {
                    el.addEventListener(evt, function(event) {
                        _handle_column_filter(api, event.target);
                    });
                });
            });

            /*
            // Here, we could explicitly invoke the handler for each column filter,
            // to make sure that the initial table contents respect any (possible)
            // default value assigned to column filters.
            // This works, but causes multiple POST requests during the first table rendering.
            //
            // So we now prefer to supply the initial search value in the column initialization:
            // see "searchCols" table attribute, as documented here:
            // https://datatables.net/reference/option/searchCols
            */
        }
    }


    function _bind_row_tools(tableEl, api, url, options, extra_data) {

        if (options.full_row_select) {

            // Full row select: when user clicks anywhere in the row,
            // expand it to show further details
            api.table().node().addEventListener('click', function(event) {
                var td = event.target.closest('td');
                if (!td) return;
                var tr = td.closest('tr');
                if (!tr) return;

                // Dont' close child when clicking inside child itself,
                // unless clicking on a button with class "btn-close"
                if (tr.classList.contains('details') && !event.target.classList.contains('btn-close')) {
                    return;
                }

                var row = api.row(tr);
                if (row.child.isShown()) {
                    row.child.hide();
                    tr.classList.remove('shown');
                }
                else {
                    tableEl.querySelectorAll('tr').forEach(function(el) { el.classList.remove('shown'); });
                    api.rows().every(function(rowIdx, tableLoop, rowLoop) {
                        this.child.hide();
                    });
                    if (!tr.classList.contains('details')) {
                        row.child(_load_row_details(row.data(), url, extra_data), 'details').show();
                        tr.classList.add('shown');
                    }
                }
            });

        } else {

            // Use "plus" and "minus" links to toggle row details
            api.table().node().addEventListener('click', function(event) {
                var target = event.target.closest('td.dataTables_row-tools .plus, td.dataTables_row-tools .minus');
                if (!target) return;
                event.preventDefault();
                var tr = target.closest('tr');
                var row = api.row(tr);
                if (row.child.isShown()) {
                    row.child.hide();
                    tr.classList.remove('shown');
                }
                else {
                    var data = _load_row_details(row.data(), url, extra_data);
                    if (options.detail_callback) {
                        options.detail_callback(data, tr);
                    }
                    else {
                        row.child(data, 'details').show();
                    }
                    tr.classList.add('shown');
                }
            });
        }
    }

    function _load_row_details(rowData, url, extra_data) {

        var div = document.createElement('div');
        div.className = 'row-details-wrapper loading';
        div.textContent = 'Loading...';

        if (rowData !== undefined) {

            var data = {
                action: 'details',
                pk: rowData['pk']
            };
            if (extra_data) {
                Object.assign(data, resolveExtraData(extra_data));
            }

            fetchJSON(url + '?' + serializeParams(data).toString(), {
                headers: {'Accept': 'application/json'}
            }).then(function(json) {
                var parent_row_id = json['parent-row-id'];
                if (parent_row_id !== undefined) {
                    div.dataset.parentRowId = parent_row_id;
                }
                div.innerHTML = json.html;
                div.classList.remove('loading');
            }).catch(function(error) {
                console.log('ERROR: ' + error);
            });
        }

        return div;
    }


    function adjust_table_columns() {
        // Adjust the column widths of all visible tables
        // https://datatables.net/reference/api/%24.fn.dataTable.tables()
        DataTable.tables({
            visible: true,
            api: true
        }).columns.adjust();
    }


    function _daterange_widget_initialize(tableEl, api, data, extraFilterState) {
        if (data.show_date_filters) {
            if (_options.fn_daterange_widget_initialize) {
                _options.fn_daterange_widget_initialize(tableEl, data, api, extraFilterState);
            }
            else {
                var wrapper = tableEl.closest('.dt-container');
                var toolbar = wrapper.querySelector('.toolbar');
                toolbar.innerHTML =
                    '<div class="daterange" style="float: left; margin-right: 6px;">' +
                    '<span class="from"><label>From</label>: <input type="date" class="date_from"></span>' +
                    '<span class="to"><label>To</label>: <input type="date" class="date_to"></span>' +
                    '</div>';
                toolbar.querySelectorAll('.date_from, .date_to').forEach(function(el) {
                    el.addEventListener('change', function(event) {
                        // Annotate table with values retrieved from date widgets
                        extraFilterState.date_from = wrapper.querySelector('.date_from').value;
                        extraFilterState.date_to = wrapper.querySelector('.date_to').value;
                        // Redraw table
                        api.draw();
                    });
                });
            }
        }
    }


    function after_table_initialization(tableEl, api, data, url, options, extra_data) {
        //console.log('*** after_table_initialization()');
        _bind_row_tools(tableEl, api, url, options, extra_data);
        _setup_column_filters(tableEl, api, data);
    }


    function _write_footer(tableEl, html) {
        var wrapper = tableEl.closest('.dt-container');
        var footer = wrapper.querySelector('.dataTables_extraFooter');
        if (!footer) {
            wrapper.insertAdjacentHTML('beforeend', '<div class="dataTables_extraFooter"></div>');
            footer = wrapper.querySelector('.dataTables_extraFooter');
        }
        footer.innerHTML = html;
    }

    function _write_toolbar_message(tableEl, html) {
        var wrapper = tableEl.closest('.dt-container');
        var toolbar = wrapper.querySelector('.toolbar');
        var toolbar_message = toolbar.querySelector('.dataTables_extraToolbar');
        if (!toolbar_message) {
            toolbar.insertAdjacentHTML('beforeend', '<div class="dataTables_extraToolbar"></div>');
            toolbar_message = toolbar.querySelector('.dataTables_extraToolbar');
        }
        toolbar_message.innerHTML = html;
    }

    function initialize_table(element, url, extra_options, extra_data) {
        extra_options = extra_options || {};
        extra_data = extra_data || {};

        var tableEl = (typeof element === 'string') ? document.querySelector(element) : element;

        var initData = {action: 'initialize'};
        Object.assign(initData, resolveExtraData(extra_data));

        fetchJSON(url, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: serializeParams(initData)
        }).then(function(data) {

            // https://datatables.net/manual/api
            // DataTables' non-jQuery constructor (new DataTable(selector, options)) returns
            // the API instance directly - there is no separate jQuery-object/.api() step.

            // Per-table state that used to live in jQuery's .data() cache on the table element.
            var extraFilterState = {date_from: '', date_to: ''};

            var options = {
                processing: true,
                serverSide: true,
                scrollX: true,
                autoWidth: true,
                dom: '<"toolbar">lrftip',
                language: _options.language,
                full_row_select: false,
                // language: {
                //     "decimal":        "",
                //     "emptyTable":     "Nessun dato disponibile per la tabella",
                //     "info":           "Visualizzate da _START_ a _END_ di _TOTAL_ entries",
                //     "infoEmpty":      "Visualizzate da 0 a 0 di 0 entries",
                //     "infoFiltered":   "(filtered from _MAX_ total entries)",
                //     "infoPostFix":    "",
                //     "thousands":      ",",
                //     "lengthMenu":     "Visualizza _MENU_ righe per pagina",
                //     "loadingRecords": "Caricamento in corso ...",
                //     "processing":     "Elaborazione in corso ...",
                //     "search":         "Cerca:",
                //     "zeroRecords":    "Nessun record trovato",
                //     "paginate": {
                //         "first":      "Prima",
                //         "last":       "Ultima",
                //         "next":       "Prossima",
                //         "previous":   "Precedente"
                //     },
                //     "aria": {
                //         "sortAscending":  ": activate to sort column ascending",
                //         "sortDescending": ": activate to sort column descending"
                //     }
                // },
                ajax: function(requestData, callback, settings) {
                    requestData.date_from = extraFilterState.date_from;
                    requestData.date_to = extraFilterState.date_to;
                    Object.assign(requestData, resolveExtraData(extra_data));
                    console.log('data tx: %o', requestData);

                    fetchJSON(url, {
                        method: 'POST',
                        headers: {
                            'Accept': 'application/json',
                            'X-CSRFToken': getCSRFToken()
                        },
                        body: serializeParams(requestData)
                    }).then(function(responseData) {
                        console.log('data rx: %o', responseData);
                        callback(responseData);

                        var footer_message = responseData.footer_message;
                        if (footer_message !== null && footer_message !== undefined) {
                            _write_footer(tableEl, footer_message);
                        }
                        var toolbar_message = responseData.toolbar_message;
                        if (toolbar_message !== null && toolbar_message !== undefined) {
                            _write_toolbar_message(tableEl, toolbar_message);
                        }
                    }).catch(function(error) {
                        console.log('ERROR: ' + error);
                    });
                },
                columns: data.columns,
                searchCols: normalizeSearchCols(data.searchCols),
                lengthMenu: data.length_menu,
                order: data.order,
                initComplete: function() {
                    // HACK: wait 200 ms then adjust the column widths
                    // of all visible tables
                    setTimeout(function() {
                        AjaxDatatableViewUtils.adjust_table_columns();
                    }, 200);

                    // Notify subscribers
                    //console.log('Broadcast initComplete()');
                    tableEl.dispatchEvent(new CustomEvent('initComplete', {
                        detail: {table: api}
                    }));
                },
                drawCallback: function(settings) {
                    // Notify subscribers
                    //console.log('Broadcast drawCallback()');
                    tableEl.dispatchEvent(new CustomEvent('drawCallback', {
                        detail: {table: api, settings: settings}
                    }));
                },
                rowCallback: function(row, data) {
                    // Notify subscribers
                    //console.log('Broadcast rowCallback()');
                    tableEl.dispatchEvent(new CustomEvent('rowCallback', {
                        detail: {table: api, row: row, data: data}
                    }));
                },
                footerCallback: function(row, data, start, end, display) {
                    // Notify subscribers
                    //console.log('Broadcast footerCallback()');
                    tableEl.dispatchEvent(new CustomEvent('footerCallback', {
                        detail: {table: api, row: row, data: data, start: start, end: end, display: display}
                    }));
                }
            };

            if (extra_options) {
                Object.assign(options, extra_options);
            }

            var api = new DataTable(tableEl, options);

            _daterange_widget_initialize(tableEl, api, data, extraFilterState);
            after_table_initialization(tableEl, api, data, url, options, extra_data);
        }).catch(function(error) {
            console.log('ERROR: ' + error);
        });
    }


    function redraw_all_tables() {
        DataTable.tables({
            api: true
        }).draw();
    }


    // Redraw table holding the current paging position
    function redraw_table(element) {
        var el = (typeof element === 'string') ? document.querySelector(element) : element;
        var tableEl = el.closest('table.dataTable');
        new DataTable(tableEl).ajax.reload(null, false);
    }


    return {
        init: init,
        initialize_table: initialize_table,
        adjust_table_columns: adjust_table_columns,
        redraw_all_tables: redraw_all_tables,
        redraw_table: redraw_table
    };

})();
