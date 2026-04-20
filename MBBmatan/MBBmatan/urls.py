from django.contrib import admin
from django.urls import path, include, re_path
from app.views import custom_error_view

handler404 = lambda request, exception: custom_error_view(request, 404, exception)
handler500 = lambda request: custom_error_view(request, 500)
handler403 = lambda request, exception: custom_error_view(request, 403, exception)
handler400 = lambda request, exception: custom_error_view(request, 400, exception)


def _catch_all(request, *args, **kwargs):
    return custom_error_view(request, 404)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    re_path(r'^.*$', _catch_all),
]