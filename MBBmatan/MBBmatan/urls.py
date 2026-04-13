from django.contrib import admin
from django.urls import path, include
from app.views import custom_error_view

handler404 = lambda request, exception: custom_error_view(request, 404, exception)
handler500 = lambda request: custom_error_view(request, 500)
handler403 = lambda request, exception: custom_error_view(request, 403, exception)
handler400 = lambda request, exception: custom_error_view(request, 400, exception)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
]