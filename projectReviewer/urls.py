
from django.contrib import admin
from django.urls import path, include, re_path
from django.shortcuts import render


# Custom 404 View
def custom_404_view(request, exception=None):
    return render(request, 'error_pages/404.html', status=404)

# Set the handler for 404 errors
handler404 = 'projectReviewer.urls.custom_404_view'


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('',include('appReviewer.urls')),
]



# Fallback for DEBUG=True to handle unknown paths
from django.conf import settings as heysettings
if heysettings.DEBUG:
    urlpatterns += [
        re_path(r'^.*$', custom_404_view),
    ]


# note: 404 ovveride is only used for development stage
# change to debug false and static and media server(aws) to serve static files on production stage