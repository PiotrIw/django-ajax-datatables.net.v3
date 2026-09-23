from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils.translation import gettext_lazy as _
from ajax_datatable.views import AjaxDatatableView

from backend.models import Track, Album, Artist, CustomPk
from frontend.query_debugger import query_debugger

User = get_user_model()


class PermissionAjaxDatatableView(AjaxDatatableView):

    model = Permission
    title = 'Permissions'
    initial_order = [["app_label", "asc"], ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, 'all']]
    search_values_separator = '+'

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {'name': 'id', 'visible': False, },
        {'name': 'codename', 'visible': True, },
        {'name': 'name', 'visible': True, },
        {'name': 'app_label', 'foreign_field': 'content_type__app_label', 'visible': True, },
        {'name': 'model', 'foreign_field': 'content_type__model', 'visible': True, },
    ]


class TrackAjaxDatatableView(AjaxDatatableView):

    model = Track
    title = _('Tracks')
    initial_order = [["name", "asc"], ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, 'all']]
    search_values_separator = '+'
    show_date_filters = False

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {'name': 'pk', 'visible': False, },
        {'name': 'name', 'visible': True, },
        {'name': 'album', 'foreign_field': 'album__name', 'visible': True, 'lookup_field': '__istartswith', },
        {'name': 'artist', 'title': 'Artist', 'foreign_field': 'album__artist__name',
            'visible': True, 'choices': True, 'autofilter': True, },
        {'name': 'tags', 'm2m_foreign_field': 'tags__name', 'searchable': True, 'choices': True, 'autofilter': True, },
        {'name': 'tags2', 'm2m_foreign_field': 'tags2__name', 'searchable': True, 'choices': True,
            'autofilter': False, },
    ]

    @query_debugger
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class AlbumAjaxDatatableView(AjaxDatatableView):

    model = Album
    title = _('Album')
    initial_order = [["name", "asc"], ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, 'all']]
    search_values_separator = '+'

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {'name': 'pk', 'visible': False, },
        {'name': 'name', 'visible': True, },
        {'name': 'release_date', 'visible': True, },
        {'name': 'year', 'visible': True, },
        {'name': 'artist', 'title': 'Artist', 'foreign_field': 'artist__name',
            'visible': True, 'choices': True, 'autofilter': True, },
    ]

    def get_initial_queryset(self, request=None):

        def get_numeric_param(key):
            try:
                value = int(request.POST.get(key))
            except (ValueError, AttributeError, TypeError):
                value = None
            return value

        queryset = super().get_initial_queryset(request=request)

        check_year_null = get_numeric_param('check_year_null')
        if check_year_null is not None:
            if check_year_null == 0:
                queryset = queryset.filter(year=None)
            elif check_year_null == 1:
                queryset = queryset.exclude(year=None)

        from_year = get_numeric_param('from_year')
        if from_year is not None:
            queryset = queryset.filter(year__gte=from_year)

        to_year = get_numeric_param('to_year')
        if to_year is not None:
            queryset = queryset.filter(year__lte=to_year)

        return queryset


class ArtistAjaxDatatableView(AjaxDatatableView):

    model = Artist
    title = _('Artist')
    initial_order = [["name", "asc"], ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, 'all']]
    search_values_separator = '+'
    show_date_filters = False

    column_defs = [
        AjaxDatatableView.render_row_tools_column_def(),
        {'name': 'pk', 'visible': False, },
        {'name': 'name', 'visible': True, },
        {'name': 'edit', 'title': 'Edit', 'searchable': False, 'orderable': False, },
    ]

    def customize_row(self, row, obj):
        row['edit'] = """
            <a href="#" class="btn-edit"
               onclick="var id=this.closest('tr').id.substr(4); alert('Editing Artist: ' + id); return false;">
               Edit
            </a>
        """


class CustomPkAjaxDatatableView(AjaxDatatableView):

    model = CustomPk
    initial_order = [["name", "asc"], ]
    length_menu = [[10, 20, 50, 100, -1], [10, 20, 50, 100, 'all']]

    column_defs = [
        {'name': 'pk', 'visible': True, },
        {'name': 'name', 'visible': True, },
    ]
