from django.urls import path
from .views import RegisterView, CustomLoginView, ProfileView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('signup/', RegisterView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('', ProfileView.as_view(), name='profile'),
]