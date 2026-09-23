from django.urls import path
from django.views.generic import TemplateView
from . import views
from . import ajax_datatable_views

app_name = 'frontend'


urlpatterns = [
    path('', views.tracks_list_view, name="index"),

    path('ajax_datatable/tracks/', ajax_datatable_views.TrackAjaxDatatableView.as_view(), name="ajax_datatable_track"),
    path('ajax_datatable/album/', ajax_datatable_views.AlbumAjaxDatatableView.as_view(), name="ajax_datatable_album"),
    path('ajax_datatable/artist/',
         ajax_datatable_views.ArtistAjaxDatatableView.as_view(), name="ajax_datatable_artist"),

    path('ajax_datatable/permissions/', ajax_datatable_views.PermissionAjaxDatatableView.as_view(),
         name="ajax_datatable_permissions"),
    path('minimal/', TemplateView.as_view(template_name='frontend/minimal.html'), name="minimal"),

    path('custompks/', TemplateView.as_view(template_name='frontend/custompk/list.html'), name="custompks-list"),
    path('ajax_datatable/custompks/',
         ajax_datatable_views.CustomPkAjaxDatatableView.as_view(), name="ajax_datatable_custompk"),

    path('side_filters/', TemplateView.as_view(template_name='frontend/side_filters.html'), name="side_filters"),
]
