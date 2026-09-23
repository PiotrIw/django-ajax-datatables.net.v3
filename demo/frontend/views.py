from django.shortcuts import render

from frontend.query_debugger import query_debugger


@query_debugger
def tracks_list_view(request):
    """
    Render the page which contains the table.
    That will in turn invoke (via fetch) the AjaxDatatableView to fill the table content.
    """
    return render(request, "frontend/track/list.html", {})
